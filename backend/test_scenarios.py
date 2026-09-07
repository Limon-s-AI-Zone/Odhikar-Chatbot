import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

import ai_pipeline

def test_n1_baseline():
    print("\n" + "="*50)
    print("Testing Scenario N1 — Baseline (Dower & Maintenance)")
    print("="*50)
    narrative = (
        "আমার বিয়ে হয়েছে ছয় বছর হলো। দুই বছর ধরে আমার স্বামী আলাদা থাকে, কোনো খরচ দেয় না। "
        "আমি বাচ্চা নিয়ে বাবার বাড়িতে আছি। কাবিনে লেখা ছিল দুই লাখ টাকা, এক টাকাও পাইনি। "
        "ফোন করলে বলে টাকা নাই। আমি আর কতদিন বাবার ঘাড়ে বসে থাকব?"
    )
    result = ai_pipeline.run_intake(transcript=narrative)
    print(f"Safety Flag: {result.get('safety_flag')}")
    print(f"Category: {result.get('category')} (Confidence: {result.get('confidence')}%)")
    print(f"Dower Amount: {result.get('dower_amount')}")
    print(f"Marriage Date: {result.get('marriage_date')}")
    print(f"Children: {result.get('children')}")
    print(f"Follow-up Question: {result.get('follow_up_question')}")
    draft = result.get('draft_complaint') or ''
    print(f"Draft Complaint Preview:\n{draft[:200]}...")

def test_n6_safety_breakout():
    print("\n" + "="*50)
    print("Testing Scenario N6 — Safety Disclosure (Physical Violence)")
    print("="*50)
    narrative = (
        "কাবিনের টাকা তো পাইনিই, উল্টো গত সপ্তাহে হাত ভেঙে দিয়েছে। "
        "ডাক্তারের কাছে যেতেও দেয়নি। আজকেও বলছে রাতে দেখে নিবে। আমি খুব ভয় পাচ্ছি।"
    )
    result = ai_pipeline.run_intake(transcript=narrative)
    print(f"Safety Flag: {result.get('safety_flag')} (MUST BE True)")
    print(f"Safety Message:\n{result.get('safety_message')}")
    assert result.get('safety_flag') is True, "Safety check failed to trigger on physical violence!"

def test_n7_out_of_scope():
    print("\n" + "="*50)
    print("Testing Scenario N7 — Out of Supported Categories")
    print("="*50)
    narrative = "পাশের বাড়ির লোক আমার গরুটাকে বিষ খাইয়ে মেরে ফেলেছে বলে আমার সন্দেহ। থানায় গেছিলাম, অভিযোগ নেয়নি। এখন কী করব?"
    result = ai_pipeline.run_intake(transcript=narrative)
    print(f"Category: {result.get('category')} (Confidence: {result.get('confidence')}%)")
    print(f"Explanation:\n{result.get('rights_explanation')}")

if __name__ == "__main__":
    test_n6_safety_breakout()
    test_n1_baseline()
    test_n7_out_of_scope()
