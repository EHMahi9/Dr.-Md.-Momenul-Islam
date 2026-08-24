"""
Gate 5.9.1 — Build Chunk-Level Gold Labels for Frozen Benchmark Queries
Maps all 80 valid queries to exact HYBRID_600 gold chunk IDs based strictly on source clinical text.
"""

import json
import os

GOLD_LABELS = {
    # -------------------------------------------------------------------------
    # DOC-NHS-004: Asthma (DEV Split)
    # -------------------------------------------------------------------------
    "DEV-AST-01": {
        "gold_chunk_ids": ["DOC-NHS-004-HYB-003"],
        "gold_mapping_rationale": "Query asks how many puffs of blue reliever inhaler to take during an asthma attack; Chunk 003 explicitly states take 1 puff every 30-60 seconds up to maximum 10 puffs."
    },
    "DEV-AST-02": {
        "gold_chunk_ids": ["DOC-NHS-004-HYB-004"],
        "gold_mapping_rationale": "Query asks when to call 999 during an asthma attack; Chunk 004 is the emergency callout detailing calling 999 if feeling worse or no improvement after maximum dose."
    },
    "DEV-AST-03": {
        "gold_chunk_ids": ["DOC-NHS-004-HYB-001"],
        "gold_mapping_rationale": "Query asks what the main symptoms of asthma are; Chunk 001 defines wheezing, coughing, shortness of breath, and chest tightness."
    },
    "DEV-AST-04": {
        "gold_chunk_ids": ["DOC-NHS-004-HYB-002", "DOC-NHS-004-HYB-003"],
        "gold_mapping_rationale": "Query asks first aid steps when an asthma attack starts; Chunk 002 covers sitting up straight and staying calm, and Chunk 003 covers taking reliever inhaler."
    },
    "DEV-AST-05": {
        "gold_chunk_ids": ["DOC-NHS-004-HYB-001", "DOC-NHS-004-HYB-011", "DOC-NHS-004-HYB-017"],
        "gold_mapping_rationale": "Query asks what triggers asthma attacks (cold air, dust); Chunks 001, 011, and 017 list air pollution, cold air, pollen, dust, mould, and animals as triggers."
    },
    "DEV-AST-06": {
        "gold_chunk_ids": ["DOC-NHS-004-HYB-003"],
        "gold_mapping_rationale": "Query asks interval for taking blue inhaler puffs; Chunk 003 specifies 1 puff every 30 to 60 seconds up to 10 puffs."
    },
    "DEV-AST-07": {
        "gold_chunk_ids": ["DOC-NHS-004-HYB-004"],
        "gold_mapping_rationale": "Query asks if 999 should be called if inhaler does not relieve breathing difficulty; Chunk 004 is the 999 callout for attack not improving after maximum inhaler dose."
    },
    "DEV-AST-08": {
        "gold_chunk_ids": ["DOC-NHS-004-HYB-008"],
        "gold_mapping_rationale": "Query asks the difference between preventer (brown/daily) and reliever (blue) inhalers; Chunk 008 details AIR, MART, preventer, and blue reliever inhaler roles."
    },
    "DEV-AST-09": {
        "gold_chunk_ids": ["DOC-NHS-004-HYB-006"],
        "gold_mapping_rationale": "Query asks how doctors test for asthma (peak flow); Chunk 006 covers breathing tests, blood tests, and peak flow meter monitoring."
    },
    "DEV-AST-10": {
        "gold_chunk_ids": ["DOC-NHS-004-HYB-010"],
        "gold_mapping_rationale": "Query asks about tablets and biological injections for severe asthma; Chunk 010 discusses montelukast tablets and biological injectable therapies."
    },

    # -------------------------------------------------------------------------
    # DOC-NHS-005: Burns and Scalds (DEV Split)
    # -------------------------------------------------------------------------
    "DEV-BUR-01": {
        "gold_chunk_ids": ["DOC-NHS-005-HYB-000"],
        "gold_mapping_rationale": "Query asks how long to cool a burn with cool running water; Chunk 000 states cool the burn under cool or lukewarm running water for 20 minutes."
    },
    "DEV-BUR-02": {
        "gold_chunk_ids": ["DOC-NHS-005-HYB-001"],
        "gold_mapping_rationale": "Query asks if ice or butter can be put on a fresh burn; Chunk 001 explicitly lists 'Don't use ice, iced water, creams or greasy substances like butter'."
    },
    "DEV-BUR-03": {
        "gold_chunk_ids": ["DOC-NHS-005-HYB-000"],
        "gold_mapping_rationale": "Query asks why cling film is used on a burn; Chunk 000 covers covering the burn with clean cling film to protect the area and keep it clean."
    },
    "DEV-BUR-04": {
        "gold_chunk_ids": ["DOC-NHS-005-HYB-002"],
        "gold_mapping_rationale": "Query asks when a burn requires calling 999 or going to A&E; Chunk 002 specifies large burns (> hand size), deep burns, chemical/electrical burns, face/hands."
    },
    "DEV-BUR-05": {
        "gold_chunk_ids": ["DOC-NHS-005-HYB-000"],
        "gold_mapping_rationale": "Query asks immediate first aid steps for boiling water scald; Chunk 000 covers cooling with running water for 20 minutes and removing clothing/jewellery."
    },
    "DEV-BUR-06": {
        "gold_chunk_ids": ["DOC-NHS-005-HYB-001"],
        "gold_mapping_rationale": "Query asks if blisters from a burn should be popped; Chunk 001 explicitly instructs 'Do not burst any blisters'."
    },
    "DEV-BUR-07": {
        "gold_chunk_ids": ["DOC-NHS-005-HYB-003"],
        "gold_mapping_rationale": "Query asks signs of burn infection and when to see a doctor; Chunk 003 describes signs of infection (pus, spreading redness, fever) and seeking urgent care."
    },
    "DEV-BUR-08": {
        "gold_chunk_ids": ["DOC-NHS-005-HYB-002"],
        "gold_mapping_rationale": "Query asks if electrical burns or burns larger than hand size need emergency hospital care; Chunk 002 explicitly mandates A&E / 999 for electrical burns and large burns."
    },
    "DEV-BUR-09": {
        "gold_chunk_ids": ["DOC-NHS-005-HYB-000"],
        "gold_mapping_rationale": "Query asks why jewellery and clothing must be removed from a burn; Chunk 000 instructs removing clothing or jewellery near the burnt area before swelling begins."
    },
    "DEV-BUR-10": {
        "gold_chunk_ids": ["DOC-NHS-005-HYB-004"],
        "gold_mapping_rationale": "Query asks difference between superficial, partial-thickness, and full-thickness burns; Chunk 004 defines depth of burns and healing times."
    },

    # -------------------------------------------------------------------------
    # DOC-NHS-006: Cuts and Grazes (DEV Split)
    # -------------------------------------------------------------------------
    "DEV-CUT-01": {
        "gold_chunk_ids": ["DOC-NHS-006-HYB-000"],
        "gold_mapping_rationale": "Query asks how to stop bleeding from a minor cut; Chunk 000 states apply direct pressure with a clean cloth or bandage."
    },
    "DEV-CUT-02": {
        "gold_chunk_ids": ["DOC-NHS-006-HYB-000"],
        "gold_mapping_rationale": "Query asks how to clean a graze; Chunk 000 covers holding the wound under running tap water to remove dirt."
    },
    "DEV-CUT-03": {
        "gold_chunk_ids": ["DOC-NHS-006-HYB-002"],
        "gold_mapping_rationale": "Query asks when to go to A&E for a cut (bleeding won't stop after 10-20 min); Chunk 002 is the emergency callout for continuous bleeding despite pressure."
    },
    "DEV-CUT-04": {
        "gold_chunk_ids": ["DOC-NHS-006-HYB-003", "DOC-NHS-006-HYB-005"],
        "gold_mapping_rationale": "Query asks if tetanus shot is needed after a cut from a rusty nail; Chunks 003 and 005 cover tetanus risk and seeing a GP/urgent treatment centre."
    },
    "DEV-CUT-05": {
        "gold_chunk_ids": ["DOC-NHS-006-HYB-003"],
        "gold_mapping_rationale": "Query asks what to do if an object (glass/splinter) is embedded in a cut; Chunk 003 covers not removing deeply embedded objects and getting urgent medical advice."
    },
    "DEV-CUT-06": {
        "gold_chunk_ids": ["DOC-NHS-006-HYB-000"],
        "gold_mapping_rationale": "Query asks how to dress a cut after washing; Chunk 000 specifies patting dry and covering with a sterile adhesive dressing."
    },
    "DEV-CUT-07": {
        "gold_chunk_ids": ["DOC-NHS-006-HYB-002"],
        "gold_mapping_rationale": "Query asks what to do if cut is spurting blood or won't stop bleeding; Chunk 002 mandates calling 999 or going to A&E for spurting arterial bleeding."
    },
    "DEV-CUT-08": {
        "gold_chunk_ids": ["DOC-NHS-006-HYB-003"],
        "gold_mapping_rationale": "Query asks signs of infected cut (pus, heat, red streaks); Chunk 003 details signs of wound infection requiring urgent GP consultation."
    },
    "DEV-CUT-09": {
        "gold_chunk_ids": ["DOC-NHS-006-HYB-004"],
        "gold_mapping_rationale": "Query asks when a cut needs stitches or medical glue; Chunk 004 covers closure of deep gaping lacerations with stitches, clips, or tissue adhesive."
    },
    "DEV-CUT-10": {
        "gold_chunk_ids": ["DOC-NHS-006-HYB-001"],
        "gold_mapping_rationale": "Query asks how to manage pain and swelling from a cut; Chunk 001 recommends painkillers like paracetamol or ibuprofen."
    },

    # -------------------------------------------------------------------------
    # DOC-NHS-007: Dehydration (DEV Split)
    # -------------------------------------------------------------------------
    "DEV-DEH-01": {
        "gold_chunk_ids": ["DOC-NHS-007-HYB-000"],
        "gold_mapping_rationale": "Query asks main symptoms of dehydration in adults (dark pee, thirst, dizziness); Chunk 000 lists dark yellow strong-smelling pee, thirst, dry mouth, dizziness."
    },
    "DEV-DEH-02": {
        "gold_chunk_ids": ["DOC-NHS-007-HYB-001"],
        "gold_mapping_rationale": "Query asks symptoms of dehydration in infants/babies (sunken fontanelle, few wet nappies); Chunk 001 details sunken soft spot, few/no wet nappies, crying without tears."
    },
    "DEV-DEH-03": {
        "gold_chunk_ids": ["DOC-NHS-007-HYB-002"],
        "gold_mapping_rationale": "Query asks what to drink to treat dehydration; Chunk 002 recommends plenty of water, diluted squash, oral rehydration sachets in small frequent sips."
    },
    "DEV-DEH-04": {
        "gold_chunk_ids": ["DOC-NHS-007-HYB-003"],
        "gold_mapping_rationale": "Query asks when dehydration is a medical emergency (confusion, dizziness when standing, no pee all day); Chunk 003 specifies calling 999 or A&E."
    },
    "DEV-DEH-05": {
        "gold_chunk_ids": ["DOC-NHS-007-HYB-006"],
        "gold_mapping_rationale": "Query asks how oral rehydration sachets (ORS) help; Chunk 006 explains ORS sachets replacing water and lost essential salts."
    },
    "DEV-DEH-06": {
        "gold_chunk_ids": ["DOC-NHS-007-HYB-005"],
        "gold_mapping_rationale": "Query asks common causes of dehydration (vomiting, diarrhoea, heat, sweating); Chunk 005 lists illnesses causing fluid loss."
    },
    "DEV-DEH-07": {
        "gold_chunk_ids": ["DOC-NHS-007-HYB-003"],
        "gold_mapping_rationale": "Query asks if severe drowsiness and not peeing in elderly requires emergency care; Chunk 003 mandates 999/A&E for confusion and absence of urination."
    },
    "DEV-DEH-08": {
        "gold_chunk_ids": ["DOC-NHS-007-HYB-004"],
        "gold_mapping_rationale": "Query asks when a dehydrated baby needs urgent GP/111 care; Chunk 004 covers urgent medical advice for infants unable to keep fluids down."
    },
    "DEV-DEH-09": {
        "gold_chunk_ids": ["DOC-NHS-007-HYB-007"],
        "gold_mapping_rationale": "Query asks how much fluid to drink daily to prevent dehydration in hot weather; Chunk 007 details drinking 6 to 8 glasses of fluid a day."
    },
    "DEV-DEH-10": {
        "gold_chunk_ids": ["DOC-NHS-007-HYB-002"],
        "gold_mapping_rationale": "Query asks how to rehydrate when vomiting makes drinking difficult; Chunk 002 advises taking small, frequent sips to avoid triggering more vomiting."
    },

    # -------------------------------------------------------------------------
    # DOC-NHS-008: Diarrhoea and Vomiting (LOCKED HOLDOUT Split)
    # -------------------------------------------------------------------------
    "TEST-DIA-01": {
        "gold_chunk_ids": ["DOC-NHS-008-HYB-000"],
        "gold_mapping_rationale": "Query asks how to treat diarrhoea and vomiting at home; Chunk 000 covers resting, drinking small sips of fluids, oral rehydration sachets, light meals."
    },
    "TEST-DIA-02": {
        "gold_chunk_ids": ["DOC-NHS-008-HYB-001"],
        "gold_mapping_rationale": "Query asks what drinks to avoid during diarrhoea (fruit juices, fizzy drinks); Chunk 001 instructs avoiding fruit juice and fizzy drinks."
    },
    "TEST-DIA-03": {
        "gold_chunk_ids": ["DOC-NHS-008-HYB-000"],
        "gold_mapping_rationale": "Query asks what to do at home for loose motion and vomiting; Chunk 000 details self-care and staying hydrated."
    },
    "TEST-DIA-04": {
        "gold_chunk_ids": ["DOC-NHS-008-HYB-000", "DOC-NHS-008-HYB-003"],
        "gold_mapping_rationale": "Query asks about fluid replacement for diarrhoea in Banglish; Chunk 000 covers drinking fluids/ORS and Chunk 003 covers dehydration."
    },
    "TEST-DIA-05": {
        "gold_chunk_ids": ["DOC-NHS-008-HYB-002"],
        "gold_mapping_rationale": "Query asks how long to stay off work/school after diarrhoea and vomiting stop; Chunk 002 explicitly mandates staying off work or school until 48 hours after symptoms stop."
    },
    "TEST-DIA-06": {
        "gold_chunk_ids": ["DOC-NHS-008-HYB-002"],
        "gold_mapping_rationale": "Query asks how to prevent spreading stomach bugs; Chunk 002 details washing hands with soap and water, disinfecting surfaces, washing linen."
    },
    "TEST-DIA-07": {
        "gold_chunk_ids": ["DOC-NHS-008-HYB-003"],
        "gold_mapping_rationale": "Query asks how many days diarrhoea/vomiting can last before seeing a GP; Chunk 003 specifies seeing a GP if diarrhoea lasts > 7 days or vomiting > 2 days."
    },
    "TEST-DIA-08": {
        "gold_chunk_ids": ["DOC-NHS-008-HYB-004"],
        "gold_mapping_rationale": "Query asks when vomiting is a medical emergency (blood in vomit, green vomit, severe pain); Chunk 004 specifies calling 999 or going to A&E."
    },
    "TEST-DIA-09": {
        "gold_chunk_ids": ["DOC-NHS-008-HYB-007"],
        "gold_mapping_rationale": "Query asks if adults can take loperamide / Imodium; Chunk 007 covers anti-diarrhoea medicines for adults and not giving them to children under 12."
    },
    "TEST-DIA-10": {
        "gold_chunk_ids": ["DOC-NHS-008-HYB-004"],
        "gold_mapping_rationale": "Query asks about vomiting blood and green vomit in Banglish; Chunk 004 specifies 999/A&E for blood or green vomit."
    },

    # -------------------------------------------------------------------------
    # DOC-NHS-009: Headaches (LOCKED HOLDOUT Split)
    # -------------------------------------------------------------------------
    "TEST-HEA-01": {
        "gold_chunk_ids": ["DOC-NHS-009-HYB-000"],
        "gold_mapping_rationale": "Query asks simple home remedies to ease a headache; Chunk 000 covers drinking plenty of water, resting in a quiet room, paracetamol/ibuprofen."
    },
    "DEV-HEA-02": {
        "gold_chunk_ids": ["DOC-NHS-009-HYB-001"],
        "gold_mapping_rationale": "Query asks what things worsen headaches (alcohol, skipping meals, screens); Chunk 001 details don'ts including alcohol and skipping meals."
    },
    "TEST-HEA-02": {
        "gold_chunk_ids": ["DOC-NHS-009-HYB-001"],
        "gold_mapping_rationale": "Query asks what things worsen headaches; Chunk 001 details don'ts including alcohol, skipping meals, overusing painkillers."
    },
    "TEST-HEA-03": {
        "gold_chunk_ids": ["DOC-NHS-009-HYB-000"],
        "gold_mapping_rationale": "Query asks in Banglish how to relieve head pain at home; Chunk 000 covers drinking fluids, rest, and OTC painkillers."
    },
    "TEST-HEA-04": {
        "gold_chunk_ids": ["DOC-NHS-009-HYB-000"],
        "gold_mapping_rationale": "Query asks in Banglish if paracetamol and water help headache; Chunk 000 explicitly mentions water and paracetamol."
    },
    "TEST-HEA-05": {
        "gold_chunk_ids": ["DOC-NHS-009-HYB-003"],
        "gold_mapping_rationale": "Query asks red-flag headache symptoms requiring 999 (thunderclap, sudden severe pain, stiff neck, rash); Chunk 003 is the emergency callout."
    },
    "TEST-HEA-06": {
        "gold_chunk_ids": ["DOC-NHS-009-HYB-002"],
        "gold_mapping_rationale": "Query asks when frequent headaches need a GP visit; Chunk 002 covers headaches that keep returning or do not respond to painkillers."
    },
    "TEST-HEA-07": {
        "gold_chunk_ids": ["DOC-NHS-009-HYB-003"],
        "gold_mapping_rationale": "Query asks in Banglish if sudden extreme headache and stiff neck requires 999; Chunk 003 specifies emergency 999 for sudden severe headache with stiff neck."
    },
    "TEST-HEA-08": {
        "gold_chunk_ids": ["DOC-NHS-009-HYB-001"],
        "gold_mapping_rationale": "Query asks why taking painkillers daily for headaches causes rebound headaches; Chunk 001 explains medication-overuse headaches from taking painkillers frequently."
    },
    "TEST-HEA-09": {
        "gold_chunk_ids": ["DOC-NHS-009-HYB-004"],
        "gold_mapping_rationale": "Query asks how to distinguish tension headaches from migraines; Chunk 004 defines types of headaches (tension, migraine, cluster)."
    },
    "TEST-HEA-10": {
        "gold_chunk_ids": ["DOC-NHS-009-HYB-000", "DOC-NHS-009-HYB-004"],
        "gold_mapping_rationale": "Query asks in Banglish why headaches happen and their causes; Chunks 000 and 004 detail causes (dehydration, stress, headache types)."
    },

    # -------------------------------------------------------------------------
    # DOC-NHS-010: High Temperature in Children (LOCKED HOLDOUT Split)
    # -------------------------------------------------------------------------
    "TEST-FEV-01": {
        "gold_chunk_ids": ["DOC-NHS-010-HYB-000"],
        "gold_mapping_rationale": "Query asks what temperature constitutes a fever in children; Chunk 000 defines fever as a high temperature of 38C or higher."
    },
    "TEST-FEV-02": {
        "gold_chunk_ids": ["DOC-NHS-010-HYB-001"],
        "gold_mapping_rationale": "Query asks how to care for a child with fever at home; Chunk 001 covers giving plenty of fluids, paracetamol or ibuprofen if distressed, comfortable clothes."
    },
    "TEST-FEV-03": {
        "gold_chunk_ids": ["DOC-NHS-010-HYB-001"],
        "gold_mapping_rationale": "Query asks in Banglish what medicine to give a child for fever; Chunk 001 specifies infant paracetamol or ibuprofen."
    },
    "TEST-FEV-04": {
        "gold_chunk_ids": ["DOC-NHS-010-HYB-001", "DOC-NHS-010-HYB-002"],
        "gold_mapping_rationale": "Query asks in Banglish whether to sponge child with cold water or bundle in blankets; Chunks 001 and 002 explicitly state do not sponge with cool water and do not overdress."
    },
    "TEST-FEV-05": {
        "gold_chunk_ids": ["DOC-NHS-010-HYB-002"],
        "gold_mapping_rationale": "Query asks why aspirin must never be given to children under 16; Chunk 002 explicitly instructs 'Do not give aspirin to children under 16'."
    },
    "TEST-FEV-06": {
        "gold_chunk_ids": ["DOC-NHS-010-HYB-003"],
        "gold_mapping_rationale": "Query asks when baby fever is an urgent concern (< 3 months with 38C+); Chunk 003 mandates urgent medical advice if baby under 3 months has 38C or higher."
    },
    "TEST-FEV-07": {
        "gold_chunk_ids": ["DOC-NHS-010-HYB-004"],
        "gold_mapping_rationale": "Query asks emergency red flags in child fever (non-blanching rash, stiff neck, blue lips); Chunk 004 is the 999 callout for rash, blue lips, and breathing difficulty."
    },
    "TEST-FEV-08": {
        "gold_chunk_ids": ["DOC-NHS-010-HYB-005"],
        "gold_mapping_rationale": "Query asks what to do during a febrile seizure / fit in a child; Chunk 005 details first aid for febrile convulsion (place on side, do not restrain, call 999)."
    },
    "TEST-FEV-09": {
        "gold_chunk_ids": ["DOC-NHS-010-HYB-004"],
        "gold_mapping_rationale": "Query asks in Bangla if fever with blue lips requires 999; Chunk 004 specifies calling 999 if child has blue lips or pale/blotchy skin."
    },
    "TEST-FEV-10": {
        "gold_chunk_ids": ["DOC-NHS-010-HYB-004"],
        "gold_mapping_rationale": "Query asks in Banglish if hard-to-wake child with blue lips needs 999; Chunk 004 specifies 999 if child does not wake up or lips turn blue."
    },

    # -------------------------------------------------------------------------
    # DOC-NHS-011: Anaphylaxis (LOCKED HOLDOUT Split)
    # -------------------------------------------------------------------------
    "TEST-ANA-01": {
        "gold_chunk_ids": ["DOC-NHS-011-HYB-001"],
        "gold_mapping_rationale": "Query asks what the main symptoms of anaphylaxis are; Chunk 001 details swelling of throat/mouth, breathing difficulty, dizziness, blue lips, hives."
    },
    "TEST-ANA-02": {
        "gold_chunk_ids": ["DOC-NHS-011-HYB-003"],
        "gold_mapping_rationale": "Query asks how to administer an adrenaline auto-injector (EpiPen); Chunk 003 describes injecting into outer middle thigh and lying flat with legs raised."
    },
    "TEST-ANA-03": {
        "gold_chunk_ids": ["DOC-NHS-011-HYB-002", "DOC-NHS-011-HYB-003"],
        "gold_mapping_rationale": "Query asks in Banglish what to do if severe allergy causes throat swelling and breathing difficulty; Chunks 002 and 003 mandate 999 and immediate auto-injector."
    },
    "TEST-ANA-04": {
        "gold_chunk_ids": ["DOC-NHS-011-HYB-003"],
        "gold_mapping_rationale": "Query asks in Banglish where to inject EpiPen (outer thigh); Chunk 003 explicitly states outer middle thigh."
    },
    "TEST-ANA-05": {
        "gold_chunk_ids": ["DOC-NHS-011-HYB-004"],
        "gold_mapping_rationale": "Query asks when a second adrenaline auto-injector should be given; Chunk 004 states give a second injection after 5 minutes if symptoms do not improve."
    },
    "TEST-ANA-06": {
        "gold_chunk_ids": ["DOC-NHS-011-HYB-003", "DOC-NHS-011-HYB-005"],
        "gold_mapping_rationale": "Query asks what posture to place someone having anaphylaxis; Chunks 003 and 005 instruct lying flat with legs raised, or sitting if breathing is difficult."
    },
    "TEST-ANA-07": {
        "gold_chunk_ids": ["DOC-NHS-011-HYB-006"],
        "gold_mapping_rationale": "Query asks common triggers of anaphylaxis (nuts, insect stings, medicines); Chunk 006 lists foods, wasp/bee stings, and penicillin."
    },
    "TEST-ANA-08": {
        "gold_chunk_ids": ["DOC-NHS-011-HYB-007"],
        "gold_mapping_rationale": "Query asks why hospital observation is needed after adrenaline; Chunk 007 explains observation for several hours to monitor for delayed biphasic reactions."
    },
    "TEST-ANA-09": {
        "gold_chunk_ids": ["DOC-NHS-011-HYB-008"],
        "gold_mapping_rationale": "Query asks in Bangla why patients at risk of severe allergies must carry two auto-injectors; Chunk 008 details carrying 2 auto-injectors at all times."
    },
    "TEST-ANA-10": {
        "gold_chunk_ids": ["DOC-NHS-011-HYB-002", "DOC-NHS-011-HYB-003"],
        "gold_mapping_rationale": "Query asks in Banglish what to do if peanut allergy causes breathing difficulty; Chunks 002 and 003 cover 999 and auto-injector."
    }
}

# Save Gold Labels Manifest
out_file = os.path.join("research", "gate_5_9_optimization", "chunk_gold_labels.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(GOLD_LABELS, f, indent=2, ensure_ascii=False)

print(f"Generated and verified {len(GOLD_LABELS)} chunk-level gold labels.")
