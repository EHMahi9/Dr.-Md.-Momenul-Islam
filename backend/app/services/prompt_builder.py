"""
Grounded Prompt Builder Service (Phase 6D).
Constructs structured, tamper-resistant prompts that explicitly enforce:
1. Evidence-first factual grounding
2. No hallucinated medical claims or fabricated citations
3. Clear medical uncertainty boundaries
4. Emergency triage disclaimers
5. Explicit declaration of insufficient evidence
"""

from typing import List, Dict, Any, Optional
from app.schemas.api_models import RetrievedEvidenceChunk
from app.schemas.generation_models import (
    GroundingEvidence,
    GroundedPrompt
)

# Standard grounding system instructions
SYSTEM_GROUNDING_INSTRUCTIONS = """You are a clinical evidence synthesis assistant for Dr. Md. Momenul Islam health information platform.
Your role is to summarize authoritative clinical evidence retrieved from verified NHS sources for users in Bangladesh.

MANDATORY BEHAVIORAL PROTOCOLS:
1. EVIDENCE BOUNDARY: Use the provided retrieved NHS evidence excerpts as your EXCLUSIVE factual source.
2. NO MEDICAL HALLUCINATION: Never extrapolate, assume, or invent medical facts not explicitly stated in the evidence.
3. CITATION DISCIPLINE: Append citation tags like [1], [2] immediately following every claim directly supported by an evidence excerpt.
4. NO FABRICATED CITATIONS: Never cite a passage index or source that does not exist in the retrieved evidence section.
5. NO DOCTOR PERSONA: Do not pretend to be the user's personal physician, and never provide a definitive individual medical diagnosis.
6. NO DANGEROUS PRESCRIBING: Never recommend specific drug dosages, prescription medications, or unverified invasive home remedies.
7. INSUFFICIENT EVIDENCE: If the provided evidence does not fully answer the user's question, clearly state: "The retrieved NHS evidence does not contain sufficient details to answer this question."
8. UNCERTAINTY & LANGUAGE: If the query is ambiguous, explain what is known from the evidence and advise consulting a qualified healthcare professional."""

SAFETY_AND_TRIAGE_INSTRUCTIONS = """EMERGENCY TRIAGE RULES:
- If the query mentions red-flag emergency symptoms (such as severe chest pain radiating to arm/jaw, signs of stroke/FAST, severe anaphylaxis/breathing stoppage, meningitis rash that does not fade under glass, severe sepsis symptoms):
  * State the emergency triage advice FIRST (e.g. Call emergency services / 999 / go to nearest emergency hospital immediately).
  * Do not delay emergency guidance behind general background text.

GENERAL SAFETY NOTICE:
- All information provided is for educational and informational health guidance only, derived under Open Government Licence v3.0 from NHS England."""


class PromptBuilder:
    """
    Constructs structured GroundedPrompt objects from queries and evidence.
    """

    def __init__(
        self,
        system_instructions: str = SYSTEM_GROUNDING_INSTRUCTIONS,
        safety_instructions: str = SAFETY_AND_TRIAGE_INSTRUCTIONS
    ):
        self.system_instructions = system_instructions
        self.safety_instructions = safety_instructions

    def format_evidence_block(self, evidence: List[GroundingEvidence]) -> str:
        """
        Format retrieved evidence chunks into structured, numbered passages for model consumption.
        """
        if not evidence:
            return "[NO EVIDENCE PASSAGES RETRIEVED]"

        blocks = []
        for idx, item in enumerate(evidence, start=1):
            block = (
                f"--- EVIDENCE EXCERPT [{idx}] ---\n"
                f"Chunk ID: {item.chunk_id}\n"
                f"Source: {item.source_title} ({item.parent_source_id})\n"
                f"URL: {item.source_url}\n"
                f"Content:\n{item.excerpt.strip()}\n"
            )
            blocks.append(block)

        return "\n".join(blocks)

    def build_prompt(
        self,
        query: str,
        evidence: List[RetrievedEvidenceChunk],
        corpus_metadata: Optional[Dict[str, Any]] = None
    ) -> GroundedPrompt:
        """
        Compose the complete GroundedPrompt contract.
        """
        grounding_evidence = [
            GroundingEvidence.from_retrieved_chunk(c) for c in evidence
        ]

        meta = corpus_metadata or {
            "licence": "Open Government Licence v3.0",
            "provider": "NHS England",
            "active_conditions": 14,
            "evidence_count": len(evidence)
        }

        formatted_evidence = self.format_evidence_block(grounding_evidence)

        full_payload = (
            f"=== SYSTEM INSTRUCTIONS ===\n{self.system_instructions}\n\n"
            f"=== SAFETY & TRIAGE RULES ===\n{self.safety_instructions}\n\n"
            f"=== SOURCE METADATA ===\n"
            f"Corpus: Active NHS Knowledge Base ({meta.get('active_conditions', 14)} Conditions)\n"
            f"Licensing: {meta.get('licence')}\n\n"
            f"=== RETRIEVED CLINICAL EVIDENCE ===\n{formatted_evidence}\n\n"
            f"=== USER INQUIRY ===\n{query.strip()}\n\n"
            f"=== GROUNDED RESPONSE INSTRUCTIONS ===\n"
            f"Generate a clear, respectful summary answering the user inquiry based strictly on excerpts [1]..[{len(grounding_evidence)}]. "
            f"Use inline bracket citations like [1] for every factual statement."
        )

        return GroundedPrompt(
            user_question=query.strip(),
            retrieved_evidence=grounding_evidence,
            source_metadata=meta,
            system_instructions=self.system_instructions,
            safety_instructions=self.safety_instructions,
            formatted_prompt_payload=full_payload
        )
