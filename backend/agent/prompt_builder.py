"""
Dynamic, config-driven prompt manager for Odhikar AI Paralegal.
Loads prompts, categories, stages, suggested replies, and fallback questions
from prompt_config.yaml instead of hardcoded Python strings.
"""

import os
import yaml
from typing import Dict, List, Tuple, Optional, Any


class PromptBuilder:
    """Dynamic prompt builder that loads all prompt content from YAML config.
    
    Replaces the static string constants in prompts.py and the hardcoded
    keyword-matching functions in ai_pipeline.py (generate_suggested_replies,
    generate_extra_fallback_question, get_stage_fallback_question).
    """

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "prompt_config.yaml")
        self._config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load()

    def _load(self):
        """Load YAML config file."""
        with open(self._config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    def reload(self):
        """Hot-reload config without restarting the server."""
        self._load()

    # =========================================================================
    # System Prompts
    # =========================================================================
    def get_system_prompt(self, prompt_type: str) -> str:
        """Get a system prompt by type key.
        
        Args:
            prompt_type: One of 'classification', 'safety', 'extraction',
                         'intake_dialogue', 'follow_up', 'dynamic_solution'
        Returns:
            The system prompt string from config, or empty string if not found.
        """
        return self._config.get("system_prompts", {}).get(prompt_type, "")

    # =========================================================================
    # Category Info
    # =========================================================================
    def get_categories(self) -> Dict[str, Any]:
        """Return all category definitions."""
        return self._config.get("categories", {})

    def get_category_label(self, category: str) -> str:
        """Return the Bengali label for a category."""
        return self._config.get("categories", {}).get(category, {}).get("label_bn", category)

    # =========================================================================
    # Stage Info
    # =========================================================================
    def get_intake_stages(self) -> List[Dict[str, str]]:
        """Return the ordered list of intake stage definitions."""
        return self._config.get("intake_stages", [])

    def get_stage_label(self, stage_id: str) -> str:
        """Return the Bengali label for a stage."""
        for s in self.get_intake_stages():
            if s["id"] == stage_id:
                return s.get("label_bn", stage_id)
        return stage_id

    # =========================================================================
    # Stage Fallback Questions
    # Replaces: get_stage_fallback_question() in ai_pipeline.py
    # =========================================================================
    def get_stage_fallback_question(
        self,
        category: Optional[str],
        stage: str,
        missing_item: Optional[str] = None
    ) -> str:
        """Get the fallback follow-up question for a given category and stage.

        If missing_item indicates court documents, tries the _documents_for_court variant first.
        Falls back to default question if stage-specific one is not found.
        """
        cat = category or "general"
        fallbacks = self._config.get("stage_fallback_questions", {})
        cat_fallbacks = fallbacks.get(cat, {})

        # Check for court document variant when stage is 'history'
        if missing_item and stage == "history":
            court_keywords = ["মামলা", "কাগজ", "আদালত", "documents_for_court"]
            if missing_item == "documents_for_court" or any(
                w in (missing_item or "") for w in court_keywords
            ):
                court_q = cat_fallbacks.get("history_documents_for_court") or fallbacks.get("general", {}).get("history_documents_for_court")
                if court_q:
                    return court_q

        # Try exact stage match
        q = cat_fallbacks.get(stage) or fallbacks.get("general", {}).get(stage)
        if q:
            return q

        # Try default for this category
        default_q = cat_fallbacks.get("default") or fallbacks.get("general", {}).get("default")
        if default_q:
            return default_q

        # Ultimate fallback
        return (
            f"আপনার সমস্যাটির সুষ্ঠু সমাধানের জন্য একটি বিষয় জানা প্রয়োজন: "
            f"{missing_item or 'বিরোধের মূল কারণ'} সম্পর্কে কি বিস্তারিত জানাবেন?"
        )

    # =========================================================================
    # Suggested Replies
    # Replaces: generate_suggested_replies() in ai_pipeline.py (~200 lines)
    # =========================================================================
    def get_suggested_replies(
        self,
        question: Optional[str],
        missing_fields: Optional[List[str]] = None,
        category: Optional[str] = None
    ) -> List[str]:
        """Get dynamic quick-reply chips based on the follow-up question context.
        
        Uses config-based keyword matching to find the right reply set.
        This replaces the massive if/elif chain in generate_suggested_replies().
        """
        q = (question or "").strip()
        target = (missing_fields[0] if missing_fields and len(missing_fields) > 0 else "").strip()
        replies_config = self._config.get("suggested_replies", {})

        # -1. Action Selection / Initial Inquiry
        if (
            target == "action_selection"
            or any(w in q for w in ["আইনি পদক্ষেপ বা প্রতিকার যাচাই", "কী ধরনের আইনি পদক্ষেপ", "কী ধরণের আইনি পদক্ষেপ"])
        ):
            return replies_config.get("action_selection", {}).get("default", [
                "দেনমোহর ও ভরণপোষণ আদায়ের পদক্ষেপ",
                "বকেয়া মজুরি ও ক্ষতিপূরণ আদায়ের পদক্ষেপ",
                "জমিজমা দখল উদ্ধার বা স্বত্ব সুরক্ষার পদক্ষেপ",
                "যৌতুক ও পারিবারিক নির্যাতন প্রতিরোধে পদক্ষেপ"
            ])

        # -1a. Required Docs & Proofs Inquiry
        if (
            target == "required_docs_inquiry"
            or any(w in q for w in ["কাগজপত্র ও প্রমাণাদি প্রস্তুত রয়েছে", "কাগজপত্র ও প্রমাণাদি প্রস্তুত আছে", "প্রয়োজনীয় কাগজপত্র ও প্রমাণাদি"])
        ):
            cat_docs_replies = replies_config.get("required_docs_inquiry", {}).get(category)
            if cat_docs_replies:
                return cat_docs_replies
            return replies_config.get("required_docs_inquiry", {}).get("default", [
                "হ্যাঁ, সমস্ত প্রয়োজনীয় কাগজপত্র ও প্রমাণাদি প্রস্তুত আছে",
                "কিছু কাগজপত্র আছে, তবে সব নেই",
                "কোনো লিখিত কাগজপত্র বা প্রমাণ নেই"
            ])

        # -1b. Confirm Process (Do you want to process?)
        if (
            target in ("confirm_process", "process_confirmation")
            or "প্রক্রিয়াটি কি আপনি সম্পন্ন করতে চান" in q
            or "প্রক্রিয়াটি সম্পন্ন করতে চান" in q
            or "প্রক্রিয়াটি সম্পন্ন করতে চান" in q
        ):
            return replies_config.get("confirm_process", {}).get("default", [
                "হ্যাঁ, প্রক্রিয়াটি সম্পন্ন করতে চাই",
                "না, এখন নয় / পরে বিবেচনা করব"
            ])

        # -1c. Partial Docs Action Confirmation
        if (
            target == "partial_docs_action"
            or "বিদ্যমান কাগজপত্রের ভিত্তিতে" in q
            or "বিদ্যমান তথ্যের ভিত্তিতে এই আইনি প্রক্রিয়ায়" in q
        ):
            return replies_config.get("partial_docs_action", {}).get("default", [
                "হ্যাঁ, বিদ্যমান কাগজের ভিত্তিতেই অগ্রসর হতে চাই",
                "বিকল্প কোনো উপায় আছে কি?"
            ])

        # 0. Confirm Solution / Agreement to Proceed
        if (
            target in ("confirm_solution", "solution_confirmation")
            or "সম্মত আছেন" in q
            or "সম্মতি" in q
            or "অগ্রসর হতে চান" in q
            or "অগ্রসর হতে সম্মত" in q
        ):
            return replies_config.get("confirm_solution", {}).get("default", [
                "হ্যাঁ, আমি সম্মত আছি",
                "হ্যাঁ, এভাবেই সমাধান চাই",
                "বিকল্প কোনো উপায় আছে কি?"
            ])

        # 0a. Desired Solution / Legal Remedy
        if (
            target == "desired_solution"
            or any(w in q for w in [
                "সালিশের মাধ্যমে", "আদালতে মামলা", "মামলা করতে চান", "আপস চান",
                "আইনি সমাধান", "আইনি প্রতিকার", "সালিশ চান"
            ])
            or (
                ("সালিশ" in q or "আদালত" in q or "মামলা" in q)
                and ("চান" in q or "প্রতিকার" in q or "সমাধান" in q)
            )
        ):
            cat_replies = replies_config.get("desired_solution", {}).get(category)
            if cat_replies:
                return cat_replies
            return replies_config.get("desired_solution", {}).get("default", [])

        # 0b. Cause of dispute (family / wages / land / dowry)
        is_cause_inquiry = (
            target == "cause"
            or "বিরোধের মূল কারণ" in target
            or "বিরোধের কারণ" in target
            or any(w in q for w in ["কী কারণে", "কি কারণে", "কোনো বিরোধ", "কোন বিরোধ", "বিরোধ হয়েছিল", "বিরোধ হয়েছিল", "ঝামেলা হয়েছে কেন", "ঝামেলা হয়েছিল কেন", "কেন বন্ধ", "বিরোধের কারণ", "সূত্রপাত কীভাবে", "কীভাবে শুরু"])
        )
        if is_cause_inquiry:
            if category == "unpaid_wages" or any(w in q for w in ["মজুরি", "বেতন", "ঠিকাদার", "মালিক"]):
                cat_replies = replies_config.get("cause", {}).get("unpaid_wages")
                if cat_replies:
                    return cat_replies
            elif category == "land_dispute" or any(w in q for w in ["জমি", "দখল"]):
                cat_replies = replies_config.get("cause", {}).get("land_dispute")
                if cat_replies:
                    return cat_replies
            else:
                cat_replies = replies_config.get("cause", {}).get("family_dower_maintenance")
                if cat_replies:
                    return cat_replies

        # 1. Kabinnama / Marriage document evidence
        if (
            ("কাবিন" in q or "কাবিননামা" in q or "কাবিননামা" in target)
            or (("দলিল" in q or "কাগজ" in q) and category in ("family_dower_maintenance", "dowry"))
        ):
            if any(w in q for w in ["মামলা", "প্রস্তুত", "আদালত"]):
                return replies_config.get("kabinnama", {}).get("court_context", [])
            return replies_config.get("kabinnama", {}).get("default", [])

        # 2. Dower / Dowry / Claim amount
        if (
            category in ("family_dower_maintenance", "dowry")
            and ("দেনমোহর" in q or "টাকার পরিমাণ" in target or "টাকা" in q or "দাবি" in q)
        ) or "দেনমোহর" in q:
            return replies_config.get("dower", {}).get("default", [])

        # 3. Marriage Date / Timeline
        if ("বিয়ে" in q) and any(w in q for w in ["সন", "কবে", "সাল", "বছর", "তারিখ"]):
            return replies_config.get("marriage_date", {}).get("default", [])

        # 4. Wages / Unpaid Salary Amount
        if (
            category == "unpaid_wages" and (any(w in q for w in ["টাকা", "কত টাকা", "পরিমাণ", "বকেয়া", "মজুরি", "বেতন", "পাওনা"]))
            or (any(w in q for w in ["মজুরি", "বেতন", "পাওনা"]) and any(w in q for w in ["টাকা", "কত টাকা", "পরিমাণ", "কত মাসের"]))
            or any(w in target for w in ["বকেয়া মজুরির মোট পরিমাণ", "টাকার পরিমাণ", "unpaid_wages_claim"])
        ):
            return replies_config.get("wages", {}).get("default", [])

        # 5. Work Period / Duration
        if "কতদিন" in q or "কাজের সময়" in target or "কোন সময়" in q:
            return replies_config.get("work_period", {}).get("default", [])

        # 6. Work Evidence / Witness / Sardar / Slip
        if any(w in q for w in ["সাক্ষী", "সর্দার", "স্লিপ", "হাজিরা"]) or "সাক্ষী" in target:
            return replies_config.get("evidence", {}).get("default", [])

        # 7a. Land Possession & Nature of Dispute
        if (
            category == "land_dispute"
            and (
                any(w in q for w in ["দখল", "দখলে", "ওয়ারিশ", "সীমানা", "বেদখল"])
                or any(w in target for w in ["দখল", "কারণ"])
                or target == "cause"
            )
        ):
            return replies_config.get("land_possession", {}).get("default", [])

        # 7b. Land Deeds / Records / Evidence
        if (
            (category == "land_dispute" or "জমি" in q)
            and any(w in q for w in ["দলিল", "খতিয়ান", "পর্চা", "কাগজ", "রেজিস্ট্রি"])
        ):
            return replies_config.get("land_deeds", {}).get("default", [])

        # 7c. Land Salish / Opponent
        if (
            (category == "land_dispute" or "জমি" in q)
            and any(w in q for w in ["সালিশ", "চেয়ারম্যান", "মেম্বার", "প্রতিপক্ষ", "শরিক"])
        ):
            return replies_config.get("land_salish", {}).get("default", [])

        # 7d. General Land Dispute fallback
        if category == "land_dispute" or "জমি" in q:
            return replies_config.get("land_general", {}).get("default", [])

        # 8. Children / Maintenance
        if any(w in q for w in ["সন্তান", "বাচ্চা", "ভরণপোষণ"]):
            return replies_config.get("children", {}).get("default", [])

        # 9. Disambiguation
        if category == "unclassifiable" or "পারিবারিক" in q:
            return replies_config.get("disambiguation", {}).get("default", [])

        # 10. Confirmation / Yes-No
        if any(w in q for w in ["কি না", "কিনা", "আছে কি", "হয়েছে কি"]) or q.endswith("?"):
            return replies_config.get("confirmation", {}).get("default", [])

        # 11. General fallback
        return replies_config.get("general_fallback", {}).get("default", [
            "হ্যাঁ, এই বিষয়ে প্রয়োজনীয় সব তথ্য আমার কাছে আছে",
            "কোনো লিখিত প্রমাণ বা কাগজপত্র নেই, সবই মৌখিক",
            "সব আলোচনা ও চুক্তি মৌখিকভাবে হয়েছিল",
            "এই পরিস্থিতিতে কীভাবে অগ্রসর হব সেই আইনি পরামর্শ চাই"
        ])

    # =========================================================================
    # Fallback Questions (document_nei / mone_nei)
    # Replaces: generate_extra_fallback_question() in ai_pipeline.py (~110 lines)
    # =========================================================================
    def get_fallback_question(
        self,
        match_type: str,
        category: Optional[str] = None,
        previous_question: Optional[str] = None
    ) -> Tuple[str, List[str]]:
        """Get empathetic fallback question and chips when client indicates
        lack of documents or inability to remember.
        
        Returns:
            Tuple of (question_text, list_of_reply_chips)
        """
        cat = (category or "").lower()
        prev_q = (previous_question or "").lower()
        fallbacks = self._config.get("fallback_questions", {})

        # Determine if this is a document-context question
        is_doc_context = (
            match_type == "document_nei"
            or any(w in prev_q for w in [
                "কাবিন", "কাবিননামা", "দলিল", "কাগজ", "খতিয়ান",
                "পর্চা", "স্লিপ", "হাজিরা", "রেজিস্ট্রি"
            ])
        )

        if is_doc_context:
            doc_fallbacks = fallbacks.get("document_nei", {})

            # Category-specific document fallback
            if cat in ("family_dower_maintenance", "dowry") or any(
                w in prev_q for w in ["কাবিন", "বিয়ে"]
            ):
                entry = doc_fallbacks.get("family_dower_maintenance", {})
            elif cat == "unpaid_wages" or any(
                w in prev_q for w in ["মজুরি", "বেতন", "কাজ"]
            ):
                entry = doc_fallbacks.get("unpaid_wages", {})
            elif cat == "land_dispute" or any(
                w in prev_q for w in ["জমি", "দলিল"]
            ):
                entry = doc_fallbacks.get("land_dispute", {})
            else:
                entry = doc_fallbacks.get("default", {})

            if entry:
                return entry.get("question", ""), entry.get("chips", [])

        # Memory/timeline fallbacks
        mone_fallbacks = fallbacks.get("mone_nei", {})

        # Date/timeline
        if any(w in prev_q for w in ["কবে", "সন", "সাল", "বছর", "তারিখ", "সময়", "কতদিন"]):
            entry = mone_fallbacks.get("date", {})
            if entry:
                return entry.get("question", ""), entry.get("chips", [])

        # Money amount
        if any(w in prev_q for w in [
            "কত টাকা", "টাকার পরিমাণ", "দেনমোহর কত",
            "বেতন কত", "মজুরি কত", "দাবি কত"
        ]):
            entry = mone_fallbacks.get("money", {})
            if entry:
                return entry.get("question", ""), entry.get("chips", [])

        # General memory fallback
        entry = mone_fallbacks.get("general", {})
        if entry:
            return entry.get("question", ""), entry.get("chips", [])

        # Ultimate hardcoded fallback (should never reach here if config is valid)
        return (
            "এই তথ্যটি নির্দিষ্টভাবে মনে না থাকলেও কোনো সমস্যা নেই। "
            "আপনার পরিবারের কেউ কি এ বিষয়ে সাহায্য করতে পারবেন?",
            [
                "বাবার বাড়ির লোকজন তথ্য দিতে পারবেন",
                "স্থানীয় মেম্বার বিষয়টি জানেন",
                "আত্মীয়রা খোঁজ নিয়ে জানাতে পারবেন",
                "কারও কাছেই তথ্য নেই"
            ]
        )

    # =========================================================================
    # Action Workflow Methods (Check Action -> Required Docs -> Confirm Process / Partial / Continue)
    # =========================================================================
    def get_action_workflow_initial_question(self) -> str:
        """Returns the opening question asking what kind of action the user wants to check."""
        return self._config.get("action_workflow", {}).get(
            "initial_question",
            "আসসালামু আলাইকুম। অধিকার (Odhikar) এআই প্যারালিগ্যাল সেবায় আপনাকে স্বাগতম। আপনি কী ধরনের আইনি পদক্ষেপ বা প্রতিকার যাচাই করতে চান?"
        )

    def get_action_chips(self) -> List[str]:
        """Returns the quick reply chips for available legal action categories."""
        return self._config.get("action_workflow", {}).get(
            "action_chips",
            [
                "দেনমোহর ও ভরণপোষণ আদায়ের পদক্ষেপ",
                "বকেয়া মজুরি ও ক্ষতিপূরণ আদায়ের পদক্ষেপ",
                "জমিজমা দখল উদ্ধার বা স্বত্ব সুরক্ষার পদক্ষেপ",
                "যৌতুক ও পারিবারিক নির্যাতন প্রতিরোধে পদক্ষেপ"
            ]
        )

    def get_required_docs_question(self, category: Optional[str]) -> str:
        """Returns the category-specific question listing required documents & proofs."""
        cat = category or "general"
        cats = self._config.get("action_workflow", {}).get("categories", {})
        cat_data = cats.get(cat) or cats.get("general", {})
        return cat_data.get("docs_question", "এই বিষয়ে আইনি পদক্ষেপ গ্রহণের জন্য প্রয়োজনীয় কাগজপত্র ও প্রমাণাদি প্রস্তুত আছে কি?")

    def get_required_docs_chips(self, category: Optional[str] = None) -> List[str]:
        """Returns the suggested reply chips for the required documents question."""
        replies = self._config.get("suggested_replies", {}).get("required_docs_inquiry", {})
        if category and category in replies:
            return replies[category]
        return replies.get("default", [
            "হ্যাঁ, সমস্ত প্রয়োজনীয় কাগজপত্র ও প্রমাণাদি প্রস্তুত আছে",
            "কিছু কাগজপত্র আছে, তবে সব নেই",
            "কোনো লিখিত কাগজপত্র বা প্রমাণ নেই"
        ])

    def get_confirm_process_question(self, category: Optional[str]) -> str:
        """Returns the question asking if client wants to process when all docs are provided."""
        cat = category or "general"
        cats = self._config.get("action_workflow", {}).get("categories", {})
        cat_data = cats.get(cat) or cats.get("general", {})
        return cat_data.get("all_docs_confirm_question", "আপনার প্রয়োজনীয় সকল কাগজপত্র ও প্রমাণাদি প্রস্তুত রয়েছে। আপনি কি এই আইনি পদক্ষেপের প্রক্রিয়াটি সম্পন্ন করতে চান?")

    def get_confirm_process_chips(self) -> List[str]:
        """Returns Yes/No chips for process confirmation."""
        return self._config.get("suggested_replies", {}).get("confirm_process", {}).get("default", [
            "হ্যাঁ, প্রক্রিয়াটি সম্পন্ন করতে চাই",
            "না, এখন নয় / পরে বিবেচনা করব"
        ])

    def get_partial_docs_action_text(self, category: Optional[str], evidence: str = "") -> str:
        """Returns actionable steps based on partial documents provided so far."""
        cat = category or "general"
        cats = self._config.get("action_workflow", {}).get("categories", {})
        cat_data = cats.get(cat) or cats.get("general", {})
        return cat_data.get("partial_docs_action", "📋 আপনার বিদ্যমান কাগজপত্রের ভিত্তিতে আইনি পদক্ষেপ গ্রহণ করা সম্ভব। আপনি কি এই প্রক্রিয়ায় অগ্রসর হতে সম্মত আছেন?")

    def get_partial_docs_chips(self) -> List[str]:
        """Returns chips for partial docs confirmation."""
        return self._config.get("suggested_replies", {}).get("partial_docs_action", {}).get("default", [
            "হ্যাঁ, বিদ্যমান কাগজের ভিত্তিতেই অগ্রসর হতে চাই",
            "বিকল্প কোনো উপায় আছে কি?"
        ])

    def get_no_docs_continuation_question(self, category: Optional[str]) -> str:
        """Returns reassurance that process continues without docs, plus next question."""
        cat = category or "general"
        cats = self._config.get("action_workflow", {}).get("categories", {})
        cat_data = cats.get(cat) or cats.get("general", {})
        return cat_data.get("no_docs_continuation", "কোনো লিখিত কাগজপত্র না থাকলেও আপনার আইনি প্রক্রিয়া অব্যাহত থাকবে। ঘটনার বিষয়ে কোনো প্রত্যক্ষদর্শী সাক্ষী অবগত আছেন কি?")

    def get_no_docs_chips(self, category: Optional[str] = None) -> List[str]:
        """Returns chips for no-docs continuation inquiry."""
        return [
            "হ্যাঁ, প্রত্যক্ষদর্শী স্থানীয় সাক্ষী আছেন",
            "গ্রামের মেম্বার ও মুরব্বিরা বিষয়টি জানেন",
            "কোনো সাক্ষী নেই, পরামর্শ চাই"
        ]


# =============================================================================
# Module-level singleton
# =============================================================================
_builder: Optional[PromptBuilder] = None


def get_prompt_builder() -> PromptBuilder:
    """Get or create the singleton PromptBuilder instance."""
    global _builder
    if _builder is None:
        _builder = PromptBuilder()
    return _builder
