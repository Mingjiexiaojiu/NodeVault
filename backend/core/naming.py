"""Name auto-generation utilities for Skill kebab-case names."""

import re
import unicodedata


def to_kebab_case(display_name: str) -> str:
    """Convert a display name to kebab-case.

    Chinese characters are converted to pinyin; other characters are lowercased
    and non-alphanumeric characters become hyphens. Consecutive hyphens are
    collapsed and leading/trailing hyphens are stripped.
    """
    try:
        from pypinyin import lazy_pinyin, Style
        parts: list[str] = []
        buf = ""
        for ch in display_name:
            if _is_cjk(ch):
                if buf:
                    parts.append(_ascii_to_kebab(buf))
                    buf = ""
                parts.extend(lazy_pinyin(ch, style=Style.NORMAL))
            else:
                buf += ch
        if buf:
            parts.append(_ascii_to_kebab(buf))
        raw = "-".join(p for p in parts if p)
    except ImportError:
        raw = _ascii_to_kebab(display_name)

    # Final cleanup
    raw = re.sub(r"-+", "-", raw).strip("-")
    return raw[:64] if raw else "skill"


def _is_cjk(ch: str) -> bool:
    """Return True if the character is a CJK Unified Ideograph."""
    try:
        return "CJK UNIFIED" in unicodedata.name(ch, "")
    except ValueError:
        return False


def _ascii_to_kebab(text: str) -> str:
    """Convert ASCII text to kebab-case."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")
