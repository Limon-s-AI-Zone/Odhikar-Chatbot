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

def test_llm_error_handling():
    print("\n" + "="*50)
    print("Testing LLM Error Handling (401, Connection, Token Issues)")
    print("="*50)

    # 1. Test 401 Unauthorized parsing
    import httpx
    from langchain_openai.chat_models.base import OpenAIAuthenticationError, OpenAIConnectionError, OpenAIRateLimitError

    req = httpx.Request('POST', 'https://openrouter.ai/api/v1')
    resp_401 = httpx.Response(401, request=req)
    err_401 = OpenAIAuthenticationError("Error code: 401 - Missing or invalid API key", response=resp_401, body=None)
    parsed_401 = ai_pipeline.parse_llm_error(err_401)
    print(f"[401 Test] Error Type: {parsed_401['error_type']}, Status: {parsed_401['status_code']}")
    assert parsed_401['status_code'] == 401
    assert "401" in parsed_401['title']
    assert "OPENROUTER_API_KEY" in parsed_401['message_bn']
    print("✓ 401 Unauthorized parsed correctly with user-facing Bengali message.")

    # 2. Test Connection Error parsing
    err_conn = OpenAIConnectionError(request=req)
    parsed_conn = ai_pipeline.parse_llm_error(err_conn)
    print(f"[Connection Test] Error Type: {parsed_conn['error_type']}, Status: {parsed_conn['status_code']}")
    assert parsed_conn['error_type'] == 'connection_error'
    assert "সংযোগ বিচ্ছিন্ন" in parsed_conn['title']
    print("✓ Connection failure parsed correctly.")

    # 3. Test Rate Limit / Token Quota parsing (429)
    resp_429 = httpx.Response(429, request=req)
    err_429 = OpenAIRateLimitError("Error code: 429 - Rate limit exceeded or token quota reached", response=resp_429, body=None)
    parsed_429 = ai_pipeline.parse_llm_error(err_429)
    print(f"[Token / 429 Test] Error Type: {parsed_429['error_type']}, Status: {parsed_429['status_code']}")
    assert parsed_429['status_code'] == 429
    assert "টোকেন কোটা" in parsed_429['title']
    print("✓ 429 Token limit / quota parsed correctly.")

    # 4. Test Missing API Key handling in run_intake
    import utils.model_connection
    orig_key = utils.model_connection.OPENROUTER_API_KEY
    try:
        utils.model_connection.OPENROUTER_API_KEY = ""
        res_no_key = ai_pipeline.run_intake("আমার দেনমোহরের দাবি আছে।")
        assert res_no_key.get("llm_error") is not None
        assert res_no_key.get("llm_error_details")["status_code"] == 401
        print("✓ Missing API key immediately caught and returned with Bengali error message.")
    finally:
        utils.model_connection.OPENROUTER_API_KEY = orig_key

    # 5. Test check_llm_status
    status = ai_pipeline.check_llm_status()
    print(f"[LLM Status Check] Connected: {status.get('connected')}, Code: {status.get('status_code')}")
    assert "status_code" in status
    print("✓ check_llm_status() returned valid diagnostic payload.")

if __name__ == "__main__":
    test_llm_error_handling()
    # Scenarios testing
    # test_n6_safety_breakout()
    # test_n1_baseline()
    # test_n7_out_of_scope()
