"""
Gate 5.24 — Step 1 & 2: Create and Lock New Development Benchmark (DEV-24)
Independently authored 40-query development set for reranker research across all 8 documents.
Zero overlap with 150 prior project queries.
"""

import json
import os
import sys
import hashlib
import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BENCHMARK_DIR = os.path.join(BASE_DIR, "benchmark")
DIAGNOSTICS_DIR = os.path.join(BASE_DIR, "diagnostics")
EXPERIMENTS_DIR = os.path.join(BASE_DIR, "experiments")
COMPARISONS_DIR = os.path.join(BASE_DIR, "comparisons")
CANDIDATE_DIR = os.path.join(BASE_DIR, "candidate")

os.makedirs(BENCHMARK_DIR, exist_ok=True)
os.makedirs(DIAGNOSTICS_DIR, exist_ok=True)
os.makedirs(EXPERIMENTS_DIR, exist_ok=True)
os.makedirs(COMPARISONS_DIR, exist_ok=True)
os.makedirs(CANDIDATE_DIR, exist_ok=True)

RESEARCH_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
CHUNKS_FILE = os.path.join(RESEARCH_DIR, "gate_5_9_optimization", "chunks", "hybrid_600", "provenance_manifest.json")
OLD_BM_FILE = os.path.join(RESEARCH_DIR, "gate_5_8_retrieval_validation", "benchmark", "frozen_benchmark.json")
FRESH_BM_FILE = os.path.join(RESEARCH_DIR, "gate_5_22_fresh_benchmark", "benchmark", "fresh_locked_benchmark.json")

# Load existing chunks
with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    corpus_chunks = json.load(f)
chunk_ids = {c["chunk_id"] for c in corpus_chunks}

# Load all 150 previous queries for anti-overlap verification
previous_queries = set()
with open(OLD_BM_FILE, "r", encoding="utf-8") as f:
    for q in json.load(f):
        previous_queries.add(q["query_text"].lower().strip())
with open(FRESH_BM_FILE, "r", encoding="utf-8") as f:
    for q in json.load(f)["queries"]:
        previous_queries.add(q["query_text"].lower().strip())

print(f"Loaded {len(previous_queries)} previously used queries to enforce strict zero-overlap.")

# 40 Independently-Authored Development Queries
queries = [
    # ── Group 1: Asthma (DOC-NHS-004) ──────────────────────────────────────────
    {
        "query_id": "DEV24-AST-01",
        "benchmark_split": "DEV_24",
        "query_text": "What questions will a doctor ask to diagnose asthma?",
        "language": "English",
        "expected_source_id": "DOC-NHS-004",
        "gold_chunk_ids": ["DOC-NHS-004-HYB-006"],
        "query_type": "Diagnosis_Procedure",
        "intent_category": "Professional_Referral",
        "target_topic": "How asthma is diagnosed by GP",
        "annotation_rationale": "HYB-006 specifically covers 'How asthma is diagnosed', describing what a GP or nurse will ask about symptoms and breathing tests."
    },
    {
        "query_id": "DEV24-AST-02",
        "benchmark_split": "DEV_24",
        "query_text": "What should you do if your reliever inhaler is not helping your symptoms?",
        "language": "English",
        "expected_source_id": "DOC-NHS-004",
        "gold_chunk_ids": ["DOC-NHS-004-HYB-005"],
        "query_type": "Urgent_Advice",
        "intent_category": "Professional_Referral",
        "target_topic": "Urgent GP appointment when reliever inhaler fails",
        "annotation_rationale": "HYB-005 provides 'Urgent advice: Ask for an urgent GP appointment if you have symptoms that are not relieved by your reliever inhaler'."
    },
    {
        "query_id": "DEV24-AST-03",
        "benchmark_split": "DEV_24",
        "query_text": "\u0985\u09cd\u09af\u09be\u099c\u09ae\u09be \u09a5\u09be\u0995\u09b2\u09c7 \u0995\u09cb\u09a8 \u0995\u09cb\u09a8 \u09ac\u09bf\u09b7\u09af\u09bc\u09c7 \u09b2\u09be\u0987\u09ab\u09b8\u09cd\u099f\u09be\u0987\u09b2 \u09aa\u09b0\u09bf\u09ac\u09b0\u09cd\u09a4\u09a8 \u0995\u09b0\u09be \u09a6\u09b0\u0995\u09be\u09b0?",
        "language": "Native_Bangla",
        "expected_source_id": "DOC-NHS-004",
        "gold_chunk_ids": ["DOC-NHS-004-HYB-012", "DOC-NHS-004-HYB-013"],
        "query_type": "Lifestyle_Management",
        "intent_category": "Prevention",
        "target_topic": "Healthy weight, routine vaccinations, and managing asthma",
        "annotation_rationale": "HYB-012 and HYB-013 discuss lifestyle factors: keeping healthy weight, getting vaccines, and practical lifestyle adjustments."
    },
    {
        "query_id": "DEV24-AST-04",
        "benchmark_split": "DEV_24",
        "query_text": "spacer device kivabe inhaler er shathe use korte hoy?",
        "language": "Standard_Banglish",
        "expected_source_id": "DOC-NHS-004",
        "gold_chunk_ids": ["DOC-NHS-004-HYB-009"],
        "query_type": "Technique_Instruction",
        "intent_category": "Procedural",
        "target_topic": "Inhaler and spacer device usage technique",
        "annotation_rationale": "HYB-009 explains 'Using your inhaler', spacer attachments, and getting inhaler technique checked at asthma reviews."
    },
    {
        "query_id": "DEV24-AST-05",
        "benchmark_split": "DEV_24",
        "query_text": "steroid tablet nile asthma te kon doctor dekhe?",
        "language": "Abbreviated_Banglish",
        "expected_source_id": "DOC-NHS-004",
        "gold_chunk_ids": ["DOC-NHS-004-HYB-011"],
        "query_type": "Specialist_Referral",
        "intent_category": "Professional_Referral",
        "target_topic": "Steroid tablets and specialist asthma clinic care",
        "annotation_rationale": "HYB-011 covers steroid tablets, injections, and specialist clinic referrals for advanced asthma treatment."
    },

    # ── Group 2: Burns & Scalds (DOC-NHS-005) ──────────────────────────────────
    {
        "query_id": "DEV24-BUR-01",
        "benchmark_split": "DEV_24",
        "query_text": "What kind of ointment or cream can be applied to a soothing minor burn?",
        "language": "English",
        "expected_source_id": "DOC-NHS-005",
        "gold_chunk_ids": ["DOC-NHS-005-HYB-004"],
        "query_type": "Medication_Topical",
        "intent_category": "Home_Treatment",
        "target_topic": "Emollient ointment and soothing creams for minor burns",
        "annotation_rationale": "HYB-004 explicitly advises: 'use an emollient ointment or aloe vera-based after sun spray to soothe the skin'."
    },
    {
        "query_id": "DEV24-BUR-02",
        "benchmark_split": "DEV_24",
        "query_text": "How long does a minor burn usually take to fully heal at home?",
        "language": "English",
        "expected_source_id": "DOC-NHS-005",
        "gold_chunk_ids": ["DOC-NHS-005-HYB-003"],
        "query_type": "Healing_Duration",
        "intent_category": "Duration",
        "target_topic": "Healing time for small burns (around 2 weeks)",
        "annotation_rationale": "HYB-003 states: 'Small burns and scalds can often be treated at home and can take around 2 weeks to heal'."
    },
    {
        "query_id": "DEV24-BUR-03",
        "benchmark_split": "DEV_24",
        "query_text": "\u09ae\u09c1\u0996 \u09ac\u09be \u09b8\u09cd\u09aa\u09b0\u09cd\u09b6\u0995\u09be\u09a4\u09b0 \u099c\u09be\u09af\u09bc\u0997\u09be\u09af\u09bc \u09aa\u09cb\u09a1\u09bc\u09be \u09b2\u09be\u0997\u09b2\u09c7 \u0995\u09bf \u09a6\u09cd\u09b0\u09c1\u09a4 \u09b9\u09be\u09b8\u09aa\u09be\u09a4\u09be\u09b2\u09c7 \u09af\u09c7\u09a4\u09c7 \u09b9\u09ac\u09c7?",
        "language": "Native_Bangla",
        "expected_source_id": "DOC-NHS-005",
        "gold_chunk_ids": ["DOC-NHS-005-HYB-002"],
        "query_type": "Location_Emergency",
        "intent_category": "Emergency_Escalation",
        "target_topic": "Burns on face, genitals, or sensitive areas -> A&E",
        "annotation_rationale": "HYB-002 specifies emergency criteria: 'Call 999 or go to A&E if: You have a burn or scald that: is on your face, genitals or bottom'."
    },
    {
        "query_id": "DEV24-BUR-04",
        "benchmark_split": "DEV_24",
        "query_text": "acid ba chemical diye hat purle first aid ki?",
        "language": "Standard_Banglish",
        "expected_source_id": "DOC-NHS-005",
        "gold_chunk_ids": ["DOC-NHS-005-HYB-001"],
        "query_type": "Chemical_First_Aid",
        "intent_category": "Procedural",
        "target_topic": "Acid and chemical burn initial instruction",
        "annotation_rationale": "HYB-001 specifically opens with guidance on acid and chemical burns alongside general first aid."
    },
    {
        "query_id": "DEV24-BUR-05",
        "benchmark_split": "DEV_24",
        "query_text": "pora jaygay borof lagale problem ki?",
        "language": "Abbreviated_Banglish",
        "expected_source_id": "DOC-NHS-005",
        "gold_chunk_ids": ["DOC-NHS-005-HYB-001"],
        "query_type": "Contraindication_Ice",
        "intent_category": "Contraindication",
        "target_topic": "Do not use ice or iced water on burns",
        "annotation_rationale": "HYB-001 includes explicit contraindication: 'do not use ice, iced water, or any creams or greasy substances like butter'."
    },

    # ── Group 3: Cuts & Grazes (DOC-NHS-006) ──────────────────────────────────
    {
        "query_id": "DEV24-CUT-01",
        "benchmark_split": "DEV_24",
        "query_text": "What steps should be taken if blood soaks through the first wound dressing?",
        "language": "English",
        "expected_source_id": "DOC-NHS-006",
        "gold_chunk_ids": ["DOC-NHS-006-HYB-002"],
        "query_type": "Severe_Bleeding_Step",
        "intent_category": "Procedural",
        "target_topic": "Applying second bandage if blood comes through",
        "annotation_rationale": "HYB-002 instructs: 'If blood comes through the bandage or cloth, apply another bandage or cloth on top to put pressure on the wound'."
    },
    {
        "query_id": "DEV24-CUT-02",
        "benchmark_split": "DEV_24",
        "query_text": "How should you clean your hands before touching an open graze?",
        "language": "English",
        "expected_source_id": "DOC-NHS-006",
        "gold_chunk_ids": ["DOC-NHS-006-HYB-001"],
        "query_type": "Hand_Hygiene_First_Aid",
        "intent_category": "Procedural",
        "target_topic": "Washing hands thoroughly and using disposable gloves",
        "annotation_rationale": "HYB-001 starts with: 'Wash your hands thoroughly and dry them. Put on disposable gloves if you have some'."
    },
    {
        "query_id": "DEV24-CUT-03",
        "benchmark_split": "DEV_24",
        "query_text": "\u0995\u09be\u099f\u09be \u0995\u09cd\u09b7\u09a4\u09c7\u09b0 \u09ac\u09cd\u09af\u09be\u09a8\u09cd\u09a1\u09c7\u099c \u0995\u09a4\u09a6\u09bf\u09a8 \u09aa\u09b0 \u09aa\u09b0 \u09aa\u09b0\u09bf\u09ac\u09b0\u09cd\u09a4\u09a8 \u0995\u09b0\u09be \u0989\u099a\u09bf\u09a4?",
        "language": "Native_Bangla",
        "expected_source_id": "DOC-NHS-006",
        "gold_chunk_ids": ["DOC-NHS-006-HYB-004"],
        "query_type": "Dressing_Maintenance",
        "intent_category": "Home_Treatment",
        "target_topic": "Changing dressing when wet/dirty and keeping dry",
        "annotation_rationale": "HYB-004 describes keeping the dressing clean and dry, using waterproof dressings, and changing whenever it gets wet or dirty."
    },
    {
        "query_id": "DEV24-CUT-04",
        "benchmark_split": "DEV_24",
        "query_text": "kete jawar por shorir kharap lagle ba fever ashle 111 call korbo?",
        "language": "Standard_Banglish",
        "expected_source_id": "DOC-NHS-006",
        "gold_chunk_ids": ["DOC-NHS-006-HYB-005"],
        "query_type": "Cut_Fever_Escalation",
        "intent_category": "Professional_Referral",
        "target_topic": "Cut with fever or generally unwell -> NHS 111",
        "annotation_rationale": "HYB-005 specifies: 'You can call 111 or get help from 111 online if: you've cut yourself and also feel generally unwell or have a high temperature'."
    },
    {
        "query_id": "DEV24-CUT-05",
        "benchmark_split": "DEV_24",
        "query_text": "wound e skin glue ba stitch lagbe kina kivabe jane?",
        "language": "Abbreviated_Banglish",
        "expected_source_id": "DOC-NHS-006",
        "gold_chunk_ids": ["DOC-NHS-006-HYB-006"],
        "query_type": "Clinical_Closure_Types",
        "intent_category": "Professional_Referral",
        "target_topic": "Stitches, skin glue, and sterile strips for wound closure",
        "annotation_rationale": "HYB-006 covers: 'The cut will be closed with stitches, skin glue or special sticky tape (steri-strips)'."
    },

    # ── Group 4: Dehydration (DOC-NHS-007) ────────────────────────────────────
    {
        "query_id": "DEV24-DEH-01",
        "benchmark_split": "DEV_24",
        "query_text": "What drink choices are best for preventing everyday dehydration?",
        "language": "English",
        "expected_source_id": "DOC-NHS-007",
        "gold_chunk_ids": ["DOC-NHS-007-HYB-006"],
        "query_type": "Fluid_Choices",
        "intent_category": "Prevention",
        "target_topic": "Water or diluted sugar-free squash to reduce risk",
        "annotation_rationale": "HYB-006 specifies: 'Drinking fluids regularly can reduce the risk of dehydration. Water or diluted sugar-free squash are good choices'."
    },
    {
        "query_id": "DEV24-DEH-02",
        "benchmark_split": "DEV_24",
        "query_text": "When is tiredness or dizziness from lack of fluids an urgent GP concern?",
        "language": "English",
        "expected_source_id": "DOC-NHS-007",
        "gold_chunk_ids": ["DOC-NHS-007-HYB-003"],
        "query_type": "Tiredness_GP_Escalation",
        "intent_category": "Professional_Referral",
        "target_topic": "Urgent GP if unusually tired or child seems drowsy",
        "annotation_rationale": "HYB-003 gives: 'Urgent advice: Ask for an urgent GP appointment or get help from NHS 111 if: you're feeling unusually tired (or your child seems drowsy)'."
    },
    {
        "query_id": "DEV24-DEH-03",
        "benchmark_split": "DEV_24",
        "query_text": "\u09ac\u09af\u09bc\u09b8\u09cd\u0995 \u09ae\u09be\u09a8\u09c1\u09b7 \u0995\u09ae \u09aa\u09be\u09a8\u09bf \u0996\u09c7\u09b2\u09c7 \u09a4\u09be\u09a6\u09c7\u09b0 \u0995\u09c0\u09ad\u09be\u09ac\u09c7 \u09ac\u09c7\u09b6\u09bf \u09a4\u09b0\u09b2 \u0996\u09be\u0993\u09af\u09bc\u09be\u09a8\u09cb \u09af\u09be\u09af\u09bc?",
        "language": "Native_Bangla",
        "expected_source_id": "DOC-NHS-007",
        "gold_chunk_ids": ["DOC-NHS-007-HYB-007"],
        "query_type": "Elderly_Support_Tips",
        "intent_category": "Home_Treatment",
        "target_topic": "Making drinking a social thing, mealtimes, high-water foods",
        "annotation_rationale": "HYB-007 details helping elderly people drink: mealtimes, social drinking, high water content foods like soup/jelly."
    },
    {
        "query_id": "DEV24-DEH-04",
        "benchmark_split": "DEV_24",
        "query_text": "dehydration hole nappy veja kome jay baby r ki lokkhon?",
        "language": "Standard_Banglish",
        "expected_source_id": "DOC-NHS-007",
        "gold_chunk_ids": ["DOC-NHS-007-HYB-001"],
        "query_type": "Infant_Symptom_Nappies",
        "intent_category": "Symptom",
        "target_topic": "Fewer wet nappies and sunken eyes in baby dehydration",
        "annotation_rationale": "HYB-001 lists infant symptoms: 'sunken eyes, few or no tears when they cry, fewer wet nappies than usual'."
    },
    {
        "query_id": "DEV24-DEH-05",
        "benchmark_split": "DEV_24",
        "query_text": "muk nil hoye gese dehydration e emergency ambulance daki?",
        "language": "Abbreviated_Banglish",
        "expected_source_id": "DOC-NHS-007",
        "gold_chunk_ids": ["DOC-NHS-007-HYB-004"],
        "query_type": "Cyanosis_Emergency",
        "intent_category": "Emergency_Escalation",
        "target_topic": "Blue/grey skin or lips with dehydration -> 999",
        "annotation_rationale": "HYB-004 states: 'Call 999 or go to A&E if: You or somebody else has signs of dehydration and: blue, grey, pale or blotchy skin, lips or tongue'."
    },

    # ── Group 5: Diarrhoea & Vomiting (DOC-NHS-008) ────────────────────────────
    {
        "query_id": "DEV24-DIA-01",
        "benchmark_split": "DEV_24",
        "query_text": "Why should you avoid using a public swimming pool after having diarrhoea?",
        "language": "English",
        "expected_source_id": "DOC-NHS-008",
        "gold_chunk_ids": ["DOC-NHS-008-HYB-003"],
        "query_type": "Pool_Hygiene_Restriction",
        "intent_category": "Prevention",
        "target_topic": "Do not use swimming pool until 48 hours after symptoms stop",
        "annotation_rationale": "HYB-003 states: 'do not use a swimming pool until at least 48 hours after the diarrhoea and vomiting have stopped'."
    },
    {
        "query_id": "DEV24-DIA-02",
        "benchmark_split": "DEV_24",
        "query_text": "What does vomit that looks like ground coffee indicate?",
        "language": "English",
        "expected_source_id": "DOC-NHS-008",
        "gold_chunk_ids": ["DOC-NHS-008-HYB-005"],
        "query_type": "Ground_Coffee_Vomit",
        "intent_category": "Emergency_Escalation",
        "target_topic": "Vomit that looks like ground coffee is an emergency",
        "annotation_rationale": "HYB-005 specifies: 'Call 999 or go to A&E if you or your child: vomit blood or have vomit that looks like ground coffee'."
    },
    {
        "query_id": "DEV24-DIA-03",
        "benchmark_split": "DEV_24",
        "query_text": "\u09a1\u09be\u09af\u09bc\u09b0\u09bf\u09af\u09bc\u09be\u09b0 \u09b8\u09ae\u09af\u09bc \u099b\u09cb\u099f \u099a\u09c1\u09ae\u09c1\u0995 \u09a6\u09bf\u09af\u09bc\u09c7 \u09a4\u09b0\u09b2 \u09aa\u09be\u09a8 \u0995\u09b0\u09be\u09b0 \u09a8\u09bf\u09af\u09bc\u09ae \u0995\u09c0?",
        "language": "Native_Bangla",
        "expected_source_id": "DOC-NHS-008",
        "gold_chunk_ids": ["DOC-NHS-008-HYB-001"],
        "query_type": "Fluid_Intake_Technique",
        "intent_category": "Home_Treatment",
        "target_topic": "Small sips of fluid if feeling sick",
        "annotation_rationale": "HYB-001 instructs: 'drink lots of fluids, such as water or squash – take small sips if you feel sick'."
    },
    {
        "query_id": "DEV24-DIA-04",
        "benchmark_split": "DEV_24",
        "query_text": "diarrhoea ar vomiting er main karon ki stomach bug naki food poisoning?",
        "language": "Standard_Banglish",
        "expected_source_id": "DOC-NHS-008",
        "gold_chunk_ids": ["DOC-NHS-008-HYB-007"],
        "query_type": "Causes_Inquiry",
        "intent_category": "Factoid",
        "target_topic": "Common causes: stomach bug, norovirus, food poisoning",
        "annotation_rationale": "HYB-007 lists: 'The most common causes of diarrhoea and vomiting are: a stomach bug, food poisoning'."
    },
    {
        "query_id": "DEV24-DIA-05",
        "benchmark_split": "DEV_24",
        "query_text": "12 masher bacha feeding bondho korle 111 call dibo?",
        "language": "Abbreviated_Banglish",
        "expected_source_id": "DOC-NHS-008",
        "gold_chunk_ids": ["DOC-NHS-008-HYB-004"],
        "query_type": "Baby_Feeding_Escalation",
        "intent_category": "Professional_Referral",
        "target_topic": "Baby under 12 months stops breast or bottle feeding -> 111",
        "annotation_rationale": "HYB-004 states: 'Call 111 now if: you're worried about a baby under 12 months, your child stops breast or bottle feeding'."
    },

    # ── Group 6: Headaches (DOC-NHS-009) ──────────────────────────────────────
    {
        "query_id": "DEV24-HEA-01",
        "benchmark_split": "DEV_24",
        "query_text": "Can poor posture or eyesight strain trigger frequent headaches?",
        "language": "English",
        "expected_source_id": "DOC-NHS-009",
        "gold_chunk_ids": ["DOC-NHS-009-HYB-004"],
        "query_type": "Headache_Triggers_Posture",
        "intent_category": "Factoid",
        "target_topic": "Causes of headaches: bad posture, eyesight problems",
        "annotation_rationale": "HYB-004 lists causes: 'having a cold or flu, stress, drinking too much alcohol, bad posture, eyesight problems'."
    },
    {
        "query_id": "DEV24-HEA-02",
        "benchmark_split": "DEV_24",
        "query_text": "What emergency symptoms with a headache indicate a stroke or seizure requiring 999?",
        "language": "English",
        "expected_source_id": "DOC-NHS-009",
        "gold_chunk_ids": ["DOC-NHS-009-HYB-003"],
        "query_type": "Neurological_Emergency",
        "intent_category": "Emergency_Escalation",
        "target_topic": "Seizure, numbness, weakness, stroke signs with headache -> 999",
        "annotation_rationale": "HYB-003 lists 999 criteria: 'has had a seizure (fit), has numbness or weakness in the body, speech problems'."
    },
    {
        "query_id": "DEV24-HEA-03",
        "benchmark_split": "DEV_24",
        "query_text": "\u09ae\u09be\u09a5\u09be\u09ac\u09cd\u09af\u09a5\u09be \u09a8\u09bf\u099c\u09c7 \u09a8\u09bf\u099c\u09c7 \u0989\u09aa\u09b6\u09ae\u09c7\u09b0 \u099c\u09a8\u09cd\u09af \u0995\u09a4\u09a6\u09bf\u09a8 \u0985\u09aa\u09c7\u0995\u09cd\u09b7\u09be \u0995\u09b0\u09be \u09af\u09be\u09af\u09bc?",
        "language": "Native_Bangla",
        "expected_source_id": "DOC-NHS-009",
        "gold_chunk_ids": ["DOC-NHS-009-HYB-000"],
        "query_type": "Natural_Resolution_Duration",
        "intent_category": "Duration",
        "target_topic": "Headaches lasting from 30 mins to several hours, going away on their own",
        "annotation_rationale": "HYB-000 states: 'Most headaches go away on their own... Headaches can last between 30 minutes and several hours'."
    },
    {
        "query_id": "DEV24-HEA-04",
        "benchmark_split": "DEV_24",
        "query_text": "regular headache thakle GP r kase checkup kobe lagbe?",
        "language": "Standard_Banglish",
        "expected_source_id": "DOC-NHS-009",
        "gold_chunk_ids": ["DOC-NHS-009-HYB-002"],
        "query_type": "Recurring_GP_Advice",
        "intent_category": "Professional_Referral",
        "target_topic": "Regular headaches or painkillers not helping -> GP appointment",
        "annotation_rationale": "HYB-002 specifies: 'Non-urgent advice: See a GP if: you regularly get headaches, painkillers do not help'."
    },
    {
        "query_id": "DEV24-HEA-05",
        "benchmark_split": "DEV_24",
        "query_text": "matha betha te paracetamol er shathe rest nile hobe?",
        "language": "Abbreviated_Banglish",
        "expected_source_id": "DOC-NHS-009",
        "gold_chunk_ids": ["DOC-NHS-009-HYB-000", "DOC-NHS-009-HYB-001"],
        "query_type": "Self_Care_Combinations",
        "intent_category": "Home_Treatment",
        "target_topic": "Drink plenty of water, get plenty of rest, take paracetamol",
        "annotation_rationale": "HYB-000 and HYB-001 describe self-care: resting, hydration, and taking paracetamol/ibuprofen."
    },

    # ── Group 7: Fever in Children (DOC-NHS-010) ──────────────────────────────
    {
        "query_id": "DEV24-FEV-01",
        "benchmark_split": "DEV_24",
        "query_text": "What should you do if a child with a fever is extremely sensitive to light?",
        "language": "English",
        "expected_source_id": "DOC-NHS-010",
        "gold_chunk_ids": ["DOC-NHS-010-HYB-005"],
        "query_type": "Photophobia_Fever",
        "intent_category": "Emergency_Escalation",
        "target_topic": "Child with fever bothered by light -> Emergency sign",
        "annotation_rationale": "HYB-005 explicitly lists emergency criteria: 'Call 999 if your child: is bothered by light'."
    },
    {
        "query_id": "DEV24-FEV-02",
        "benchmark_split": "DEV_24",
        "query_text": "What temperature in an infant aged 3 to 6 months requires calling 111?",
        "language": "English",
        "expected_source_id": "DOC-NHS-010",
        "gold_chunk_ids": ["DOC-NHS-010-HYB-004"],
        "query_type": "Infant_3_6mo_Threshold",
        "intent_category": "Factoid",
        "target_topic": "3 to 6 months old with 39C or higher -> Call 111",
        "annotation_rationale": "HYB-004 states: 'Call 111 if your child: is 3 to 6 months old and has a temperature of 39C or higher'."
    },
    {
        "query_id": "DEV24-FEV-03",
        "benchmark_split": "DEV_24",
        "query_text": "\u09ac\u09be\u099a\u09cd\u099a\u09be\u09b0 \u099c\u09cd\u09ac\u09b0 \u0995\u09a4 \u09a6\u09bf\u09a8 \u09b8\u09cd\u09a5\u09be\u09af\u09bc\u09c0 \u09b9\u09b2\u09c7 \u099a\u09bf\u0995\u09bf\u09ce\u09b8\u0995\u09c7\u09b0 \u09aa\u09b0\u09be\u09ae\u09b0\u09cd\u09b6 \u09a8\u09bf\u09a4\u09c7 \u09b9\u09ac\u09c7?",
        "language": "Native_Bangla",
        "expected_source_id": "DOC-NHS-010",
        "gold_chunk_ids": ["DOC-NHS-010-HYB-004"],
        "query_type": "Fever_Duration_5Days",
        "intent_category": "Professional_Referral",
        "target_topic": "Fever lasting 5 days or more -> Call 111",
        "annotation_rationale": "HYB-004 provides: 'Call 111 if your child: has a high temperature that's lasted for 5 days or more'."
    },
    {
        "query_id": "DEV24-FEV-04",
        "benchmark_split": "DEV_24",
        "query_text": "fever ashle baby ke breastfeed kora continue rakhbo?",
        "language": "Standard_Banglish",
        "expected_source_id": "DOC-NHS-010",
        "gold_chunk_ids": ["DOC-NHS-010-HYB-002"],
        "query_type": "Breastfeeding_During_Fever",
        "intent_category": "Home_Treatment",
        "target_topic": "Continue to breastfeed baby as normal during fever",
        "annotation_rationale": "HYB-002 specifies: 'Do: give them plenty of fluids – if your baby is breastfed, continue to breastfeed as normal'."
    },
    {
        "query_id": "DEV24-FEV-05",
        "benchmark_split": "DEV_24",
        "query_text": "bachar cold cough er jonno temp barta pare naki?",
        "language": "Abbreviated_Banglish",
        "expected_source_id": "DOC-NHS-010",
        "gold_chunk_ids": ["DOC-NHS-010-HYB-006"],
        "query_type": "Fever_Infection_Causes",
        "intent_category": "Factoid",
        "target_topic": "High temperature as natural response to coughs, colds, viral illnesses",
        "annotation_rationale": "HYB-006 explains: 'A high temperature is the body's natural response to fighting infections like coughs and colds'."
    },

    # ── Group 8: Anaphylaxis (DOC-NHS-011) ────────────────────────────────────
    {
        "query_id": "DEV24-ANA-01",
        "benchmark_split": "DEV_24",
        "query_text": "How should a pregnant woman be positioned during an anaphylactic reaction?",
        "language": "English",
        "expected_source_id": "DOC-NHS-011",
        "gold_chunk_ids": ["DOC-NHS-011-HYB-004"],
        "query_type": "Pregnancy_Positioning",
        "intent_category": "Procedural",
        "target_topic": "Lie on left side if pregnant during anaphylaxis",
        "annotation_rationale": "HYB-004 explicitly advises: 'Lie down... (if you're pregnant, lie on your left side)'."
    },
    {
        "query_id": "DEV24-ANA-02",
        "benchmark_split": "DEV_24",
        "query_text": "What is a trainer adrenaline auto-injector used for?",
        "language": "English",
        "expected_source_id": "DOC-NHS-011",
        "gold_chunk_ids": ["DOC-NHS-011-HYB-007"],
        "query_type": "Trainer_Device_Purpose",
        "intent_category": "Prevention",
        "target_topic": "Practising how to use injector with needleless trainer",
        "annotation_rationale": "HYB-007 explains: 'practise how to use your adrenaline auto-injector by using a trainer injector (an injector that has no needle or medicine in it)'."
    },
    {
        "query_id": "DEV24-ANA-03",
        "benchmark_split": "DEV_24",
        "query_text": "\u0985\u09cd\u09af\u09be\u09a8\u09be\u09ab\u09be\u0987\u09b2\u09cd\u09af\u09be\u0995\u09cd\u09b8\u09bf\u09b8 \u09b0\u09cb\u0997\u09c0\u09a6\u09c7\u09b0 \u0995\u09c7\u09a8 \u09a6\u09c1\u099f\u09bf \u0985\u099f\u09cb-\u0987\u09a8\u099c\u09c7\u0995\u09cd\u099f\u09b0 \u09b8\u09ac\u09b8\u09ae\u09af\u09bc \u09b8\u09be\u09a5\u09c7 \u09b0\u09be\u0996\u09a4\u09c7 \u09b9\u09af\u09bc?",
        "language": "Native_Bangla",
        "expected_source_id": "DOC-NHS-011",
        "gold_chunk_ids": ["DOC-NHS-011-HYB-006", "DOC-NHS-011-HYB-007"],
        "query_type": "Dual_Device_Prescription",
        "intent_category": "Prevention",
        "target_topic": "Given 2 auto-injectors before leaving hospital; carry 2 at all times",
        "annotation_rationale": "HYB-006 and HYB-007 cover being prescribed 2 auto-injectors and carrying both at all times in case of relapse/failure."
    },
    {
        "query_id": "DEV24-ANA-04",
        "benchmark_split": "DEV_24",
        "query_text": "EpiPen injection dewar por ambulance ke ki bolte hobe?",
        "language": "Standard_Banglish",
        "expected_source_id": "DOC-NHS-011",
        "gold_chunk_ids": ["DOC-NHS-011-HYB-004"],
        "query_type": "Ambulance_Communication",
        "intent_category": "Emergency_Escalation",
        "target_topic": "Call 999 for ambulance and say having anaphylactic reaction",
        "annotation_rationale": "HYB-004 states: 'Call 999 for an ambulance and say that you think you're having an anaphylactic reaction'."
    },
    {
        "query_id": "DEV24-ANA-05",
        "benchmark_split": "DEV_24",
        "query_text": "inhaler naki auto-injector allergy te first lagbe?",
        "language": "Abbreviated_Banglish",
        "expected_source_id": "DOC-NHS-011",
        "gold_chunk_ids": ["DOC-NHS-011-HYB-003", "DOC-NHS-011-HYB-004"],
        "query_type": "Auto_Injector_Priority",
        "intent_category": "Emergency_Escalation",
        "target_topic": "Use adrenaline auto-injector immediately if anaphylaxis",
        "annotation_rationale": "HYB-003 and HYB-004 emphasize using the adrenaline auto-injector immediately as first-line treatment for anaphylactic reactions."
    }
]

# Validation checks
assert len(queries) == 40, f"Expected 40 queries, got {len(queries)}"

# Check gold chunk IDs exist in corpus
for q in queries:
    for gc in q["gold_chunk_ids"]:
        assert gc in chunk_ids, f"Non-existent gold chunk {gc} in query {q['query_id']}"

# Check zero overlap with previous queries
overlaps = []
for q in queries:
    text = q["query_text"].lower().strip()
    if text in previous_queries:
        overlaps.append(q["query_id"])
assert len(overlaps) == 0, f"Overlapping queries found: {overlaps}"

# Check language counts
lang_counts = {}
for q in queries:
    l = q["language"]
    lang_counts[l] = lang_counts.get(l, 0) + 1
print(f"Language distribution: {lang_counts}")

# Check source counts
src_counts = {}
for q in queries:
    s = q["expected_source_id"]
    src_counts[s] = src_counts.get(s, 0) + 1
print(f"Source distribution: {src_counts}")

# Serialize benchmark
benchmark_data = {
    "gate": "GATE_5.24",
    "benchmark_name": "DEV_24_RERANKER_DEVELOPMENT_BENCHMARK",
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "total_queries": len(queries),
    "language_distribution": lang_counts,
    "source_distribution": src_counts,
    "purpose": "DEVELOPMENT_ONLY_FOR_RERANKER_EVIDENCE_SELECTION_RESEARCH",
    "queries": queries
}

benchmark_json = json.dumps(benchmark_data, indent=2, ensure_ascii=False)
benchmark_hash = hashlib.sha256(benchmark_json.encode('utf-8')).hexdigest()
benchmark_data["benchmark_sha256"] = benchmark_hash

target_bm_file = os.path.join(BENCHMARK_DIR, "dev24_benchmark.json")
with open(target_bm_file, "w", encoding="utf-8") as f:
    json.dump(benchmark_data, f, indent=2, ensure_ascii=False)

print(f"\n✓ DEV-24 Benchmark created and locked at: {target_bm_file}")
print(f"✓ SHA-256: {benchmark_hash}")
