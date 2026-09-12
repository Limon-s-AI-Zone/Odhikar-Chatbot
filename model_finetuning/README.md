# 🦙 LLMStudio: End-to-End LLM Fine-Tuning Pipeline

A modular, production-ready fine-tuning pipeline for modern open-source language models—specifically **Llama 3.2 (1B / 3B)** and **Llama 3.1 (8B)**—powered by **[Unsloth](https://github.com/unslothai/unsloth)** and **Hugging Face TRL (`SFTTrainer`)**.

Designed to run seamlessly on **Google Colab (Free T4 / Pro A100 / L4)**, **Kaggle GPUs**, or local CUDA environments with minimal VRAM requirements.

---

## 🚀 Key Advantages

- **2x–5x Faster Fine-Tuning**: Hardware-accelerated manual backpropagation and optimized Triton kernels via Unsloth.
- **Up to 70% Less Memory**: Fits 4-bit QLoRA training comfortably within 16GB VRAM (Free Colab T4).
- **Zero Loss in Accuracy**: Employs exact mathematically equivalent gradient calculations.
- **Multiple Export Targets**:
  - 📦 **LoRA Adapters** (~50–150 MB) for Hub publishing or dynamic loading.
  - 🔄 **16-bit Merged Weights** for high-throughput serving (vLLM, TGI, Triton).
  - ⚡ **GGUF Quantization** (Q4_K_M, Q8_0, F16) for local inference via **Ollama**, **LM Studio**, and **llama.cpp**.

---

## 📁 Repository Structure

```text
LLMStudio/
├── llms_fine_tuning.ipynb   # Interactive step-by-step fine-tuning notebook
├── fine_tune.py             # Production CLI training script for headless / server runs
└── README.md                # Project documentation and deployment guide
```

---

## 🛠️ Step-by-Step Workflow in the Notebook

The [`llms_fine_tuning.ipynb`](file:///C:/Users/malek.sarker/Desktop/LLMStudio/llms_fine_tuning.ipynb) notebook is organized into 9 structured sections:

1. **Hardware & GPU Environment Check**: Verifies GPU name, VRAM, and bfloat16 capability.
2. **Dependency Installation**: Automated setup of Unsloth, TRL, PEFT, bitsandbytes, and PyTorch.
3. **Base Model Loading (4-bit QLoRA)**: Loads `unsloth/Llama-3.2-1B-Instruct` with 4-bit precision (no gated login required).
4. **LoRA Adapter Setup**: Configures rank (`r=16`), alpha (`16`), and target projections (`q, k, v, o, gate, up, down`).
5. **Dataset Preparation**: Automatically loads the Bengali legal dataset from `dataset/custom_dataset.jsonl` with Llama 3 chat template.
6. **Baseline Inference**: Tests base model response quality before training.
7. **Supervised Fine-Tuning (SFTTrainer)**: Executes training loop with 8-bit AdamW, optional prompt masking, and memory tracking.
8. **Post-Training Inference**: Tests fine-tuned model with fast token generation (`FastLanguageModel.for_inference`).
9. **Saving & Local Model Export**: Multi-target saving locally (LoRA adapters, 16-bit merged weights, and GGUF for Ollama).

---

## 📋 Hardware Recommendations

| Model | Min VRAM (Training) | Recommended Runtime | Quantization |
| :--- | :--- | :--- | :--- |
| **Llama 3.2 1B Instruct** | ~6 GB VRAM | Google Colab Free T4 / GTX 1080+ | 4-bit QLoRA |
| **Llama 3.2 3B Instruct** | ~10 GB VRAM | Google Colab Free T4 / RTX 3060+ | 4-bit QLoRA |
| **Llama 3.1 8B Instruct** | ~14 GB VRAM | Google Colab Free T4 / Pro A100 / RTX 3090+ | 4-bit QLoRA |

---

## 📊 Custom Dataset: Bangladeshi Family Law (Denmohor / দেনমোহর)

The `dataset/` directory contains **17 multi-turn conversation dialogues** in Bengali focusing on Bangladeshi Family Law regarding dower/mahr (দেনমোহর).

- **Format**: Multi-turn chat `messages` (`system`, `user`, `assistant`).
- **Preprocessed file**: [`dataset/custom_dataset.jsonl`](file:///C:/Users/malek.sarker/Desktop/LLMStudio/dataset/custom_dataset.jsonl) (consolidated 97 conversational turns across 17 dialogues).
- **Auto-detection**: Both [`llms_fine_tuning.ipynb`](file:///C:/Users/malek.sarker/Desktop/LLMStudio/llms_fine_tuning.ipynb) and [`fine_tune.py`](file:///C:/Users/malek.sarker/Desktop/LLMStudio/fine_tune.py) automatically detect and load `dataset/custom_dataset.jsonl`.

If you add new `.json` conversation files into `dataset/`, consolidate them at any time:
```bash
python prepare_dataset.py
```

---

## 🖥️ Running via Command Line (`fine_tune.py`)

For non-interactive training on remote servers, GPU clusters, or background tasks:

```bash
# Standard fine-tuning on Llama 3.2 3B
python fine_tune.py \
    --model_name "unsloth/Llama-3.2-3B-Instruct" \
    --max_steps 100 \
    --batch_size 2 \
    --gradient_accumulation_steps 4 \
    --learning_rate 2e-4

# Fine-tuning with custom dataset, response-only loss masking, and GGUF export
python fine_tune.py \
    --custom_dataset_file "my_dataset.jsonl" \
    --mask_prompt \
    --export_gguf "llama_3.2_gguf" \
    --gguf_method "q4_k_m"
```

---

## 🦙 Deploying Exported GGUF Model to Ollama

After exporting your model to GGUF (`q4_k_m`) via Section 10 of the notebook:

1. Create a file named `Modelfile`:
   ```dockerfile
   FROM ./llama_3.2_gguf/unsloth.Q4_K_M.gguf
   PARAMETER temperature 0.7
   PARAMETER top_p 0.9
   TEMPLATE """<|begin_of_text|><|start_header_id|>system<|end_header_id|>
   {{ .System }}<|eot_id|><|start_header_id|>user<|end_header_id|>
   {{ .Prompt }}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
   {{ .Response }}<|eot_id|>"""
   ```

2. Register and start interacting with your model:
   ```bash
   ollama create my-llama-model -f Modelfile
   ollama run my-llama-model
   ```

---

## 📚 References & Resources

- [Unsloth GitHub Repository](https://github.com/unslothai/unsloth)
- [Hugging Face TRL Documentation](https://huggingface.co/docs/trl/index)
- [Meta Llama 3.2 Model Card](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct)
