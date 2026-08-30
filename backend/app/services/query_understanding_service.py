"""
Query Understanding, Ambiguity Classification, and Conversational Clarification Service.
Phase 7A Track B Foundation.

Deterministic non-diagnostic query understanding:
1. Language detection (English, Native Bangla, Banglish).
2. Intent & sufficiency classification:
   - CLEARLY_ANSWERABLE
   - UNDERSPECIFIED_AMBIGUOUS
   - UNSUPPORTED_ACTIVE_CORPUS
   - POTENTIALLY_EMERGENCY
3. Red-flag emergency detection (safety-first routing).
4. Structured clarification question generation.
5. Evidence presentation policy determination.
"""

import re
from typing import List, Optional, Dict, Any, Tuple
from app.schemas.api_models import (
    QueryIntentCategory,
    EvidenceSufficiencyState,
    ClarificationQuestion,
    EmergencyAdvice,
    QueryUnderstandingResult
)

# ---------------------------------------------------------------------------
# 1. Corpus Domain & Out-of-Domain Lexicons (14 NHS Conditions)
# ---------------------------------------------------------------------------
# Active 14 NHS Conditions:
# DOC-NHS-004: Asthma
# DOC-NHS-005: Burns and scalds
# DOC-NHS-006: Cuts and grazes
# DOC-NHS-007: Dehydration
# DOC-NHS-008: Diarrhoea and vomiting
# DOC-NHS-009: Headaches
# DOC-NHS-010: High temperature (fever) in children
# DOC-NHS-011: Insect bites and stings / Anaphylaxis
# DOC-NHS-012: Chest pain / Heartburn
# DOC-NHS-013: Sprains and strains
# DOC-NHS-014: Earache
# DOC-NHS-015: Sore throat
# DOC-NHS-016: Nosebleeds
# DOC-NHS-017: Allergic rhinitis / Hay fever

# Specific Out-of-Domain condition keywords (NOT in active 14 NHS conditions)
UNSUPPORTED_CONDITION_PATTERNS = [
    (r'\b(diabetes|diabetic|insulin|blood\s*sugar|shuker|sugar)\b|(ডায়াবেটিস|ডায়বেটিস|ইনসুলিন|ব্লাড\s*সুগার)', "Diabetes / Blood Sugar"),
    (r'\b(chickenpox|waterpox|jolboshonto|guti\s*boshonto)\b|(জলবসন্ত|গুটিবসন্ত)', "Chickenpox"),
    (r'\b(tooth|teeth|toothache|dant|dante|dath|dat|dentist|cavity|root\s*canal)\b|(দাঁত|দাঁতে|দাঁতের|ক্যাভিটি|রুট\s*ক্যানেল|রুট\s*ক্যানাল|ডেন্টাল)', "Dental / Toothache"),
    (r'\b(piles|hemorrhoid|hemorrhoids|gosh|arsho)\b|(পাইলস|অর্শ)', "Hemorrhoids / Piles"),
    (r'\b(cancer|tumor|chemotherapy|radiation|chemo)\b|(ক্যান্সার|ক্যান্সারের|টিউমার|কেমোথেরাপি|কেমোথেরাপির|রেডিয়েশন)', "Oncology / Cancer"),
    (r'\b(pregnancy|pregnant|garbhoboti|garbhodharon|miscarriage|trimester|labor\s*pain|delivery)\b|(গর্ভবতী|গর্ভধারণ|প্রেগন্যান্ট|গর্ভপাত|প্রসব|ডেলিভারি)', "Obstetrics / Pregnancy"),
    (r'\b(kidney\s*stone|pathuri|dialysis)\b|(কিডনি\s*পাথর|ডায়ালাইসিস|ডায়ালাইসিস)', "Nephrology / Kidney Stone"),
    (r'\b(jaundice|hepatitis|liver|kamla)\b|(জন্ডিস|হেপাটাইটিস|লিভার)', "Hepatology / Jaundice"),
    (r'\b(hypertension|high\s*pressure|blood\s*pressure)\b|(উচ্চ\s*রক্তচাপ|হাই\s*প্রেসার)', "Hypertension / Blood Pressure Management"),
    (r'\b(glaucoma|cataract|chani|chhani|phaco)\b|(ছানি|চোখের\s*ছানি|গ্লুকোমা)', "Ophthalmology / Eye Surgery"),
    (r'\b(fracture|bhanga\s*har|bone\s*broken)\b|(হাড়\s*ভাঙা|হাড়\s*ভাঙা|ফ্র্যাকচার)', "Bone Fracture"),
]

# Emergency Red-Flag Patterns (English, Banglish, Native Bangla)
EMERGENCY_RED_FLAG_PATTERNS = [
    # Chest pain with red flags or radiation
    (r'(buk|chest|বুক).*(bam\s*haat|left\s*arm|jaw|ghor|heavy|crushing|chape|chap\s*lagche|chap|radiation|radiating|বাম\s*হাত|ভারী|চাপ)', "Potential Acute Cardiac Event / Heart Attack Red Flag"),
    (r'(severe|crushing|heavy|unbearable).*(chest\s*pain|buke\s*betha|বুকের\s*ব্যথা)', "Severe Acute Chest Pain"),
    
    # Respiratory crisis / severe dyspnea
    (r'(shash\s*nite\s*(parchi\s*na|kosto|koshto|koshtho)|shash\s*bondho|shashkosto|shashkoshto|prochondo\s*shash|cannot\s*breathe|struggling\s*to\s*breathe|shortness\s*of\s*breath|blue\s*lips|thot\s*neel|শ্বাস\s*কষ্ট|শ্বাসকষ্ট|শ্বাস\s*নিতে\s*পারছি\s*না|শ্বাস\s*নিতে\s*কষ্ট|শ্বাস\s*বন্ধ|ঠোঁট\s*নীল)', "Severe Acute Respiratory Distress"),
    
    # Leg pain + shortness of breath (Deep Vein Thrombosis -> Pulmonary Embolism concern)
    (r'(paye|pa|leg|calf|পা|পায়ে).*(shash|breathing|kosto|koshto|shortness|শ্বাস|দম)', "Unilateral Leg Pain with Dyspnea (PE/DVT Red Flag)"),
    (r'(shash|breathing|শ্বাস|দম).*(paye|pa|leg|calf|পা|পায়ে)', "Dyspnea with Leg Symptoms (PE/DVT Red Flag)"),
    
    # Anaphylaxis / Airway compromise
    (r'(gola\s*fule|throat\s*closing|tongue\s*swelling|jeeb\s*fule|গলা\s*ফুলে|জিভ\s*ফুলে|গলা\s*আটকে)', "Airway Compromise / Acute Anaphylaxis"),
    
    # Neurological / Stroke
    (r'(mukh\s*beke|face\s*droop|ek\s*pashe\s*obosh|paralysis|slurred\s*speech|kotha\s*joray|মুখ\s*বেঁকে|মুখ\s*বেকে|একপাশে\s*অবশ|প্যারালাইসিস|কথা\s*জড়িয়ে)', "Acute Neurological / Stroke Signs (FAST)"),
    
    # Uncontrolled severe hemorrhage / Unconsciousness
    (r'(behosh|unconscious|fainted|rokto\s*bondho\s*hocche\s*na|massive\s*bleeding|অজ্ঞান|বেহুঁশ|রক্তপাত\s*বন্ধ\s*হচ্ছে\s*না)', "Severe Hemorrhage or Altered Consciousness"),
]

# Specific In-Corpus Clinical Topic Patterns (Unambiguous First Aid queries)
SPECIFIC_IN_CORPUS_PATTERNS = [
    r'\b(pure\s*geche|gorom\s*tel|gorom\s*pani|burn|scald|blister|blistering|cool\s*running\s*water)\b|(পুড়ে\s*গেছে|পুড়ে|গরম\s*পানি|গরম\s*তেল|ঠান্ডা\s*পানি)',
    r'\b(kete\s*rokt|kete\s*geche|churi\s*diye\s*kete|glass\s*cut|blade|bleeding\s*cut|bandage|dressing)\b|(কেটে\s*রক্ত|কেটে\s*গেছে|ছুরি\s*দিয়ে\s*কেটে|ব্যান্ডেজ|রক্ত\s*পড়ছে|রক্ত\s*বের\s*হচ্ছে)',
    r'\b(nosebleed|nose\s*bleeding|lean\s*forward)\b|(নাক\s*দিয়ে\s*রক্ত|নাক\s*থেকে\s*রক্ত)',
    r'\b(anaphylaxis|antihistamine|rhinitis|hay\s*fever|sneezes|runny\s*nose)\b|(অ্যানাফিল্যাক্সিস|অ্যালার্জি|হাঁচি)',
    r'\b(asthma|inhaler|reliever|puffs)\b|(হাঁপানি|ইনহেলার)',
    r'\b(baccha.*(jor|fever)|temperature.*children)\b|(বাচ্চা.*জ্বর|শিশুর\s*জ্বর)',
    r'\b(paracetamol|tension\s*headache|migraine)\b|(প্যারাসিটামল|মাইগ্রেন)',
    r'\b(meningitis|stiff\s*neck|glass\s*tumbler|sepsis|stroke|FAST\s*test)\b|(মেনিনজাইটিস|সেপসিস|স্ট্রোক)',
    r'\b(diarrhoea|vomiting|dehydration|ORS|fluids|oral\s*rehydration)\b|(ডায়রিয়া|ডায়রিয়া|বমি|পানিশূন্যতা|ওরস্যালাইন|স্যালাইন)',
]

# Underspecified / Vague symptom patterns (Mentions vague pain without adequate detail or in non-corpus anatomical sites)
UNDERSPECIFIED_PATTERNS = [
    # Banglish anatomical pain
    (r'(amar\s+)?(paye|pa|haat|hate|hatute|wrist|gora|komor|komore|pith|pithe|pet|pete|angul|angule|body|gaye|matha|mathaye|chokh|chokhe|buk|buke)\s+(betha|khapani|kosto|koshto|problem|shomossha|chap|oshosti|oshosthi|discomfort)', "Underspecified Localized Pain"),
    (r'(amar\s+)?(paye|pa|haat|hate|hatute|komor|komore|pith|pithe|pet|pete|angul|angule|body|gaye|matha|mathaye|buk|buke).*(betha|kosto|koshto|chap|oshosti|oshosthi|discomfort)\s*(korche|lagche|hocche)?', "Underspecified Localized Pain"),
    
    # English anatomical pain
    (r'(i\s+have\s+)?(pain\s+in\s+my\s+|my\s+)?(leg|arm|foot|feet|hand|back|finger|waist|knee|wrist|shoulder|head|eye|chest|body)\s+(hurts|is\s+hurting|pain|aching|ache|discomfort)', "Underspecified Body Ache"),
    (r'i\s+have\s+pain\s+in\s+my\s+(leg|arm|foot|feet|hand|back|finger|waist|knee|wrist|shoulder|head|eye|chest|body)', "Underspecified Body Ache"),
    
    # Native Bangla anatomical pain
    (r'(আমার\s+)?(পায়ে|পা|পায়ের|হাতে|হাত|হাতের|হাঁটুতে|হাঁটু|পায়ের\s*পাতায়|কোমরে|কোমর|পিঠে|পিঠ|পেটে|পেট|বুকে|বুক|মাথায়|মাথা|শরীরে|শরীর).*(ব্যথা|ব্যাথা|যন্ত্রণা|কষ্ট|সমস্যা|অস্বস্তি|চাপ)', "Underspecified Localized Pain"),
    (r'(হাতে|পায়ে|বুকে|মাথায়|শরীরে)\s*(ব্যথা|ব্যাথা|অস্বস্তি)\s*(পাচ্ছি|করছে|হচ্ছে|লাগছে)', "Underspecified Localized Pain"),

    # Vague general malaise
    (r'(amar\s+)?(kharap\s*lagche|osustho\s*lagche|valona|valo\s*lagche\s*na|oshanti\s*lagche|feeling\s*sick|unwell|not\s*feeling\s*well|shorir\s*kemon|kemon\s*lagche)', "General Vague Malaise"),
]

# ---------------------------------------------------------------------------
# 2. Language Detection
# ---------------------------------------------------------------------------
def detect_query_language(text: str) -> str:
    """Detect whether text is native Bangla script, English, or Romanized Banglish."""
    if not text or not text.strip():
        return "en"
    # Bangla Unicode block: \u0980-\u09FF
    bangla_chars = len(re.findall(r'[\u0980-\u09FF]', text))
    total_alpha = len(re.findall(r'[a-zA-Z\u0980-\u09FF]', text))
    if total_alpha == 0:
        return "en"
    if bangla_chars / total_alpha >= 0.40:
        return "bn"
    
    # Check for common Banglish markers
    banglish_markers = [
        r'\b(amar|tumi|apni|korbo|lagche|hocche|kivabe|kotokhon|oshudh|khabo|pani|rokt|betha|shash|matha|baccha|jor|poka|buk|haat|pa|paye)\b'
    ]
    t_lower = text.lower()
    for m in banglish_markers:
        if re.search(m, t_lower):
            return "banglish"
            
    return "en"

def resolve_output_language(detected_lang: str, preferred_lang: Optional[str] = "auto") -> str:
    """
    Resolve target response language:
    - If preferred_lang is 'bn', returns 'bn'
    - If preferred_lang is 'en', returns 'en'
    - If preferred_lang is 'auto':
        - English -> 'en'
        - Native Bangla -> 'bn'
        - Banglish -> 'bn' (default clinical presentation language)
    """
    if preferred_lang in ["bn", "bangla", "বাংলা"]:
        return "bn"
    if preferred_lang in ["en", "english"]:
        return "en"
    
    # Auto logic
    if detected_lang == "en":
        return "en"
    return "bn"

# ---------------------------------------------------------------------------
# 3. Query Understanding & Ambiguity Classifier
# ---------------------------------------------------------------------------
class QueryUnderstandingService:
    """
    Deterministic Query Understanding & Clarification Engine for Clinical Intelligence.
    """
    
    def analyze_query(
        self,
        query: str,
        preferred_language: str = "auto",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> QueryUnderstandingResult:
        q_clean = query.strip()
        q_lower = q_clean.lower()
        detected_lang = detect_query_language(q_clean)
        resolved_resp_lang = resolve_output_language(detected_lang, preferred_language)
        
        # 1. Check for Emergency Red Flags (Highest Priority)
        for pattern, red_flag_desc in EMERGENCY_RED_FLAG_PATTERNS:
            if re.search(pattern, q_lower, re.IGNORECASE) or re.search(pattern, q_clean, re.IGNORECASE):
                advice = EmergencyAdvice(
                    alert_title_en="CRITICAL: Emergency Medical Warning",
                    alert_title_bn="জরুরি সতর্কতা: অবিলম্বে জরুরি চিকিৎসা সহায়তা নিন",
                    action_advice_en=(
                        "Your query contains symptoms that may indicate a serious medical emergency "
                        f"({red_flag_desc}). Please call emergency services (999/112) or go to the nearest "
                        "Emergency Department / A&E immediately. Do not delay for online information."
                    ),
                    action_advice_bn=(
                        "আপনার উপসর্গে জরুরি চিকিৎসার লক্ষণ পাওয়া গেছে "
                        f"({red_flag_desc})। অনুগ্রহ করে অবিলম্বে জরুরি সেবা (৯৯৯) বা নিকটস্থ হাসপাতালের জরুরি বিভাগে যোগাযোগ করুন। "
                        "অনলাইনে উত্তরের অপেক্ষায় সময় নষ্ট করবেন না।"
                    )
                )
                return QueryUnderstandingResult(
                    query_raw=q_clean,
                    detected_language=detected_lang,
                    resolved_response_language=resolved_resp_lang,
                    intent_category=QueryIntentCategory.POTENTIALLY_EMERGENCY,
                    sufficiency_state=EvidenceSufficiencyState.EMERGENCY,
                    extracted_symptoms=[red_flag_desc],
                    red_flags_detected=[red_flag_desc],
                    is_emergency=True,
                    emergency_advice=advice,
                    evidence_presentation_policy="SHOW_EMERGENCY_OVERRIDE",
                    explanation=f"Emergency red-flag detected: {red_flag_desc}. Immediate safety routing triggered."
                )
        
        # 2. Check for Specific Out-of-Corpus Conditions
        for pattern, cond_name in UNSUPPORTED_CONDITION_PATTERNS:
            if re.search(pattern, q_lower, re.IGNORECASE) or re.search(pattern, q_clean, re.IGNORECASE):
                clarification = ClarificationQuestion(
                    field_to_clarify="out_of_scope_condition",
                    question_text_en=(
                        f"This query appears to relate to '{cond_name}', which is not currently covered in our 14 NHS first-aid topics. "
                        "Please consult a qualified healthcare professional or visit the official NHS website for this condition."
                    ),
                    question_text_bn=(
                        f"এই প্রশ্নটি '{cond_name}' সম্পর্কিত, যা বর্তমানে আমাদের ১৪টি এনএইচএস প্রাথমিক চিকিৎসা বিষয়ের অন্তর্ভুক্ত নয়। "
                        "এই বিষয়ের জন্য অনুগ্রহ করে একজন রেজিস্টার্ড চিকিৎসকের পরামর্শ নিন অথবা অফিসিয়াল স্বাস্থ্য নির্দেশিকা দেখুন।"
                    ),
                    options=[
                        "View covered conditions",
                        "Ask another first-aid question"
                    ]
                )
                return QueryUnderstandingResult(
                    query_raw=q_clean,
                    detected_language=detected_lang,
                    resolved_response_language=resolved_resp_lang,
                    intent_category=QueryIntentCategory.UNSUPPORTED_ACTIVE_CORPUS,
                    sufficiency_state=EvidenceSufficiencyState.UNSUPPORTED,
                    extracted_symptoms=[cond_name],
                    is_emergency=False,
                    clarification_question=clarification,
                    evidence_presentation_policy="SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION",
                    explanation=f"Query explicitly asks about '{cond_name}', which is outside the 14 active NHS conditions."
                )

        # 3. Check for specific first-aid topics (Unambiguous / Clearly answerable)
        is_specific_first_aid = False
        for pattern in SPECIFIC_IN_CORPUS_PATTERNS:
            if re.search(pattern, q_lower, re.IGNORECASE) or re.search(pattern, q_clean, re.IGNORECASE):
                is_specific_first_aid = True
                break

        # 4. Check for Underspecified / Vague Queries (e.g., 'amar paye betha')
        if not is_specific_first_aid:
            for pattern, vague_desc in UNDERSPECIFIED_PATTERNS:
                if re.search(pattern, q_lower, re.IGNORECASE) or re.search(pattern, q_clean, re.IGNORECASE):
                    # Determine body part or symptom
                    body_part = "body"
                    if re.search(r'(paye|pa|leg|foot|feet|calf|knee|hatute|পা|পায়ে|পায়ের|হাঁটু|হাঁটুতে|পায়ের\s*পাতায়)', q_lower) or any(w in q_clean for w in ["পা", "পায়ে", "পায়ের", "হাঁটু", "হাঁটুতে"]):
                        body_part = "leg/foot"
                    elif re.search(r'(haat|hate|arm|hand|wrist|হাতে|হাত|হাতের)', q_lower) or any(w in q_clean for w in ["হাত", "হাতে", "হাতের"]):
                        body_part = "arm/hand"
                    elif re.search(r'(komor|komore|back|waist|কোমর|কোমরে|পিঠ|পিঠে)', q_lower) or any(w in q_clean for w in ["কোমর", "কোমরে", "পিঠ", "পিঠে"]):
                        body_part = "back/waist"
                    elif re.search(r'(pet|pete|stomach|পেট|পেটে)', q_lower) or any(w in q_clean for w in ["পেট", "পেটে"]):
                        body_part = "abdomen/stomach"
                    elif re.search(r'(matha|head|মাথা|মাথায়)', q_lower) or any(w in q_clean for w in ["মাথা", "মাথায়"]):
                        body_part = "head"
                    elif re.search(r'(buk|chest|বুক|বুকে)', q_lower) or any(w in q_clean for w in ["বুক", "বুকে"]):
                        body_part = "chest"

                    if body_part == "head":
                        q_text_en = (
                            "To provide relevant information for head pain, could you specify the type? "
                            "Is it a throbbing pain on one side (migraine), tension across the forehead, or from a recent injury?"
                        )
                        q_text_bn = (
                            "মাথাব্যথার সঠিক তথ্যের জন্য অনুগ্রহ করে বিস্তারিত জানান: "
                            "এটি কি একপাশের তীব্র দপদপ করা ব্যথা (মাইগ্রেন), সাধারণ চাপযুক্ত মাথাব্যথা, নাকি মাথায় আঘাতের কারণে?"
                        )
                        opts = [
                            "একপাশে তীব্র ব্যথা (Migraine)" if resolved_resp_lang == "bn" else "Throbbing on one side (Migraine)",
                            "সাধারণ চাপযুক্ত ব্যথা (Tension headache)" if resolved_resp_lang == "bn" else "Tension headache",
                            "মাথায় আঘাত (Head injury)" if resolved_resp_lang == "bn" else "Head injury"
                        ]
                    elif body_part == "chest":
                        q_text_en = (
                            "To provide relevant information for chest discomfort, could you specify what you are feeling? "
                            "Is it a mild burning/acid sensation after eating, or any breathing difficulty?"
                        )
                        q_text_bn = (
                            "বুকের অস্বস্তির সঠিক তথ্যের জন্য অনুগ্রহ করে বিস্তারিত জানান: "
                            "এটি কি খাওয়ার পর মৃদু বুকজ্বালা বা এসিডিটি, নাকি কোনো শ্বাসকষ্ট হচ্ছে?"
                        )
                        opts = [
                            "খাওয়ার পর বুকজ্বালা (Heartburn/Reflux)" if resolved_resp_lang == "bn" else "Heartburn / Acid reflux",
                            "হালকা চাপ কিন্তু শ্বাসকষ্ট নেই (Mild pressure, no dyspnea)" if resolved_resp_lang == "bn" else "Mild pressure, no dyspnea",
                            "অন্যান্য সাধারণ অস্বস্তি (General discomfort)" if resolved_resp_lang == "bn" else "General discomfort"
                        ]
                    else:
                        q_text_en = (
                            f"To provide relevant first aid information for {body_part} pain, could you please specify what happened? "
                            "For example: Is there swelling or a sprain from an injury, a cut or wound, a burn, or a rash?"
                        )
                        q_text_bn = (
                            f"{body_part} ব্যথার সঠিক প্রাথমিক তথ্যের জন্য অনুগ্রহ করে বিস্তারিত জানান: "
                            "এটি কি মচকে যাওয়া বা আঘাতের ব্যথা, কেটে যাওয়া বা রক্তপাত, পুড়ে যাওয়া, নাকি কোনো ফোলা বা পোকার কামড়?"
                        )
                        opts = [
                            "আঘাত বা মচকে গেছে (Sprain/Injury)" if resolved_resp_lang == "bn" else "Sprain or injury",
                            "কেটে গেছে বা রক্তপাত (Cut/Bleeding)" if resolved_resp_lang == "bn" else "Cut or bleeding",
                            "পুড়ে গেছে (Burn/Scald)" if resolved_resp_lang == "bn" else "Burn or scald",
                            "অন্যান্য বা সাধারণ ব্যথা (Other/General)" if resolved_resp_lang == "bn" else "Other / General ache"
                        ]

                    clarification = ClarificationQuestion(
                        field_to_clarify="symptom_detail",
                        question_text_en=q_text_en,
                        question_text_bn=q_text_bn,
                        options=opts
                    )
                    return QueryUnderstandingResult(
                        query_raw=q_clean,
                        detected_language=detected_lang,
                        resolved_response_language=resolved_resp_lang,
                        intent_category=QueryIntentCategory.UNDERSPECIFIED_AMBIGUOUS,
                        sufficiency_state=EvidenceSufficiencyState.INSUFFICIENT,
                        extracted_symptoms=["pain"],
                        extracted_body_location=body_part,
                        is_emergency=False,
                        clarification_question=clarification,
                        evidence_presentation_policy="SUPPRESS_UNRELATED_CARDS_SHOW_ABSTENTION",
                        explanation=f"Query is underspecified for '{body_part} pain' without injury or context details. Clarification question generated."
                    )

        # 5. Clearly Answerable / Potentially Supported Queries
        return QueryUnderstandingResult(
            query_raw=q_clean,
            detected_language=detected_lang,
            resolved_response_language=resolved_resp_lang,
            intent_category=QueryIntentCategory.CLEARLY_ANSWERABLE,
            sufficiency_state=EvidenceSufficiencyState.SUFFICIENT,
            is_emergency=False,
            evidence_presentation_policy="SHOW_GROUNDING_CARDS",
            explanation="Query contains specific clinical keywords suitable for active NHS corpus retrieval."
        )

# Singleton instance
_query_understanding_instance: Optional[QueryUnderstandingService] = None

def get_query_understanding_service() -> QueryUnderstandingService:
    global _query_understanding_instance
    if _query_understanding_instance is None:
        _query_understanding_instance = QueryUnderstandingService()
    return _query_understanding_instance
