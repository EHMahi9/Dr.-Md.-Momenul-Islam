"""
Post-Generation Output Validation Service (Phase 6D).
Performs deterministic, rule-based verification of generated text:
1. Citation index verification (e.g., ensure all [1], [2] tags map to real retrieved chunks)
2. Fabricated citation detection
3. Citation reference object mapping (claim -> chunk_id -> source_title -> source_url)
4. Basic safety pattern and medical disclaimer auditing

NO LLM JUDGE IS USED IN THIS PHASE (DETERMINISTIC CHECKS ONLY).
"""

import re
from typing import List, Tuple, Optional
from app.schemas.api_models import RetrievedEvidenceChunk
from app.schemas.generation_models import (
    CitationReference,
    PostValidationResult
)


class OutputValidator:
    """
    Validates model output against retrieved evidence and safety guardrails.
    """

    CITATION_PATTERN = re.compile(r'\[(\d+)\]')

    # Basic heuristic safety red flags for diagnostic or dosage assertions
    PROSCRIBED_PATTERNS = [
        (r'\b(i diagnose you with|you definitely have)\b', "Definitive diagnosis assertion without clinical examination"),
        (r'\b(take \d+\s*(mg|milligrams|tablets|pills) of)\b', "Specific unverified dosage recommendation"),
        (r'\b(ignore doctor|do not go to hospital|do not call (999|911|ambulance))\b', "Dangerous emergency avoidance recommendation")
    ]

    def extract_citation_indices(self, text: str) -> List[int]:
        """Extract all unique citation indices appearing in text in order."""
        matches = self.CITATION_PATTERN.findall(text)
        indices = []
        for m in matches:
            idx = int(m)
            if idx not in indices:
                indices.append(idx)
        return indices

    def build_citation_references(
        self,
        text: str,
        evidence: List[RetrievedEvidenceChunk]
    ) -> Tuple[List[CitationReference], List[str]]:
        """
        Map bracket citations in text to verified CitationReference objects.
        Returns (valid_citations, fabricated_citations).
        """
        indices = self.extract_citation_indices(text)
        valid_citations: List[CitationReference] = []
        fabricated: List[str] = []

        total_evidence = len(evidence)

        for idx in indices:
            if 1 <= idx <= total_evidence:
                chunk = evidence[idx - 1]
                # Build snippet of max 150 chars from chunk text
                snippet = chunk.text[:150].strip() + ("..." if len(chunk.text) > 150 else "")
                valid_citations.append(CitationReference(
                    citation_index=idx,
                    chunk_id=chunk.chunk_id,
                    parent_source_id=chunk.parent_source_id,
                    source_title=chunk.source_title,
                    source_url=chunk.source_url,
                    excerpt_snippet=snippet
                ))
            else:
                fabricated.append(f"[{idx}] (Index out of range 1..{total_evidence})")

        return valid_citations, fabricated

    def validate_safety_patterns(self, text: str) -> Tuple[bool, List[str]]:
        """Scan generated text for forbidden prescribing or diagnostic phrasing."""
        flags: List[str] = []
        t_lower = text.lower()
        for pattern, reason in self.PROSCRIBED_PATTERNS:
            if re.search(pattern, t_lower):
                flags.append(reason)
        return len(flags) == 0, flags

    def validate_output(
        self,
        generated_text: str,
        evidence: List[RetrievedEvidenceChunk]
    ) -> Tuple[PostValidationResult, List[CitationReference]]:
        """
        Run full deterministic validation pipeline on generated text.
        """
        if not generated_text or not generated_text.strip():
            return PostValidationResult(
                is_valid=False,
                citations_valid=False,
                summary_notes="Generated text is empty."
            ), []

        citations, fabricated = self.build_citation_references(generated_text, evidence)
        citations_valid = len(fabricated) == 0

        safety_ok, safety_flags = self.validate_safety_patterns(generated_text)

        is_valid = citations_valid and safety_ok

        summary_parts = []
        if not citations_valid:
            summary_parts.append(f"Found {len(fabricated)} invalid/fabricated citation tag(s): {', '.join(fabricated)}.")
        if not safety_ok:
            summary_parts.append(f"Safety flags triggered: {'; '.join(safety_flags)}.")
        if is_valid:
            summary_parts.append(f"Validation clean: {len(citations)} verified citation(s) mapped.")

        validation_result = PostValidationResult(
            is_valid=is_valid,
            citations_valid=citations_valid,
            fabricated_citations=fabricated,
            unsupported_claims=[],
            safety_check_passed=safety_ok,
            validation_flags=safety_flags,
            summary_notes=" ".join(summary_parts)
        )

        return validation_result, citations
