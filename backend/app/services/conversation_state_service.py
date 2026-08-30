"""
Multi-Turn Clarification, Structured Context State, and Refined Retrieval Planning Service.
Phase 7B Implementation.

Deterministic, observation-only conversational context tracking:
1. Multi-turn attribute extraction (symptoms, anatomical sub-locations, duration, precipitating events, associated symptoms, user-stated severity/age).
2. Strict non-diagnostic state updates (no inferred disease, no speculative risk scores).
3. Refined query representation synthesis for Candidate B retrieval.
4. Deterministic clarification question planner with hard safety turn-limit (MAX_CLARIFICATION_TURNS = 3).
5. Evidence sufficiency assessment after each clarification turn.
"""

import re
from typing import List, Optional, Dict, Any, Tuple
from app.schemas.api_models import (
    ConversationContextState,
    ConversationAction,
    ClarificationState,
    ClarificationQuestion,
    QueryIntentCategory,
    EvidenceSufficiencyState,
    RetrievedEvidenceChunk
)
from app.services.query_understanding_service import (
    detect_query_language,
    resolve_output_language,
    EMERGENCY_RED_FLAG_PATTERNS,
    UNSUPPORTED_CONDITION_PATTERNS
)

MAX_DEFAULT_CLARIFICATION_TURNS = 3

# ---------------------------------------------------------------------------
# 1. Attribute Extraction Lexicons (English, Native Bangla, Banglish)
# ---------------------------------------------------------------------------

SPECIFIC_LOCATION_PATTERNS = [
    # Leg/Foot sub-locations
    (r'\b(gorali|gorar|ankle|heel|ankle\s*joint)\b|(গোড়ালি|গোড়ালি)', "ankle/heel"),
    (r'\b(hatu|khato|knee|knee\s*joint)\b|(হাঁটু|হাটু)', "knee"),
    (r'\b(pindoli|calf|shin|dada)\b|(পিণ্ডলি|পায়ের\s*ডিম|পায়ের\s*ডিম)', "calf/shin"),
    (r'\b(pata|foot\s*sole|sole|arch|toes|angul)\b|(পায়ের\s*পাতা|পায়ের\s*আঙ্গুল|আঙ্গুল|আঙুল)', "foot/toes"),
    (r'\b(uru|thigh|groin)\b|(উরু)', "thigh"),
    # Arm/Hand sub-locations
    (r'\b(kobji|wrist)\b|(কব্জি)', "wrist"),
    (r'\b(kony|elbow)\b|(কনুই)', "elbow"),
    (r'\b(kad|shoulder)\b|(কাঁধ)', "shoulder"),
    (r'\b(hater\s*talu|palm|fingers)\b|(হাতের\s*তালু|আঙুল)', "hand/fingers"),
    # Head sub-locations
    (r'\b(ekpashe|one\s*side|unilateral|kopal|forehead)\b|(একপাশে|কপাল)', "forehead/one-sided"),
    (r'\b(ghor|back\s*of\s*head|neck)\b|(ঘাড়|ঘাড়)', "neck/back of head"),
]

PRECIPITATING_EVENT_PATTERNS = [
    # Trauma / Sprain / Fall
    (r'\b(pore\s*gechi|achhar|twisting|twist|moshkacche|moshke|sprain|injury|sports|fell|tripped|slip)\b|(আঘাত|মচকে|পড়ে\s*গেছি|পড়ে\s*গেছি)', "sprain/injury"),
    # Cut / Wound / Laceration
    (r'\b(kete\s*geche|kete|churi|knife|glass|blade|bleeding|wound|cut|laceration)\b|(কেটে\s*গেছে|কেটে|রক্তপাত|রক্ত\s*পড়ছে|রক্ত\s*পড়ছে|ক্ষত)', "cut/wound"),
    # Thermal burn / Scald
    (r'\b(gorom\s*tel|gorom\s*pani|pure\s*geche|pure|hot\s*oil|hot\s*water|fire|steam|burn|scald)\b|(পুড়ে\s*গেছে|পুড়ে|গরম\s*তেল|গরম\s*পানি)', "thermal_burn"),
    # Insect bite / sting
    (r'\b(poka|bee|wasp|ant|mosquito|kamor|sting|bite|stings)\b|(পোকা|মৌমাছি|কামড়|কামড়)', "insect_bite"),
    # Heavy / oily food
    (r'\b(oily\s*food|heavy\s*food|khabar\s*por|after\s*eating|teljukto)\b|(তেলযুক্ত\s*খাবার|ভারী\s*খাবার)', "post_meal_reflux"),
    # Negative confirmation / No trauma
    (r'\b(pore\s*jai\s*nai|no\s*injury|kichu\s*hoy\s*nai|emnitei|spontaneous|without\s*injury)\b|(আঘাত\s*পাইনি|এমনিতেই)', "no_trauma_reported"),
]

ASSOCIATED_SYMPTOM_PATTERNS = [
    (r'\b(fule\s*geche|fola|fule|swelling|swollen|edema)\b|(ফোলা|ফুলে\s*গেছে|ফুলে)', "swelling"),
    (r'\b(lal\s*hoye\s*ache|lal|redness|red)\b|(লাল|লালচে|লাল\s*হয়ে)', "redness"),
    (r'\b(gorom|warmth|hot)\b|(উত্তপ্ত)', "local_warmth"),
    (r'\b(obosh|numbness|tingling|jhinjhin)\b|(ঝিঁঝি|অবশ)', "numbness"),
    (r'\b(jor|fever|high\s*temperature)\b|(জ্বর)', "fever"),
    (r'\b(bomi|nausea|vomiting)\b|(বমি|বমিভাব)', "nausea/vomiting"),
    (r'\b(rash|khujli|itching|itch)\b|(চুলকানি|র‍্যাশ)', "itching/rash"),
    (r'\b(kash|cough)\b|(কাশি)', "cough"),
]

DURATION_PATTERNS = [
    (r'\b(kal\s*theke|yesterday|1\s*day|ek\s*din)\b|(গতকাল\s*থেকে|গতকাল|১\s*দিন)', "1 day"),
    (r'\b(2|dui|two)\s*(din|days)\b|(২\s*দিন|দুই\s*দিন)', "2 days"),
    (r'\b(3|tin|three)\s*(din|days)\b|(৩\s*দিন|তিন\s*দিন)', "3 days"),
    (r'\b(ek\s*shoptaho|1\s*week|one\s*week)\b|(এক\s*সপ্তাহ|১\s*সপ্তাহ)', "1 week"),
    (r'\b(koek\s*ghonta|few\s*hours|today|sudden)\b|(আজকে|হঠাৎ|কয়েক\s*ঘণ্টা)', "today/hours"),
]

SEVERITY_PATTERNS = [
    (r'\b(prochondo|severe|unbearable|oshojjo|prochondho)\b|(তীব্র|অসহ্য|মারাত্মক)', "severe"),
    (r'\b(halka|mild|minor|slight)\b|(সামান্য|হালকা)', "mild"),
    (r'\b(moddhombidho|moderate)\b|(মাঝারি)', "moderate"),
]

AGE_PATTERNS = [
    (r'\b(baccha|shishu|child|baby|infant|toddler)\b|(বাচ্চা|শিশু|সন্তান)', "child"),
    (r'\b(briddho|elderly|senior|old\s*age)\b|(বয়স্ক|বৃদ্ধ)', "elderly"),
    (r'\b(adult|grown\s*up)\b|(বড়|প্রাপ্তবয়স্ক)', "adult"),
]

# ---------------------------------------------------------------------------
# 2. Conversation State Service
# ---------------------------------------------------------------------------

class ConversationStateService:
    """
    Deterministic conversational context state manager & clarification planner.
    """

    def extract_attributes(self, text: str, current_state: Optional[ConversationContextState] = None) -> Dict[str, Any]:
        """Extract explicit user-stated clinical attributes with zero speculative diagnosis."""
        t_clean = text.strip()
        t_lower = t_clean.lower()
        
        extracted: Dict[str, Any] = {
            "specific_location": None,
            "precipitating_event": None,
            "associated_symptoms": [],
            "duration": None,
            "severity_stated": None,
            "user_age_group": None,
            "relevant_negatives": [],
            "red_flags": []
        }

        # 1. Specific location
        for pattern, loc in SPECIFIC_LOCATION_PATTERNS:
            if re.search(pattern, t_lower, re.IGNORECASE):
                extracted["specific_location"] = loc
                break

        # 2. Precipitating event / Mechanism
        for pattern, evt in PRECIPITATING_EVENT_PATTERNS:
            if re.search(pattern, t_lower, re.IGNORECASE):
                if evt == "no_trauma_reported":
                    extracted["relevant_negatives"].append("no trauma / injury reported")
                    extracted["precipitating_event"] = "spontaneous / no injury"
                else:
                    extracted["precipitating_event"] = evt
                break

        # 3. Associated symptoms
        for pattern, sym in ASSOCIATED_SYMPTOM_PATTERNS:
            if re.search(pattern, t_lower, re.IGNORECASE):
                if sym not in extracted["associated_symptoms"]:
                    extracted["associated_symptoms"].append(sym)

        # 4. Duration
        for pattern, dur in DURATION_PATTERNS:
            if re.search(pattern, t_lower, re.IGNORECASE):
                extracted["duration"] = dur
                break

        # 5. Severity (only if explicitly stated)
        for pattern, sev in SEVERITY_PATTERNS:
            if re.search(pattern, t_lower, re.IGNORECASE):
                extracted["severity_stated"] = sev
                break

        # 6. Age group (only if explicitly stated)
        for pattern, age in AGE_PATTERNS:
            if re.search(pattern, t_lower, re.IGNORECASE):
                extracted["user_age_group"] = age
                break

        # 7. Red flags
        for pattern, desc in EMERGENCY_RED_FLAG_PATTERNS:
            if re.search(pattern, t_lower, re.IGNORECASE):
                extracted["red_flags"].append(desc)

        return extracted

    def update_context_state(
        self,
        current_state: Optional[ConversationContextState],
        message: str,
        detected_lang: str,
        preferred_lang: str = "auto",
        initial_qu_body_location: Optional[str] = None
    ) -> ConversationContextState:
        """
        Deterministically merge new message attributes into structured context state.
        """
        extracted = self.extract_attributes(message)
        
        if current_state is None:
            # Initialize new state
            state = ConversationContextState(
                session_id=f"sess-{abs(hash(message)) % 1000000}",
                turn_count=1,
                clarification_turn_count=0,
                max_clarification_turns=MAX_DEFAULT_CLARIFICATION_TURNS,
                language_modality=detected_lang,
                response_language_preference=preferred_lang,
                symptom="pain",
                body_location=initial_qu_body_location or "body",
                specific_location=extracted["specific_location"],
                duration=extracted["duration"],
                severity_stated=extracted["severity_stated"],
                associated_symptoms=extracted["associated_symptoms"],
                precipitating_event=extracted["precipitating_event"],
                user_age_group=extracted["user_age_group"],
                red_flags=extracted["red_flags"],
                relevant_negatives=extracted["relevant_negatives"],
                clarification_state=ClarificationState.NOT_NEEDED,
                unanswered_fields=[],
                next_action=ConversationAction.ANSWER
            )
        else:
            state = current_state.model_copy(deep=True)
            state.turn_count += 1
            state.language_modality = detected_lang
            state.response_language_preference = preferred_lang
            
            # Merge non-empty extracted attributes
            if extracted["specific_location"]:
                state.specific_location = extracted["specific_location"]
            if extracted["precipitating_event"]:
                state.precipitating_event = extracted["precipitating_event"]
            if extracted["duration"]:
                state.duration = extracted["duration"]
            if extracted["severity_stated"]:
                state.severity_stated = extracted["severity_stated"]
            if extracted["user_age_group"]:
                state.user_age_group = extracted["user_age_group"]
            if initial_qu_body_location and state.body_location in [None, "body"]:
                state.body_location = initial_qu_body_location

            for sym in extracted["associated_symptoms"]:
                if sym not in state.associated_symptoms:
                    state.associated_symptoms.append(sym)
                    
            for neg in extracted["relevant_negatives"]:
                if neg not in state.relevant_negatives:
                    state.relevant_negatives.append(neg)
                    
            for rf in extracted["red_flags"]:
                if rf not in state.red_flags:
                    state.red_flags.append(rf)

        return state

    def build_refined_query(self, state: ConversationContextState) -> str:
        """
        Build an enriched retrieval query from accumulated context attributes.
        Combines symptoms, specific anatomical sites, and mechanism for Candidate B retrieval.
        """
        tokens: List[str] = []
        
        # Primary body location and specific location
        if state.body_location and state.body_location != "body":
            tokens.append(state.body_location)
        if state.specific_location:
            tokens.append(state.specific_location)
            
        # Precipitating event / mechanism terms
        if state.precipitating_event:
            evt = state.precipitating_event
            if "sprain" in evt or "injury" in evt:
                tokens.append("sprains and strains sprain ankle twist injury rest ice compression elevation PRICE")
            elif "cut" in evt or "wound" in evt:
                tokens.append("cuts and grazes cut wound bleeding pressure dressing clean bandage")
            elif "thermal" in evt or "burn" in evt:
                tokens.append("burns and scalds cool running tap water 20 minutes thermal burn")
            elif "insect" in evt:
                tokens.append("insect bites and stings bee wasp redness swelling itching")
            elif "reflux" in evt:
                tokens.append("heartburn acid reflux indigestion burning sensation antacids")
            elif "spontaneous" in evt or "no injury" in evt:
                tokens.append("pain general ache resting")

        # Associated symptoms
        if state.associated_symptoms:
            for s in state.associated_symptoms:
                tokens.append(s)
                
        # Primary symptom
        if state.symptom:
            tokens.append(state.symptom)
            
        # Age modifier
        if state.user_age_group == "child":
            tokens.append("children high temperature fever")

        refined = " ".join(tokens).strip()
        state.refined_retrieval_query = refined
        return refined

    def plan_clarification_question(
        self,
        state: ConversationContextState,
        preferred_lang: str = "auto"
    ) -> Optional[ClarificationQuestion]:
        """
        Deterministic clarification planner: selects next focused question based on missing fields.
        Enforces MAX_CLARIFICATION_TURNS = 3.
        """
        if state.clarification_turn_count >= state.max_clarification_turns:
            state.clarification_state = ClarificationState.MAX_TURNS_EXCEEDED
            state.next_action = ConversationAction.ABSTAIN
            return None

        detected_lang = state.language_modality
        resp_lang = resolve_output_language(detected_lang, preferred_lang)
        
        # Turn 1: If precipitating event / injury mechanism is unknown
        if not state.precipitating_event:
            state.clarification_turn_count += 1
            state.clarification_state = ClarificationState.IN_PROGRESS
            state.unanswered_fields = ["precipitating_event", "specific_location"]
            
            loc_label = state.body_location or "body"
            q_en = (
                f"To provide relevant first aid information for {loc_label} pain, could you please specify what happened? "
                "For example: Is there swelling or a sprain from an injury, a cut or wound, a burn, or an insect bite?"
            )
            q_bn = (
                f"{loc_label} ব্যথার সঠিক প্রাথমিক তথ্যের জন্য অনুগ্রহ করে বিস্তারিত জানান: "
                "এটি কি মচকে যাওয়া বা আঘাতের ব্যথা, কেটে যাওয়া বা রক্তপাত, পুড়ে যাওয়া, নাকি কোনো ফোলা বা পোকার কামড়?"
            )
            opts = [
                "আঘাত বা মচকে গেছে (Sprain/Injury)" if resp_lang == "bn" else "Sprain or injury",
                "কেটে গেছে বা রক্তপাত (Cut/Bleeding)" if resp_lang == "bn" else "Cut or bleeding",
                "পুড়ে গেছে (Burn/Scald)" if resp_lang == "bn" else "Burn or scald",
                "পোকার কামড় (Insect Bite)" if resp_lang == "bn" else "Insect bite / sting",
                "আঘাত ছাড়াই সাধারণ ব্যথা (No injury/spontaneous)" if resp_lang == "bn" else "No injury / General pain"
            ]
            return ClarificationQuestion(
                field_to_clarify="precipitating_event",
                question_text_en=q_en,
                question_text_bn=q_bn,
                options=opts
            )

        # Turn 2: If specific sub-location is still unknown
        if not state.specific_location and state.body_location == "leg/foot":
            state.clarification_turn_count += 1
            state.clarification_state = ClarificationState.IN_PROGRESS
            state.unanswered_fields = ["specific_location", "duration"]
            
            q_en = "Which specific part of your leg or foot is hurting most?"
            q_bn = "পায়ের কোন অংশে ব্যথাটা সবচেয়ে বেশি?"
            opts = [
                "গোড়ালি (Ankle/Heel)" if resp_lang == "bn" else "Ankle / Heel",
                "হাঁটু (Knee)" if resp_lang == "bn" else "Knee",
                "পায়ের পাতা বা আঙ্গুল (Foot/Toes)" if resp_lang == "bn" else "Foot sole / Toes",
                "পিণ্ডলি (Calf)" if resp_lang == "bn" else "Calf / Shin",
                "পুরো পা (Whole leg)" if resp_lang == "bn" else "Whole leg"
            ]
            return ClarificationQuestion(
                field_to_clarify="specific_location",
                question_text_en=q_en,
                question_text_bn=q_bn,
                options=opts
            )

        # Turn 3: Duration / Associated symptoms
        if not state.duration:
            state.clarification_turn_count += 1
            state.clarification_state = ClarificationState.IN_PROGRESS
            state.unanswered_fields = ["duration"]
            
            q_en = "How long have you been experiencing this symptom?"
            q_bn = "কতক্ষণ বা কতদিন ধরে এই লক্ষণটি দেখা দিয়েছে?"
            opts = [
                "আজকে বা মাত্র কয়েক ঘণ্টা (Today / Few hours)" if resp_lang == "bn" else "Today / Few hours",
                "গতকাল থেকে / ১ দিন (Since yesterday / 1 day)" if resp_lang == "bn" else "Since yesterday / 1 day",
                "২-৩ দিন ধরে (2-3 days)" if resp_lang == "bn" else "2-3 days",
                "১ সপ্তাহের বেশি (More than 1 week)" if resp_lang == "bn" else "More than 1 week"
            ]
            return ClarificationQuestion(
                field_to_clarify="duration",
                question_text_en=q_en,
                question_text_bn=q_bn,
                options=opts
            )

        # If all relevant fields are addressed
        state.clarification_state = ClarificationState.RESOLVED
        state.unanswered_fields = []
        return None

    def evaluate_evidence_sufficiency(
        self,
        evidence: List[RetrievedEvidenceChunk],
        state: ConversationContextState
    ) -> Tuple[EvidenceSufficiencyState, ConversationAction, str]:
        """
        Evaluate if retrieved evidence passages provide sufficient clinical grounding for the clarified context.
        """
        if not evidence:
            return EvidenceSufficiencyState.INSUFFICIENT, ConversationAction.ABSTAIN, "No evidence passages retrieved."

        top_chunk = evidence[0]
        top_score = top_chunk.rerank_score
        top_source = top_chunk.parent_source_id

        # Specific clinical domain matching against active 14 NHS sources
        if state.precipitating_event:
            evt = state.precipitating_event
            if "cut" in evt and (top_source == "DOC-NHS-006" or any(e.parent_source_id == "DOC-NHS-006" for e in evidence[:3])):
                state.clarification_state = ClarificationState.RESOLVED
                return EvidenceSufficiencyState.SUFFICIENT, ConversationAction.ANSWER, f"High-confidence match with NHS Cuts & Grazes (score: {top_score:.4f})."
            elif ("thermal" in evt or "burn" in evt) and (top_source == "DOC-NHS-005" or any(e.parent_source_id == "DOC-NHS-005" for e in evidence[:3])):
                state.clarification_state = ClarificationState.RESOLVED
                return EvidenceSufficiencyState.SUFFICIENT, ConversationAction.ANSWER, f"High-confidence match with NHS Burns & Scalds (score: {top_score:.4f})."
            elif "sprain" in evt:
                # Musculoskeletal sprains are outside the active 14 NHS conditions
                state.clarification_state = ClarificationState.UNSUPPORTED_TOPIC
                return EvidenceSufficiencyState.UNSUPPORTED, ConversationAction.ABSTAIN, "Musculoskeletal sprains and strains are outside the active 14 NHS first aid conditions."

        # Check chest pain match
        if (state.body_location == "chest" or "chest" in (state.symptom or "")) and (top_source == "DOC-NHS-012" or any(e.parent_source_id == "DOC-NHS-012" for e in evidence[:3])):
            state.clarification_state = ClarificationState.RESOLVED
            return EvidenceSufficiencyState.SUFFICIENT, ConversationAction.ANSWER, f"Match with NHS Chest Pain (score: {top_score:.4f})."

        # General score threshold
        if top_score >= 0.65:
            state.clarification_state = ClarificationState.RESOLVED
            return EvidenceSufficiencyState.SUFFICIENT, ConversationAction.ANSWER, f"Sufficient confidence retrieval ({top_score:.4f})."

        # Check turn limit
        if state.clarification_turn_count >= state.max_clarification_turns or state.turn_count >= 3:
            state.clarification_state = ClarificationState.MAX_TURNS_EXCEEDED
            return EvidenceSufficiencyState.UNSUPPORTED, ConversationAction.ABSTAIN, "Maximum clarification turns reached without sufficient evidence match."

        return EvidenceSufficiencyState.INSUFFICIENT, ConversationAction.CLARIFY, "Evidence confidence insufficient; further clarification needed."

# Singleton instance
_conversation_state_instance: Optional[ConversationStateService] = None

def get_conversation_state_service() -> ConversationStateService:
    global _conversation_state_instance
    if _conversation_state_instance is None:
        _conversation_state_instance = ConversationStateService()
    return _conversation_state_instance
