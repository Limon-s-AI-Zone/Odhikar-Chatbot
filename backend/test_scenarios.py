import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

from agent import ai_pipeline

def test_n1_baseline():
    print("\n" + "="*50)
    print("Testing Scenario N1 — Multi-Turn Intake (Dower & Maintenance)")
    print("="*50)
    narrative = (
        "আমার বিয়ে হয়েছে ছয় বছর হলো। দুই বছর ধরে আমার স্বামী আলাদা থাকে, কোনো খরচ দেয় না। "
        "আমি বাচ্চা নিয়ে বাবার বাড়িতে আছি। কাবিনে লেখা ছিল দুই লাখ টাকা, এক টাকাও পাইনি। "
        "ফোন করলে বলে টাকা নাই। আমি আর কতদিন বাবার ঘাড়ে বসে থাকব?"
    )
    # Turn 1: Initial Narrative
    r1 = ai_pipeline.run_intake(transcript=narrative)
    print(f"Turn 1 Safety Flag: {r1.get('safety_flag')} (MUST BE False)")
    print(f"Turn 1 Category: {r1.get('category')} (Confidence: {r1.get('confidence')}%)")
    print(f"Turn 1 Is Complete: {r1.get('is_complete')}")
    print(f"Turn 1 Follow-up Question: {r1.get('follow_up_question')}")
    print(f"Turn 1 Suggested Replies: {r1.get('suggested_replies')}")
    assert r1.get('safety_flag') is False, "Historical abuse/grievance must not trigger emergency danger flag"
    assert r1.get('is_complete') is False, "Turn 1 must not complete prematurely"
    assert r1.get('follow_up_question') is not None, "Turn 1 must ask follow-up question"

    # Turn 2: Client explains cause ("আমি টাকা চেয়েছিলাম")
    r2 = ai_pipeline.run_intake(transcript="আমি টাকা চেয়েছিলাম", existing_state=r1)
    print(f"\nTurn 2 Is Complete: {r2.get('is_complete')}")
    print(f"Turn 2 Current Stage: {r2.get('current_stage')}")
    print(f"Turn 2 Follow-up Question: {r2.get('follow_up_question')}")
    print(f"Turn 2 Suggested Replies: {r2.get('suggested_replies')}")
    assert r2.get('is_complete') is False, "Turn 2 must ask for marriage documents/Kabinnama, not complete prematurely"
    q2 = (r2.get('follow_up_question') or '').lower()
    assert any(w in q2 for w in ['কাবিন', 'কাগজ', 'বিয়ে', 'নথি']), f"Turn 2 must ask about Kabinnama/marriage documents, got: {q2}"

    # Turn 3: Client confirms Kabinnama possession
    r3 = ai_pipeline.run_intake(transcript="কাবিননামা বাবার বাড়িতে আছে", existing_state=r2)
    print(f"\nTurn 3 Is Complete: {r3.get('is_complete')}")
    print(f"Turn 3 Current Stage: {r3.get('current_stage')}")
    print(f"Turn 3 Follow-up Question: {r3.get('follow_up_question')}")
    print(f"Turn 3 Suggested Replies: {r3.get('suggested_replies')}")
    assert r3.get('is_complete') is False, "Turn 3 must ask about proposed legal remedy/salish before completing"
    q3 = (r3.get('follow_up_question') or '').lower()
    assert any(w in q3 for w in ['সালিশ', 'আদালত', 'মামলা', 'প্রতিকার', 'সমাধান', 'মীমাংসা']), f"Turn 3 must ask about proposed solution, got: {q3}"

    # Turn 4: Client specifies desired solution
    r4 = ai_pipeline.run_intake(transcript="আমি সরাসরি আদালতে মামলা করে দেনমোহর ও ভরণপোষণ আদায় করতে চাই", existing_state=r3)
    print(f"\nTurn 4 Is Complete: {r4.get('is_complete')}")
    print(f"Turn 4 Referral Clinic: {r4.get('referral_clinic')}")
    draft = r4.get('draft_complaint') or ''
    print(f"Turn 4 Draft Complaint Preview:\n{draft[:200]}...")
    assert r4.get('is_complete') is True, "Turn 4 must complete intake"
    assert r4.get('draft_complaint') is not None, "Draft complaint must be generated"
    assert r4.get('rights_explanation') is not None, "Rights explanation must be generated"
    print("✓ Scenario N1 Multi-Turn test PASSED!")

def test_n6_safety_breakout():
    print("\n" + "="*50)
    print("Testing Scenario N6 — Safety Disclosure (Physical Violence with Questionnaire Continuation)")
    print("="*50)
    narrative = (
        "কাবিনের টাকা তো পাইনিই, উল্টো গত সপ্তাহে হাত ভেঙে দিয়েছে। "
        "ডাক্তারের কাছে যেতেও দেয়নি। আজকেও বলছে রাতে দেখে নিবে। আমি খুব ভয় পাচ্ছি।"
    )
    result = ai_pipeline.run_intake(transcript=narrative)
    print(f"Safety Flag: {result.get('safety_flag')} (MUST BE True)")
    print(f"Safety Message:\n{result.get('safety_message')}")
    print(f"Follow-up Question:\n{result.get('follow_up_question')}")
    print(f"Suggested Replies: {result.get('suggested_replies')}")
    assert result.get('safety_flag') is True, "Safety check failed to trigger on physical violence!"
    assert result.get('safety_message') is not None, "Safety message must be populated!"
    assert result.get('follow_up_question') is not None, "Questionnaires must proceed without hard shortcut!"

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

    # 1. Test 401 Unauthorized parsing (Dynamic Provider-Aware)
    import utils
    import httpx
    from langchain_openai.chat_models.base import OpenAIAuthenticationError, OpenAIConnectionError, OpenAIRateLimitError

    req = httpx.Request('POST', 'https://openrouter.ai/api/v1')
    resp_401 = httpx.Response(401, request=req)
    err_401 = OpenAIAuthenticationError("Error code: 401 - Missing or invalid API key", response=resp_401, body=None)
    
    # Generic / detected provider
    parsed_401 = ai_pipeline.parse_llm_error(err_401)
    print(f"[401 Test] Error Type: {parsed_401['error_type']}, Status: {parsed_401['status_code']}")
    assert parsed_401['status_code'] == 401
    assert "401" in parsed_401['title']
    assert "API Key" in parsed_401['message_bn'] or "API কী" in parsed_401['message_bn']
    print("✓ 401 Unauthorized parsed correctly with user-facing Bengali message.")

    # 1b. Test Vertex AI-specific provider parsing
    info_vertex = utils.get_provider_info("vertex")
    parsed_vertex_401 = ai_pipeline.parse_llm_error(err_401, provider_info=info_vertex)
    assert "GOOGLE_API_KEY" in parsed_vertex_401['message_bn'] or "GOOGLE_APPLICATION_CREDENTIALS" in parsed_vertex_401['message_bn']
    print("✓ Vertex AI provider 401 dynamically injected.")

    # 1c. Test Ollama-specific provider connection error
    info_ollama = utils.get_provider_info("ollama")
    err_conn = OpenAIConnectionError(request=req)
    parsed_ollama_conn = ai_pipeline.parse_llm_error(err_conn, provider_info=info_ollama)
    assert "Ollama" in parsed_ollama_conn['title']
    assert "ollama" in parsed_ollama_conn['message_bn'].lower()
    print("✓ Ollama local provider connection failure dynamically injected.")

    # 2. Test Connection Error parsing
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
    assert "কোটা" in parsed_429['title'] or "রেট লিমিট" in parsed_429['title']
    print("✓ 429 Token limit / quota parsed correctly.")

    # 4. Test Missing API Key handling in run_intake
    import utils.model_connection
    orig_key = utils.model_connection.OPENROUTER_API_KEY
    orig_llm_key = utils.model_connection.LLM_API_KEY_RAW
    try:
        utils.model_connection.OPENROUTER_API_KEY = ""
        utils.model_connection.LLM_API_KEY_RAW = ""
        # Force is_model_configured to return False for test
        orig_is_configured = utils.model_connection.is_model_configured
        utils.model_connection.is_model_configured = lambda: False
        ai_pipeline.is_model_configured = lambda: False
        res_no_key = ai_pipeline.run_intake("আমার দেনমোহরের দাবি আছে।")
        assert res_no_key.get("llm_error") is not None
        assert res_no_key.get("llm_error_details")["status_code"] == 401
        print("✓ Missing API key immediately caught and returned with Bengali error message.")
    finally:
        utils.model_connection.OPENROUTER_API_KEY = orig_key
        utils.model_connection.LLM_API_KEY_RAW = orig_llm_key
        utils.model_connection.is_model_configured = orig_is_configured
        ai_pipeline.is_model_configured = orig_is_configured

    # 5. Test check_llm_status
    status = ai_pipeline.check_llm_status()
    print(f"[LLM Status Check] Connected: {status.get('connected')}, Code: {status.get('status_code')}")
    assert "status_code" in status
    print("✓ check_llm_status() returned valid diagnostic payload.")

def test_disambiguation_then_land_dispute():
    print("\n" + "="*60)
    print("Testing Disambiguation -> Land Dispute Flow")
    print("="*60)

    # Turn 1: Vague text
    r1 = ai_pipeline.run_intake(transcript="আমার একটা সমস্যা আছে")
    print(f"Turn 1 Category: {r1.get('category')}")
    print(f"Turn 1 Disambiguation Needed: {r1.get('disambiguation_needed')}")
    assert r1.get('disambiguation_needed') is True

    # Turn 2: User clicks "জমিজমা সংক্রান্ত বিরোধ"
    r2 = ai_pipeline.run_intake(transcript="জমিজমা সংক্রান্ত বিরোধ", existing_state=r1)
    print(f"Turn 2 Category: {r2.get('category')}")
    print(f"Turn 2 Is Complete: {r2.get('is_complete')}")
    print(f"Turn 2 Follow-up Question: {r2.get('follow_up_question')}")
    print(f"Turn 2 Suggested Replies: {r2.get('suggested_replies')}")
    
    assert r2.get('category') == "land_dispute"
    assert r2.get('is_complete') is False, "Must ask follow-up questions instead of finishing immediately after disambiguation!"
    assert r2.get('follow_up_question') is not None
    print("✓ Disambiguation -> Land Dispute flow test PASSED!")

def test_land_dispute_multiturn():
    print("\n" + "="*60)
    print("Testing Land Dispute Multi-Turn Intake Flow")
    print("="*60)

    # Turn 1: User enters "জমিজমা সংক্রান্ত বিরোধে"
    print("\n--- Turn 1: Initial Submission ---")
    t1_text = "জমিজমা সংক্রান্ত বিরোধে"
    r1 = ai_pipeline.run_intake(transcript=t1_text)
    
    print(f"Turn 1 Category: {r1.get('category')} (Confidence: {r1.get('confidence')}%)")
    print(f"Turn 1 Disambiguation Needed: {r1.get('disambiguation_needed')}")
    print(f"Turn 1 Is Complete: {r1.get('is_complete')}")
    print(f"Turn 1 Follow-up Question: {r1.get('follow_up_question')}")
    print(f"Turn 1 Suggested Replies: {r1.get('suggested_replies')}")
    
    assert r1.get('category') == "land_dispute", f"Expected land_dispute, got {r1.get('category')}"
    assert r1.get('disambiguation_needed') is False
    assert r1.get('is_complete') is False, "Should NOT complete immediately after 'জমিজমা সংক্রান্ত বিরোধে'"
    assert r1.get('follow_up_question') is not None, "Must ask a follow-up question"
    assert r1.get('suggested_replies') is not None, "Must provide suggested replies"

    # Turn 2: User answers Question 1 with possession details
    print("\n--- Turn 2: Answering Question 1 (Possession) ---")
    t2_text = "প্রতিপক্ষ জোরপূর্বক জমিটি অবৈধভাবে দখল করে রেখেছে"
    r2 = ai_pipeline.run_intake(transcript=t2_text, existing_state=r1)
    
    print(f"Turn 2 Turn Count: {r2.get('turn_count')}")
    print(f"Turn 2 Is Complete: {r2.get('is_complete')}")
    print(f"Turn 2 Follow-up Question: {r2.get('follow_up_question')}")
    print(f"Turn 2 Suggested Replies: {r2.get('suggested_replies')}")
    
    assert r2.get('is_complete') is False, "Should ask more questions (Turn 2 should not complete yet)"
    assert r2.get('follow_up_question') is not None
    assert r2.get('suggested_replies') is not None

    # Turn 3: User answers Question 2 with deeds / evidence details
    print("\n--- Turn 3: Answering Question 2 (Deeds / Records) ---")
    t3_text = "জমির মূল রেজিস্ট্রি দলিল আমাদের কাছে সংরক্ষিত আছে"
    r3 = ai_pipeline.run_intake(transcript=t3_text, existing_state=r2)
    
    print(f"Turn 3 Turn Count: {r3.get('turn_count')}")
    print(f"Turn 3 Is Complete: {r3.get('is_complete')}")
    print(f"Turn 3 Follow-up Question: {r3.get('follow_up_question')}")
    print(f"Turn 3 Suggested Replies: {r3.get('suggested_replies')}")
    
    assert r3.get('is_complete') is False, "Should ask third question (Opponent/Salish)"
    assert r3.get('follow_up_question') is not None

    # Turn 4: User answers Question 3 with salish / opponent details
    print("\n--- Turn 4: Answering Question 3 (Salish / Opponent) ---")
    t4_text = "ইউনিয়ন পরিষদে মেম্বার বা চেয়ারম্যানের কাছে সালিশ হয়েছিল কিন্তু সমাধান হয়নি"
    r4 = ai_pipeline.run_intake(transcript=t4_text, existing_state=r3)
    
    print(f"Turn 4 Turn Count: {r4.get('turn_count')}")
    print(f"Turn 4 Is Complete: {r4.get('is_complete')}")
    print(f"Turn 4 Referral Clinic: {r4.get('referral_clinic')}")
    print(f"Turn 4 Rights Explanation (first 100 chars): {(r4.get('rights_explanation') or '')[:100]}...")
    print(f"Turn 4 Draft Complaint:\n{r4.get('draft_complaint')}")
    
    assert r4.get('is_complete') is True, "Turn 4 should complete the intake"
    assert r4.get('draft_complaint') is not None
    assert r4.get('rights_explanation') is not None
    assert r4.get('referral_clinic') is not None
    print("\n✓ Multi-turn land dispute intake test PASSED!")

def test_maintenance_cause_flow():
    print("\n" + "="*60)
    print("Testing Maintenance Intake: Problem → Cause → History → Impact Flow")
    print("="*60)

    # Turn 1: User enters maintenance grievance without cause
    print("\n--- Turn 1: Initial Submission (ভরণপোষণ দেয় না) ---")
    t1_text = "আমার স্বামী আমাকে কোনো ভরণপোষণ দেয় না।"
    r1 = ai_pipeline.run_intake(transcript=t1_text)

    print(f"Turn 1 Category: {r1.get('category')} (Confidence: {r1.get('confidence')}%)")
    print(f"Turn 1 Is Complete: {r1.get('is_complete')}")
    print(f"Turn 1 Follow-up Question: {r1.get('follow_up_question')}")
    print(f"Turn 1 Suggested Replies: {r1.get('suggested_replies')}")

    assert r1.get('is_complete') is False, "Should NOT complete when cause/details are missing"
    assert r1.get('follow_up_question') is not None
    # Verify that the LLM asks why the maintenance dispute occurred ("ভরণপোষণ নিয়ে ঝামেলা হয়েছে কেন?")
    q1 = r1.get('follow_up_question', '').lower()
    print(f"Checking if question asks about Cause (ঝামেলা / কারণ / কেন / কী কারণে): {any(w in q1 for w in ['ঝামেলা', 'কারণ', 'কেন', 'কী কারণে', 'সূত্রপাত', 'আলাদা'])}")
    assert any(w in q1 for w in ['ঝামেলা', 'কারণ', 'কেন', 'কী কারণে', 'সূত্রপাত', 'আলাদা']), f"Question must ask about cause of dispute, got: {q1}"

    # Turn 2: User answers Question 1 with cause
    print("\n--- Turn 2: Answering Question 1 (Cause: যৌতুকের দাবিতে বিরোধ) ---")
    t2_text = "যৌতুকের দাবিতে ঝগড়া করে আলাদা হয়ে গেছে এবং খরচ দেওয়া বন্ধ করেছে"
    r2 = ai_pipeline.run_intake(transcript=t2_text, existing_state=r1)

    print(f"Turn 2 Turn Count: {r2.get('turn_count')}")
    print(f"Turn 2 Is Complete: {r2.get('is_complete')}")
    print(f"Turn 2 Follow-up Question: {r2.get('follow_up_question')}")
    print(f"Turn 2 Suggested Replies: {r2.get('suggested_replies')}")

    assert r2.get('is_complete') is False, "Should ask about history/documents/impact before completing"
    assert r2.get('follow_up_question') is not None

    # Turn 3: User answers Question 2 with history / documents / timeline
    print("\n--- Turn 3: Answering Question 2 (History: ৩ বছর বিয়ে, কাবিননামা বাবার বাড়ি) ---")
    t3_text = "৩ বছর আগে বিয়ে হয়েছিল, কাবিননামা বাবার বাড়িতে আছে, মেম্বারের সালিশেও স্বামী আসেনি"
    r3 = ai_pipeline.run_intake(transcript=t3_text, existing_state=r2)

    print(f"Turn 3 Turn Count: {r3.get('turn_count')}")
    print(f"Turn 3 Is Complete: {r3.get('is_complete')}")
    print(f"Turn 3 Follow-up Question: {r3.get('follow_up_question')}")
    print(f"Turn 3 Suggested Replies: {r3.get('suggested_replies')}")

    # Turn 4: User answers Question 3 with impact & desired remedy
    print("\n--- Turn 4: Answering Question 3 (Impact & Solution: বাচ্চা নিয়ে বাবার বাড়ি, খরচ ও দেনমোহর চাই) ---")
    t4_text = "বাচ্চা নিয়ে বাবার বাড়ি আছি, আমি দেনমোহর ও বাচ্চার নিয়মিত খরচ ও ভরণপোষণ চাই"
    r4 = ai_pipeline.run_intake(transcript=t4_text, existing_state=r3)

    print(f"Turn 4 Turn Count: {r4.get('turn_count')}")
    print(f"Turn 4 Is Complete: {r4.get('is_complete')}")
    print(f"Turn 4 Referral Clinic: {r4.get('referral_clinic')}")
    print(f"Turn 4 Rights Explanation (first 100 chars): {(r4.get('rights_explanation') or '')[:100]}...")
    print(f"Turn 4 Draft Complaint:\n{r4.get('draft_complaint')}")

    assert r4.get('is_complete') is True, "Turn 4 should complete after essential facts are answered"
    assert r4.get('draft_complaint') is not None
    assert r4.get('rights_explanation') is not None
    print("\n✓ Maintenance Cause Flow test PASSED!")

def test_llm_summarization():
    print("\n" + "="*60)
    print("Testing LLM Summarization for Token Guardrails")
    print("="*60)
    long_narrative = (
        "চার বছর আগে আমার বিয়ে হয়েছে। বিয়ের পর থেকে ওরা আমার বাবার কাছে বারবার যৌতুকের জন্য টাকা চাইতে থাকে। "
        "বাবা জমি বিক্রি করে কিছু টাকা দিয়েছেন, প্রায় আশি হাজার টাকা। তারপরও ওদের চাওয়া শেষ হয় না। "
        "কাবিনের টাকা আজও এক পয়সাও পাইনি। এখন ওরা আমাকে এবং আমার ছোট মেয়েকে বাড়ি ছেড়ে চলে যেতে বাধ্য করতেছে। "
        "শাশুড়ি ও ভাশুররা হুমকি দিচ্ছে। কাবিননামার কাগজ বাবার কাছে রাখা আছে। আমি এখন কোথায় যাব, কী করব কিছুই বুঝতে পারছি না।"
    )
    summary_result = ai_pipeline.summarize_narrative(long_narrative)
    summarized_text = summary_result.get("summarized_text", "")
    print(f"Original Tokens: {summary_result.get('original_tokens')}")
    print(f"Summarized Tokens: {summary_result.get('summarized_tokens')}")
    print(f"Summarized Text:\n{summarized_text}")

    assert len(summarized_text) > 0, "Summarized text should not be empty"
    assert summary_result.get("summarized_tokens") < summary_result.get("original_tokens"), "Summarized tokens should be fewer"
    
    # Test running intake with is_summarized=True
    intake_res = ai_pipeline.run_intake(transcript=summarized_text, is_summarized=True)
    assert intake_res.get("requires_continuation") is False, "Summarized intake should not be blocked by token budget"
    assert intake_res.get("category") is not None, "Should classify category from summarized text"
    print("✓ LLM Summarization and Summarized Intake Flow test PASSED!")

if __name__ == "__main__":
    test_llm_error_handling()
    test_llm_summarization()
    test_n6_safety_breakout()
    test_n1_baseline()
    test_maintenance_cause_flow()
    test_disambiguation_then_land_dispute()
    test_land_dispute_multiturn()
