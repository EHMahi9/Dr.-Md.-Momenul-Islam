"""
Adaptive Clarification Planner, Structured Context State, and Question-Utility Service.
Phase 7C Implementation.

Deterministic, inspectable, non-diagnostic conversational clarification:
1. Question-Utility Model: Engineering decision model for selecting the single highest-value question.
2. Structured Context State: Tracks user-supplied facts, missing fields, and asked questions to prevent duplicates.
3. Corpus-Aware Boundaries: Detects out-of-corpus topics (e.g., musculoskeletal sprains) and halts questioning early.
4. Stopping Rules: Stops on sufficient evidence, out-of-corpus topic, emergency route, or turn limit (MAX=3).
5. Strict Non-Diagnostic Invariant: Zero disease diagnosis, zero risk prediction, zero medication prescribing.
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
    (r'\b(bah|arm|forearm)\b|(বাহু)', "forearm/arm"),
    # Head/Face sub-locations
    (r'\b(ekpashe|one\s*side|unilateral|kopal|forehead)\b|(একপাশে|কপাল)', "forehead/one-sided"),
    (r'\b(ghor|back\s*of\s*head|neck)\b|(ঘাড়|ঘাড়)', "neck/back of head"),
    (r'\b(chokh|eye|eyes)\b|(চোখ|চোখে)', "eyes"),
    (r'\b(kan|ear|ears)\b|(কান|কানে)', "ears"),
    (r'\b(nak|nose)\b|(নাক|নাকে)', "nose"),
    # Chest/Abdomen sub-locations
    (r'\b(pet|stomach|belly|abdomen)\b|(পেট|পেটে)', "abdomen/stomach"),
    (r'\b(komor|back|lower\s*back)\b|(কোমর|পিঠ)', "lower back/back"),
]

PRECIPITATING_EVENT_PATTERNS = [
    # Trauma / Sprain / Fall (Out-of-corpus in 14 NHS active conditions)
    (r'\b(pore\s*gechi|achhar|twisting|twist|moshkacche|moshke|sprain|injury|sports|fell|tripped|slip)\b|(আঘাত|মচকে|পড়ে\s*গেছি|পড়ে\s*গেছি)', "sprain/injury"),
    # Cut / Wound / Laceration (DOC-NHS-006)
    (r'\b(kete\s*geche|kete|churi|knife|glass|blade|bleeding|wound|cut|laceration)\b|(কেটে\s*গেছে|কেটে|রক্তপাত|রক্ত\s*পড়ছে|রক্ত\s*পড়ছে|ক্ষত)', "cut/wound"),
    # Thermal burn / Scald (DOC-NHS-005)
    (r'\b(gorom\s*tel|gorom\s*pani|pure\s*geche|pure|hot\s*oil|hot\s*water|fire|steam|burn|scald)\b|(পুড়ে\s*গেছে|পুড়ে|গরম\s*তেল|গরম\s*পানি)', "thermal_burn"),
    # Insect bite / sting (DOC-NHS-011)
    (r'\b(poka|bee|wasp|ant|mosquito|kamor|sting|bite|stings)\b|(পোকা|মৌমাছি|কামড়|কামড়)', "insect_bite"),
    # Heavy / oily food (DOC-NHS-014 Heartburn)
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
    (r'\b(matha\s*ghur|dizziness|giddy)\b|(মাথা\s*ঘোরা|মাথা\s*ঘুরা)', "dizziness"),
]

DURATION_PATTERNS = [
    (r'\b(kal\s*theke|yesterday|1\s*day|ek\s*din)\b|(গতকাল\s*থেকে|গতকাল|১\s*দিন)', "1 day"),
    (r'\b(2|dui|two)\s*(din|days)\b|(২\s*দিন|দুই\s*দিন)', "2 days"),
    (r'\b(3|tin|three)\s*(din|days)\b|(৩\s*দিন|তিন\s*দিন)', "3 days"),
    (r'\b(ek\s*shoptaho|1\s*week|one\s*week)\b|(এক\s*সপ্তাহ|১\s*সপ্তাহ)', "1 week"),
    (r'\b(koek\s*ghonta|few\s*hours|today|sudden)\b|(আজকে|হঠাৎ|কয়েক\s*ঘণ্টা)', "today/hours"),
    (r'\b(onek\s*din|chronic|mas\s*dhore|months)\b|(কয়েক\s*মাস|অনেক\s*দিন)', "chronic/months"),
]

SEVERITY_PATTERNS = [
    (r'\b(prochondo|severe|unbearable|oshojjo|prochondho)\b|(তীব্র|অসহ্য|মারাত্মক)', "severe"),
    (r'\b(halka|mild|minor|slight)\b|(সামান্য|হালকা)', "mild"),
    (r'\b(moddhombidho|moderate)\b|(মাঝারি)', "moderate"),
]

AGE_PATTERNS = [
    (r'\b(baccha|bacchar|shishu|shishur|child|children|baby|infant|toddler|\d+\s*(bochor|bosor|yr|years?|bochorer|bosorer)\s*(baccha|bacchar|child|shishu)?)\b|(বাচ্চা|বাচ্চার|শিশু|শিশুর|সন্তান|\d+\s*বছরের\s*শিশু|\d+\s*বছরের)', "child"),
    (r'\b(briddho|elderly|senior|old\s*age)\b|(বয়স্ক|বৃদ্ধ)', "elderly"),
    (r'\b(adult|grown\s*up)\b|(বড়|প্রাপ্তবয়স্ক)', "adult"),
]

# ---------------------------------------------------------------------------
# 2. Question Candidate Definition & Utility Model
# ---------------------------------------------------------------------------

class QuestionCandidate:
    """Represents a potential clarification question with utility scoring rationale."""
    def __init__(
        self,
        field: str,
        retrieval_gain: float,
        safety_gain: float,
        ambiguity_reduction: float,
        corpus_relevance: float,
        question_en: str,
        question_bn: str,
        options_en: List[str],
        options_bn: List[str],
        rationale: str
    ):
        self.field = field
        self.retrieval_gain = retrieval_gain
        self.safety_gain = safety_gain
        self.ambiguity_reduction = ambiguity_reduction
        self.corpus_relevance = corpus_relevance
        self.question_en = question_en
        self.question_bn = question_bn
        self.options_en = options_en
        self.options_bn = options_bn
        self.rationale = rationale

    def compute_utility(
        self,
        state: ConversationContextState,
        evidence: Optional[List[RetrievedEvidenceChunk]] = None
    ) -> float:
        """
        Calculate engineering Question Utility:
        Utility = retrieval_gain + safety_gain + ambiguity_reduction + corpus_relevance
                  - redundancy_penalty - unnecessary_penalty
        """
        # Redundancy penalty: heavily penalize already asked or populated fields
        if self.field in state.asked_questions:
            return -1.0
        val = getattr(state, self.field, None)
        if val is not None and not (isinstance(val, list) and len(val) == 0):
            return -1.0

        # Unnecessary question penalty if evidence is already confident
        unnecessary_penalty = 0.0
        if evidence and len(evidence) > 0:
            top_chunk = evidence[0]
            if top_chunk.rerank_score >= 0.65:
                unnecessary_penalty = 0.60
            elif top_chunk.rerank_score >= 0.50:
                unnecessary_penalty = 0.20

        # Penalty if topic is already determined out of corpus
        corpus_adj = self.corpus_relevance
        if state.precipitating_event == "sprain/injury":
            corpus_adj -= 0.50

        total_utility = (
            self.retrieval_gain +
            self.safety_gain +
            self.ambiguity_reduction +
            corpus_adj -
            unnecessary_penalty
        )
        return round(max(0.0, total_utility), 4)


# ---------------------------------------------------------------------------
# 3. Conversation State Service (Phase 7C Adaptive Planner)
# ---------------------------------------------------------------------------

class ConversationStateService:
    """
    Adaptive Conversational Clarification Planner and Context State Engine.
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
                asked_questions=[],
                missing_high_value_fields=[],
                candidate_question_scores={},
                stopping_reason=None,
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

        # Update remaining missing fields
        missing: List[str] = []
        for field in ["precipitating_event", "specific_location", "associated_symptoms", "duration", "user_age_group"]:
            val = getattr(state, field, None)
            if val is None or (isinstance(val, list) and len(val) == 0):
                if field not in state.asked_questions:
                    missing.append(field)
        state.missing_high_value_fields = missing

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

    def _generate_candidate_questions(self, state: ConversationContextState) -> List[QuestionCandidate]:
        """
        Generate candidate clarification questions tailored to the current context.
        """
        loc_label = state.body_location or "body"
        candidates: List[QuestionCandidate] = []

        # 1. Precipitating Event / Mechanism Candidate
        q_precip = QuestionCandidate(
            field="precipitating_event",
            retrieval_gain=0.45,
            safety_gain=0.20,
            ambiguity_reduction=0.30,
            corpus_relevance=0.35,
            question_en=f"To provide relevant first aid information for {loc_label} pain, could you please specify what happened?",
            question_bn=f"{loc_label} ব্যথার সঠিক প্রাথমিক তথ্যের জন্য অনুগ্রহ করে জানান: এটি কি মচকে যাওয়া বা আঘাতের ব্যথা, কেটে যাওয়া বা রক্তপাত, পুড়ে যাওয়া, নাকি কোনো ফোলা বা পোকার কামড়?",
            options_en=[
                "Sprain or injury from a fall / twist",
                "Cut, scrape or bleeding wound",
                "Burn or hot liquid scald",
                "Insect bite or sting",
                "General ache without any injury"
            ],
            options_bn=[
                "আঘাত বা মচকে গেছে (Sprain/Injury)",
                "কেটে গেছে বা রক্তপাত (Cut/Bleeding)",
                "পুড়ে গেছে (Burn/Scald)",
                "পোকার কামড় (Insect Bite)",
                "আঘাত ছাড়াই সাধারণ ব্যথা (No injury/spontaneous)"
            ],
            rationale="Disambiguates primary first-aid condition across Burns, Cuts, Insect Bites, and Sprains."
        )
        candidates.append(q_precip)

        # 2. Specific Anatomical Sub-Location Candidate
        if state.body_location in ["leg/foot", "arm/hand", "head", "chest"]:
            if state.body_location == "leg/foot":
                q_loc_en = "Which specific part of your leg or foot is hurting most?"
                q_loc_bn = "পায়ের কোন অংশে ব্যথাটা সবচেয়ে বেশি?"
                opts_en = ["Ankle / Heel", "Knee", "Foot sole / Toes", "Calf / Shin", "Whole leg"]
                opts_bn = ["গোড়ালি (Ankle/Heel)", "হাঁটু (Knee)", "পায়ের পাতা বা আঙ্গুল (Foot/Toes)", "পিণ্ডলি (Calf)", "পুরো পা (Whole leg)"]
            elif state.body_location == "arm/hand":
                q_loc_en = "Which specific part of your arm or hand is affected?"
                q_loc_bn = "হাতের কোন অংশে সমস্যা বা ব্যথা হচ্ছে?"
                opts_en = ["Wrist", "Elbow", "Shoulder", "Palm / Fingers", "Whole arm"]
                opts_bn = ["কব্জি (Wrist)", "কনুই (Elbow)", "কাঁধ (Shoulder)", "হাতের তালু বা আঙ্গুল (Hand/Fingers)", "পুরো হাত (Whole arm)"]
            elif state.body_location == "head":
                q_loc_en = "Where is the head pain or discomfort located?"
                q_loc_bn = "মাথার কোন জায়গায় ব্যথাটা বেশি হচ্ছে?"
                opts_en = ["One side / Temple", "Forehead", "Back of head / Neck", "Whole head"]
                opts_bn = ["মাথার একপাশে (One side)", "কপালে (Forehead)", "ঘাড় বা মাথার পেছনে (Neck/Back)", "পুরো মাথায় (Whole head)"]
            else:
                q_loc_en = "Where specifically is the discomfort located?"
                q_loc_bn = "শরীরের কোন নির্দিষ্ট স্থানে সমস্যা হচ্ছে?"
                opts_en = ["Central chest", "Upper abdomen", "Left side", "Other"]
                opts_bn = ["বুকের মাঝখানে", "পেটের ওপরের অংশ", "বামের দিকে", "অন্যান্য"]

            q_loc = QuestionCandidate(
                field="specific_location",
                retrieval_gain=0.35,
                safety_gain=0.15,
                ambiguity_reduction=0.30,
                corpus_relevance=0.20,
                question_en=q_loc_en,
                question_bn=q_loc_bn,
                options_en=opts_en,
                options_bn=opts_bn,
                rationale="Narrows anatomical search space to improve passage retrieval precision."
            )
            candidates.append(q_loc)

        # 3. Associated Symptoms Candidate
        q_assoc = QuestionCandidate(
            field="associated_symptoms",
            retrieval_gain=0.30,
            safety_gain=0.35,
            ambiguity_reduction=0.25,
            corpus_relevance=0.25,
            question_en="Are you experiencing any other accompanying symptoms?",
            question_bn="এর সাথে কি নিচের কোনো লক্ষণ লক্ষ্য করছেন?",
            options_en=["Swelling", "Bleeding", "Fever", "Redness", "No other symptoms"],
            options_bn=["ফোলা ভাব (Swelling)", "রক্তপাত (Bleeding)", "জ্বর (Fever)", "লালচে ভাব (Redness)", "অন্য কোনো লক্ষণ নেই (None)"],
            rationale="Identifies safety-critical red flags or secondary symptoms for first-aid grounding."
        )
        candidates.append(q_assoc)

        # 4. Duration Candidate
        q_dur = QuestionCandidate(
            field="duration",
            retrieval_gain=0.15,
            safety_gain=0.10,
            ambiguity_reduction=0.15,
            corpus_relevance=0.10,
            question_en="How long have you been experiencing this symptom?",
            question_bn="কতক্ষণ বা কতদিন ধরে এই লক্ষণটি দেখা দিয়েছে?",
            options_en=["Today / Few hours", "Since yesterday / 1 day", "2-3 days", "More than 1 week"],
            options_bn=["আজকে বা কয়েক ঘণ্টা (Today / Few hours)", "গতকাল থেকে / ১ দিন (1 day)", "২-৩ দিন ধরে (2-3 days)", "১ সপ্তাহের বেশি (More than 1 week)"],
            rationale="Determines acute vs chronic onset to refine first-aid guidance."
        )
        candidates.append(q_dur)

        # 5. Age Group Candidate (High priority if symptom is fever or child-relevant)
        age_gain = 0.40 if "fever" in (state.symptom or "") or "jor" in (state.symptom or "") else 0.10
        q_age = QuestionCandidate(
            field="user_age_group",
            retrieval_gain=age_gain,
            safety_gain=0.25,
            ambiguity_reduction=0.20,
            corpus_relevance=0.30,
            question_en="Is this symptom experienced by a young child, an adult, or an elderly person?",
            question_bn="এই লক্ষণটি কি কোনো শিশুর, প্রাপ্তবয়স্কের, নাকি কোনো বয়স্ক ব্যক্তির?",
            options_en=["Child (Under 5 years)", "Adult", "Elderly person"],
            options_bn=["শিশু (Child under 5)", "প্রাপ্তবয়স্ক (Adult)", "বয়স্ক ব্যক্তি (Elderly)"],
            rationale="Differentiates child fever protocols (DOC-NHS-010/017) from adult first-aid."
        )
        candidates.append(q_age)

        return candidates

    def plan_clarification_question(
        self,
        state: ConversationContextState,
        preferred_lang: str = "auto",
        evidence: Optional[List[RetrievedEvidenceChunk]] = None
    ) -> Optional[ClarificationQuestion]:
        """
        Adaptive Question Selector:
        Uses Question-Utility model to select the single most informative question.
        Enforces MAX_CLARIFICATION_TURNS = 3, avoids duplicate fields, and halts early when topic is out-of-corpus.
        """
        # Hard turn limit check
        if state.clarification_turn_count >= state.max_clarification_turns:
            state.clarification_state = ClarificationState.MAX_TURNS_EXCEEDED
            state.next_action = ConversationAction.ABSTAIN
            state.stopping_reason = "Maximum clarification turns (3) reached."
            return None

        # Early out-of-corpus check: If user already stated sprain/trauma or unsupported topic
        if state.precipitating_event == "sprain/injury":
            state.clarification_state = ClarificationState.UNSUPPORTED_TOPIC
            state.next_action = ConversationAction.ABSTAIN
            state.stopping_reason = "Musculoskeletal sprains and strains are outside the active 14 NHS sources."
            return None

        detected_lang = state.language_modality
        resp_lang = resolve_output_language(detected_lang, preferred_lang)

        # Generate and score all candidate questions
        candidates = self._generate_candidate_questions(state)
        scored_candidates: List[Tuple[float, QuestionCandidate]] = []
        scores_dict: Dict[str, float] = {}

        for c in candidates:
            utility = c.compute_utility(state, evidence)
            scores_dict[c.field] = utility
            if utility > 0.0:
                scored_candidates.append((utility, c))

        state.candidate_question_scores = scores_dict

        # If no questions have positive utility, stop clarification
        if not scored_candidates:
            state.clarification_state = ClarificationState.RESOLVED
            state.stopping_reason = "No further high-utility clarification fields identified."
            return None

        # Sort by highest utility descending
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_candidate = scored_candidates[0]

        # Update state with selected question
        state.clarification_turn_count += 1
        state.clarification_state = ClarificationState.IN_PROGRESS
        state.asked_questions.append(best_candidate.field)
        state.unanswered_fields = [c.field for _, c in scored_candidates]

        q_text = best_candidate.question_bn if resp_lang == "bn" else best_candidate.question_en
        opts = best_candidate.options_bn if resp_lang == "bn" else best_candidate.options_en

        return ClarificationQuestion(
            field_to_clarify=best_candidate.field,
            question_text_en=best_candidate.question_en,
            question_text_bn=best_candidate.question_bn,
            options=opts,
            utility_score=best_score,
            selection_rationale=best_candidate.rationale
        )

    def evaluate_evidence_sufficiency(
        self,
        evidence: List[RetrievedEvidenceChunk],
        state: ConversationContextState
    ) -> Tuple[EvidenceSufficiencyState, ConversationAction, str]:
        """
        Evaluate if retrieved evidence passages provide sufficient clinical grounding for the clarified context.
        """
        if not evidence:
            state.stopping_reason = "No evidence passages retrieved."
            return EvidenceSufficiencyState.INSUFFICIENT, ConversationAction.ABSTAIN, "No evidence passages retrieved."

        top_chunk = evidence[0]
        top_score = top_chunk.rerank_score
        top_source = top_chunk.parent_source_id

        # Specific clinical domain matching against active 14 NHS sources
        if state.precipitating_event:
            evt = state.precipitating_event
            if "cut" in evt and (top_source == "DOC-NHS-006" or any(e.parent_source_id == "DOC-NHS-006" for e in evidence[:3])):
                state.clarification_state = ClarificationState.RESOLVED
                state.stopping_reason = "Sufficient grounding in NHS Cuts & Grazes."
                return EvidenceSufficiencyState.SUFFICIENT, ConversationAction.ANSWER, f"High-confidence match with NHS Cuts & Grazes (score: {top_score:.4f})."
            elif ("thermal" in evt or "burn" in evt) and (top_source == "DOC-NHS-005" or any(e.parent_source_id == "DOC-NHS-005" for e in evidence[:3])):
                state.clarification_state = ClarificationState.RESOLVED
                state.stopping_reason = "Sufficient grounding in NHS Burns & Scalds."
                return EvidenceSufficiencyState.SUFFICIENT, ConversationAction.ANSWER, f"High-confidence match with NHS Burns & Scalds (score: {top_score:.4f})."
            elif "insect" in evt and (top_source == "DOC-NHS-011" or any(e.parent_source_id == "DOC-NHS-011" for e in evidence[:3])):
                state.clarification_state = ClarificationState.RESOLVED
                state.stopping_reason = "Sufficient grounding in NHS Insect Bites & Stings."
                return EvidenceSufficiencyState.SUFFICIENT, ConversationAction.ANSWER, f"High-confidence match with NHS Insect Bites & Stings (score: {top_score:.4f})."
            elif "sprain" in evt:
                # Musculoskeletal sprains are outside the active 14 NHS conditions
                state.clarification_state = ClarificationState.UNSUPPORTED_TOPIC
                state.stopping_reason = "Musculoskeletal sprains and strains are outside the active 14 NHS first aid conditions."
                return EvidenceSufficiencyState.UNSUPPORTED, ConversationAction.ABSTAIN, "Musculoskeletal sprains and strains are outside the active 14 NHS first aid conditions."

        # Child fever routing
        if state.user_age_group == "child" and (state.symptom == "fever" or "fever" in (state.refined_retrieval_query or "")):
            if top_source == "DOC-NHS-010" or any(e.parent_source_id == "DOC-NHS-010" for e in evidence[:3]):
                state.clarification_state = ClarificationState.RESOLVED
                state.stopping_reason = "Sufficient grounding in NHS High Temperature in Children."
                return EvidenceSufficiencyState.SUFFICIENT, ConversationAction.ANSWER, f"Match with NHS High Temperature in Children (score: {top_score:.4f})."

        # Check chest pain match
        if (state.body_location == "chest" or "chest" in (state.symptom or "")) and (top_source == "DOC-NHS-012" or any(e.parent_source_id == "DOC-NHS-012" for e in evidence[:3])):
            state.clarification_state = ClarificationState.RESOLVED
            state.stopping_reason = "Sufficient grounding in NHS Chest Pain."
            return EvidenceSufficiencyState.SUFFICIENT, ConversationAction.ANSWER, f"Match with NHS Chest Pain (score: {top_score:.4f})."

        # General score threshold
        if top_score >= 0.65:
            state.clarification_state = ClarificationState.RESOLVED
            state.stopping_reason = f"High-confidence retrieval score ({top_score:.4f})."
            return EvidenceSufficiencyState.SUFFICIENT, ConversationAction.ANSWER, f"Sufficient confidence retrieval ({top_score:.4f})."

        # Check turn limit
        if state.clarification_turn_count >= state.max_clarification_turns or state.turn_count >= 3:
            state.clarification_state = ClarificationState.MAX_TURNS_EXCEEDED
            state.stopping_reason = "Maximum clarification turns reached without sufficient evidence match."
            return EvidenceSufficiencyState.UNSUPPORTED, ConversationAction.ABSTAIN, "Maximum clarification turns reached without sufficient evidence match."

        return EvidenceSufficiencyState.INSUFFICIENT, ConversationAction.CLARIFY, "Evidence confidence insufficient; further clarification needed."

# Singleton instance
_conversation_state_instance: Optional[ConversationStateService] = None

def get_conversation_state_service() -> ConversationStateService:
    global _conversation_state_instance
    if _conversation_state_instance is None:
        _conversation_state_instance = ConversationStateService()
    return _conversation_state_instance
