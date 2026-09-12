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
                court_q = cat_fallbacks.get("history_documents_for_court")
                if court_q:
                    return court_q

        # Try exact stage match
        q = cat_fallbacks.get(stage)
        if q:
            return q

        # Try default for this category
        default_q = cat_fallbacks.get("default")
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

        # 0b. Cause of family dispute
        if (
            ("ভরণপোষণ" in q and ("ঝামেলা" in q or "কেন" in q or "কারণ" in q))
            or "ঝামেলা হয়েছে কেন" in q
            or "বিরোধের কারণ" in q
            or "বিরোধের মূল কারণ" in target
            or (target == "cause" and category in ("family_dower_maintenance", "dowry"))
        ):
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
        if "দেনমোহর" in q or "টাকার পরিমাণ" in target or "টাকা" in q or "দাবি" in q:
            return replies_config.get("dower", {}).get("default", [])

        # 3. Marriage Date / Timeline
        if ("বিয়ে" in q) and any(w in q for w in ["সন", "কবে", "সাল", "বছর", "তারিখ"]):
            return replies_config.get("marriage_date", {}).get("default", [])

        # 4. Wages / Unpaid Salary
        if (
            any(w in q for w in ["মজুরি", "বেতন"])
            or any(w in target for w in ["বকেয়া", "মজুরির মোট পরিমাণ"])
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
