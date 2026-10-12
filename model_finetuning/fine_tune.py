#!/usr/bin/env python3
"""
LLMStudio - Standalone Fine-Tuning CLI Pipeline
Powered by Unsloth & Hugging Face TRL

Fine-tunes Llama 3.1 / 3.2 models using 4-bit QLoRA and exports to LoRA, Merged 16-bit, or GGUF.
"""

import argparse
import os
import sys
import glob
import torch
from datasets import load_dataset
from transformers import TrainingArguments, TextStreamer
from trl import SFTTrainer

# System prompt template conforming to Meta Llama 3 Instruct specifications
LLAMA_3_PROMPT_TEMPLATE = (
    "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
    "{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n"
    "{instruction}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    "{response}<|eot_id|>"
)


def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune Llama 3.1 / 3.2 with Unsloth & TRL")
    parser.add_argument(
        "--model_name",
        type=str,
        default="unsloth/Llama-3.2-1B-Instruct",
        help="Base model from Hugging Face or Unsloth",
    )
    parser.add_argument(
        "--max_seq_length",
        type=int,
        default=2048,
        help="Maximum token sequence length",
    )
    parser.add_argument(
        "--dataset_name",
        type=str,
        default="yahma/alpaca-cleaned",
        help="Hugging Face dataset identifier",
    )
    parser.add_argument(
        "--custom_dataset_file",
        type=str,
        default=None,
        help="Optional path to local .jsonl or .csv file",
    )
    parser.add_argument(
        "--lora_r",
        type=int,
        default=16,
        help="LoRA rank dimension",
    )
    parser.add_argument(
        "--lora_alpha",
        type=int,
        default=16,
        help="LoRA alpha scaling parameter",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=2,
        help="Per-device training batch size",
    )
    parser.add_argument(
        "--gradient_accumulation_steps",
        type=int,
        default=4,
        help="Gradient accumulation steps",
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        default=2e-4,
        help="Optimizer learning rate",
    )
    parser.add_argument(
        "--max_steps",
        type=int,
        default=60,
        help="Maximum training steps (-1 to train by epochs)",
    )
    parser.add_argument(
        "--num_epochs",
        type=float,
        default=1.0,
        help="Number of epochs if max_steps is -1",
    )
    parser.add_argument(
        "--mask_prompt",
        action="store_true",
        help="Only train on assistant responses, masking user instructions",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="outputs",
        help="Training checkpoint output directory",
    )
    parser.add_argument(
        "--save_lora_dir",
        type=str,
        default="lora_model",
        help="Directory to save final LoRA adapter weights",
    )
    parser.add_argument(
        "--export_merged",
        type=str,
        default=None,
        help="Optional directory to save 16-bit merged full model weights",
    )
    parser.add_argument(
        "--export_gguf",
        type=str,
        default=None,
        help="Optional directory to save GGUF quantized model for Ollama / LM Studio",
    )
    parser.add_argument(
        "--gguf_method",
        type=str,
        default="q4_k_m",
        choices=["q4_k_m", "q8_0", "f16"],
        help="GGUF quantization algorithm",
    )
    return parser.parse_args()


def check_environment():
    print("=" * 60)
    print("🔍 LLMStudio Hardware & Environment Inspection")
    print("=" * 60)
    if not torch.cuda.is_available():
        print("❌ Error: CUDA GPU not detected. Unsloth requires an NVIDIA GPU.")
        sys.exit(1)

    device_name = torch.cuda.get_device_name(0)
    total_mem = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2)
    bf16_ok = torch.cuda.is_bf16_supported()

    print(f"✅ GPU Device: {device_name}")
    print(f"📊 Total VRAM: {total_mem} GB")
    print(f"🚀 Native bfloat16: {'Supported' if bf16_ok else 'Not supported (using float16)'}")
    print("=" * 60)


def load_model_and_tokenizer(model_name: str, max_seq_length: int, lora_r: int, lora_alpha: int):
    from unsloth import FastLanguageModel

    print(f"\n📦 Loading model {model_name} in 4-bit precision...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )

    print(f"🔧 Attaching LoRA adapters (r={lora_r}, alpha={lora_alpha})...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_r,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_alpha=lora_alpha,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    trainable, total = model.get_nb_trainable_parameters()
    print(f"🎯 Trainable parameters: {trainable:,} / {total:,} ({100 * trainable / total:.2f}%)")
    return model, tokenizer


def prepare_dataset(tokenizer, dataset_name: str, custom_file: str = None):
    print(f"\n📚 Preparing dataset...")
    eos_token = tokenizer.eos_token

    # Auto-detect custom dataset if present
    if custom_file is None:
        if os.path.exists("dataset/custom_dataset.jsonl"):
            custom_file = "dataset/custom_dataset.jsonl"
        elif os.path.isdir("dataset") and glob.glob("dataset/*.json"):
            from prepare_dataset import consolidate_dataset
            custom_file = consolidate_dataset("dataset")

    def formatting_prompts(examples):
        # Case 1: Multi-turn conversation format (e.g. Bengali legal / Denmohor dataset)
        if "messages" in examples:
            texts = []
            for msg_list in examples["messages"]:
                formatted_conv = ""
                for idx, m in enumerate(msg_list):
                    role = m.get("role", "")
                    content = m.get("content", "")
                    if idx == 0 and role == "system":
                        formatted_conv += f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{content}<|eot_id|>"
                    elif role == "user":
                        formatted_conv += f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>"
                    elif role == "assistant":
                        formatted_conv += f"<|start_header_id|>assistant<|end_header_id|>\n\n{content}<|eot_id|>"
                texts.append(formatted_conv)
            return {"text": texts}

        # Case 2: Instruction-Input-Output format (e.g. Alpaca)
        instructions = examples.get("instruction", [])
        inputs = examples.get("input", [""] * len(instructions))
        outputs = examples.get("output", [])
        texts = []

        for instruction, input_text, output in zip(instructions, inputs, outputs):
            full_inst = f"{instruction}\nInput: {input_text}" if input_text else instruction
            formatted = LLAMA_3_PROMPT_TEMPLATE.format(
                system_prompt="You are a helpful, respectful, and honest assistant.",
                instruction=full_inst,
                response=output,
            ) + eos_token
            texts.append(formatted)
        return {"text": texts}

    if custom_file and os.path.exists(custom_file):
        print(f"Loading custom dataset from: {custom_file}")
        ext = "csv" if custom_file.endswith(".csv") else "json"
        dataset = load_dataset(ext, data_files=custom_file, split="train")
    else:
        print(f"Loading community dataset: {dataset_name} (subset: 3000 rows)...")
        dataset = load_dataset(dataset_name, split="train[:3000]")

    dataset = dataset.map(formatting_prompts, batched=True)
    print(f"✅ Prepared {len(dataset)} training examples.")
    return dataset


def run_training(model, tokenizer, dataset, args):
    from unsloth import is_bfloat16_supported
    from unsloth.chat_templates import train_on_responses_only

    training_kwargs = {
        "per_device_train_batch_size": args.batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "warmup_steps": 5,
        "learning_rate": args.learning_rate,
        "fp16": not is_bfloat16_supported(),
        "bf16": is_bfloat16_supported(),
        "logging_steps": 10,
        "optim": "adamw_8bit",
        "weight_decay": 0.01,
        "lr_scheduler_type": "linear",
        "seed": 3407,
        "output_dir": args.output_dir,
        "report_to": "none",
    }

    if args.max_steps > 0:
        training_kwargs["max_steps"] = args.max_steps
    else:
        training_kwargs["num_train_epochs"] = args.num_epochs

    print(f"\n⚙️ Initializing SFTTrainer with effective batch size {args.batch_size * args.gradient_accumulation_steps}...")
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(**training_kwargs),
    )

    if args.mask_prompt:
        print("🎭 Enabling train_on_responses_only (masking prompt tokens)...")
        trainer = train_on_responses_only(
            trainer,
            instruction_part="<|start_header_id|>user<|end_header_id|>\n\n",
            response_part="<|start_header_id|>assistant<|end_header_id|>\n\n",
        )

    print("\n🚀 Starting Training Loop...")
    stats = trainer.train()
    print(f"✅ Training completed in {stats.metrics.get('train_runtime', 0):.2f} seconds!")
    return trainer


def export_models(model, tokenizer, args):
    print("\n💾 Exporting Model Artifacts...")

    # 1. Always save LoRA adapters
    os.makedirs(args.save_lora_dir, exist_ok=True)
    model.save_pretrained(args.save_lora_dir)
    tokenizer.save_pretrained(args.save_lora_dir)
    print(f"✅ Saved LoRA adapters to: {args.save_lora_dir}")

    # 2. Merged 16-bit export
    if args.export_merged:
        print(f"🔄 Merging LoRA into 16-bit base model at {args.export_merged}...")
        model.save_pretrained_merged(args.export_merged, tokenizer, save_method="merged_16bit")
        print(f"✅ Merged 16-bit model saved to: {args.export_merged}")

    # 3. GGUF export
    if args.export_gguf:
        print(f"⚡ Exporting to GGUF format ({args.gguf_method}) at {args.export_gguf}...")
        model.save_pretrained_gguf(args.export_gguf, tokenizer, quantization_method=args.gguf_method)
        print(f"✅ GGUF model saved to: {args.export_gguf}")


def main():
    args = parse_args()
    check_environment()
    model, tokenizer = load_model_and_tokenizer(
        model_name=args.model_name,
        max_seq_length=args.max_seq_length,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
    )
    dataset = prepare_dataset(tokenizer, args.dataset_name, args.custom_dataset_file)
    run_training(model, tokenizer, dataset, args)
    export_models(model, tokenizer, args)
    print("\n🎉 All operations completed successfully!")


if __name__ == "__main__":
    main()
