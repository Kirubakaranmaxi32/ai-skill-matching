"""
AI Skill Matching - Skill Extraction Architecture
=================================================
Provides data structures, interfaces, and extraction strategies for identifying
technical skills mentioned in project descriptions and aligning them with the
master taxonomy.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
import re


@dataclass
class CandidateSkill:
    """
    Represents an extracted skill candidate prior to or after normalization.
    """
    raw_term: str
    normalized_name: str
    confidence: float
    source: str  # e.g., 'taxonomy_exact', 'taxonomy_alias', 'contextual_keyword'
    matched_skill_id: Optional[str] = None
    category: Optional[str] = None


class BaseSkillExtractor:
    """
    Base class / interface for skill extraction strategies.
    Future implementations can include spaCy NER, KeyBERT, or LLM-assisted zero-shot extraction.
    """

    def extract_skills(
        self,
        text: str,
        taxonomy: List[Dict[str, Any]]
    ) -> List[CandidateSkill]:
        """
        Extract candidate skills from text and map to existing taxonomy.
        """
        raise NotImplementedError


class TaxonomyMatchSkillExtractor(BaseSkillExtractor):
    """
    Rule-guided taxonomy skill extractor.
    Identifies technical skills from normalized project text by matching
    against the master taxonomy and known aliases without inventing fake skills.
    
    Guarantees:
    - Never fabricates skill IDs.
    - Only associates candidate skills with existing taxonomy items when a clear match exists.
    - Preserves confidence score indicating match fidelity.
    """

    # Common technical term aliases for taxonomy matching
    KNOWN_ALIASES: Dict[str, str] = {
        "python3": "Python",
        "python 3": "Python",
        "python programming": "Python",
        "py": "Python",
        "pytorch deep learning": "PyTorch",
        "torch": "PyTorch",
        "tensorflow 2": "TensorFlow",
        "tf": "TensorFlow",
        "react.js": "React",
        "reactjs": "React",
        "react framework": "React",
        "ts": "TypeScript",
        "typescript language": "TypeScript",
        "fast api": "FastAPI",
        "fastapi framework": "FastAPI",
        "postgres": "PostgreSQL",
        "postgres sql": "PostgreSQL",
        "postgresql database": "PostgreSQL",
        "docker containers": "Docker",
        "containerization with docker": "Docker",
    }

    def extract_skills(
        self,
        text: str,
        taxonomy: List[Dict[str, Any]]
    ) -> List[CandidateSkill]:
        if not text or not text.strip() or not taxonomy:
            return []

        lower_text = text.lower()
        extracted: List[CandidateSkill] = []
        matched_skill_ids: Set[str] = set()

        # 1. Exact & Word-Boundary match against taxonomy names
        for item in taxonomy:
            skill_id = str(item.get("id"))
            skill_name = str(item.get("name", "")).strip()
            if not skill_name:
                continue

            category = item.get("category", "general")
            # Word boundary regex matching (handling special characters like C++, .NET)
            escaped_name = re.escape(skill_name.lower())
            pattern = rf"(?<!\w){escaped_name}(?!\w)"

            if re.search(pattern, lower_text):
                if skill_id not in matched_skill_ids:
                    matched_skill_ids.add(skill_id)
                    extracted.append(
                        CandidateSkill(
                            raw_term=skill_name,
                            normalized_name=skill_name,
                            confidence=0.95,
                            source="taxonomy_exact",
                            matched_skill_id=skill_id,
                            category=category,
                        )
                    )

        # 2. Alias matching
        for alias, canonical_name in self.KNOWN_ALIASES.items():
            escaped_alias = re.escape(alias.lower())
            pattern = rf"(?<!\w){escaped_alias}(?!\w)"
            if re.search(pattern, lower_text):
                # Find taxonomy entry for canonical name
                tax_item = next(
                    (t for t in taxonomy if str(t.get("name", "")).lower() == canonical_name.lower()),
                    None
                )
                if tax_item:
                    skill_id = str(tax_item.get("id"))
                    if skill_id not in matched_skill_ids:
                        matched_skill_ids.add(skill_id)
                        extracted.append(
                            CandidateSkill(
                                raw_term=alias,
                                normalized_name=canonical_name,
                                confidence=0.85,
                                source="taxonomy_alias",
                                matched_skill_id=skill_id,
                                category=tax_item.get("category", "general"),
                            )
                        )

        # 3. Detect known technical domain skills not yet in taxonomy (unmatched candidates)
        KNOWN_TECHNICAL_TERMS = [
            "Kubernetes", "GraphQL", "ROS2", "Redis", "MongoDB", "AWS",
            "Flutter", "OpenCV", "Kafka", "Next.js", "C++", "C#", ".NET"
        ]
        already_normalized = {s.normalized_name.lower() for s in extracted}

        for term in KNOWN_TECHNICAL_TERMS:
            if term.lower() in already_normalized:
                continue
            escaped_term = re.escape(term.lower())
            pattern = rf"(?<!\w){escaped_term}(?!\w)"
            if re.search(pattern, lower_text):
                # Check if taxonomy has it
                tax_item = next(
                    (t for t in taxonomy if str(t.get("name", "")).lower() == term.lower()),
                    None
                )
                if tax_item:
                    skill_id = str(tax_item.get("id"))
                    if skill_id not in matched_skill_ids:
                        matched_skill_ids.add(skill_id)
                        extracted.append(
                            CandidateSkill(
                                raw_term=term,
                                normalized_name=tax_item.get("name", term),
                                confidence=0.90,
                                source="taxonomy_exact",
                                matched_skill_id=skill_id,
                                category=tax_item.get("category", "general"),
                            )
                        )
                else:
                    # Unmatched candidate: detected in text but not present in current taxonomy
                    extracted.append(
                        CandidateSkill(
                            raw_term=term,
                            normalized_name=term,
                            confidence=0.70,
                            source="unmatched_candidate",
                            matched_skill_id=None,
                            category="unmatched",
                        )
                    )
                already_normalized.add(term.lower())

        # Sort descending by confidence then name
        extracted.sort(key=lambda s: (-s.confidence, s.normalized_name))
        return extracted
