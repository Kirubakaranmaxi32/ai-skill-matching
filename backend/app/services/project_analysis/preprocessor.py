"""
Text Preprocessing for Project Descriptions
===========================================
Prepares raw project descriptions for NLP embedding generation and skill extraction.
Preserves technical vocabulary, programming language nomenclature, and framework names.
"""

import re
import unicodedata
from typing import Optional


class TextPreprocessor:
    """
    Cleans and normalizes project description text for downstream NLP tasks.
    
    Principles:
    1. Robust to empty or non-string inputs.
    2. Normalizes excessive whitespace and formatting artifacts.
    3. Strips markdown ornamentation without losing enclosed technical tokens.
    4. Explicitly preserves technical symbols like C++, C#, .NET, Node.js, AI/ML, CI/CD.
    """

    # Markdown link pattern [text](url) -> text
    MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\([^\)]+\)")
    
    # Markdown headings, bold, italics, code delimiters
    MARKDOWN_DECORATION_PATTERN = re.compile(r"(\*{1,3}|_{1,3}|`{1,3}|~{1,2})")

    # Bullet markers at start of lines: *, -, +, bullet points
    BULLET_PATTERN = re.compile(r"(?m)^\s*[\*\-\+•]\s+")

    # Markdown headers #, ##, etc. at start of lines
    HEADER_PATTERN = re.compile(r"(?m)^\s*#{1,6}\s+")

    # Multiple whitespace/newlines
    WHITESPACE_PATTERN = re.compile(r"\s+")

    @classmethod
    def clean(cls, text: Optional[str]) -> str:
        """
        Full cleaning and normalization pipeline.
        Returns cleaned string suitable for Sentence Transformers or skill extraction.
        """
        if text is None:
            return ""

        if not isinstance(text, str):
            text = str(text)

        # 1. Normalize unicode (NFKC: normalizes compatibility characters while keeping symbols)
        cleaned = unicodedata.normalize("NFKC", text)

        # 2. Remove control characters (except standard newlines/tabs during initial pass)
        cleaned = "".join(
            ch for ch in cleaned
            if unicodedata.category(ch)[0] != "C" or ch in ("\n", "\r", "\t")
        )

        # 3. Strip markdown links [label](url) -> label
        cleaned = cls.MARKDOWN_LINK_PATTERN.sub(r"\1", cleaned)

        # 4. Remove bullet and header markers at line starts
        cleaned = cls.BULLET_PATTERN.sub("", cleaned)
        cleaned = cls.HEADER_PATTERN.sub("", cleaned)

        # 5. Remove markdown decoration formatting (*bold*, _italic_, `code`, etc.)
        # Note: Keeps words intact (e.g. `PyTorch` -> PyTorch, **React** -> React)
        cleaned = cls.MARKDOWN_DECORATION_PATTERN.sub("", cleaned)

        # 6. Normalize all consecutive whitespace, tabs, and newlines to a single space
        cleaned = cls.WHITESPACE_PATTERN.sub(" ", cleaned)

        return cleaned.strip()

    @classmethod
    def is_empty_or_trivial(cls, text: Optional[str], min_length: int = 5) -> bool:
        """
        Checks whether the text is empty, whitespace-only, or too short to analyze.
        """
        cleaned = cls.clean(text)
        return len(cleaned) < min_length
