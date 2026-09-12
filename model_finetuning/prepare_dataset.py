#!/usr/bin/env python3
"""
LLMStudio - Custom Dataset Preprocessor
Consolidates and validates multi-turn conversation JSON files from dataset/ into custom_dataset.jsonl
"""

import glob
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def consolidate_dataset(dataset_dir: str = "dataset", output_file: str = None):
    if output_file is None:
        output_file = os.path.join(dataset_dir, "custom_dataset.jsonl")

    json_files = sorted(glob.glob(os.path.join(dataset_dir, "*.json")))
    # Filter out output_file if in the same directory
    json_files = [f for f in json_files if not f.endswith("custom_dataset.jsonl")]

    if not json_files:
        print(f"❌ No JSON files found in directory: {dataset_dir}")
        return None

    print(f"🔍 Found {len(json_files)} JSON dataset files in '{dataset_dir}'.")
    
    total_messages = 0
    total_user_turns = 0
    total_assistant_turns = 0
    conversations = []

    for file_path in json_files:
        fname = os.path.basename(file_path)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "messages" not in data or not isinstance(data["messages"], list):
                print(f"⚠️ Warning: Skipping {fname} (missing 'messages' array)")
                continue

            messages = data["messages"]
            user_count = sum(1 for m in messages if m.get("role") == "user")
            asst_count = sum(1 for m in messages if m.get("role") == "assistant")

            total_messages += len(messages)
            total_user_turns += user_count
            total_assistant_turns += asst_count

            conversations.append({"messages": messages, "source_file": fname})
        except Exception as e:
            print(f"❌ Error reading {fname}: {e}")

    # Write out consolidated JSONL
    with open(output_file, "w", encoding="utf-8") as out:
        for item in conversations:
            out.write(json.dumps(item, ensure_ascii=False) + "\n")

    print("\n" + "=" * 50)
    print("📊 Dataset Summary Statistics")
    print("=" * 50)
    print(f"✅ Total Conversations: {len(conversations)}")
    print(f"💬 Total Messages: {total_messages}")
    print(f"👤 User Turns: {total_user_turns}")
    print(f"🤖 Assistant Turns: {total_assistant_turns}")
    print(f"💾 Consolidated file: {output_file}")
    print("=" * 50)
    return output_file

if __name__ == "__main__":
    consolidate_dataset()
