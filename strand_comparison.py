#!/usr/bin/env python3
"""Strand bootstrap:
- Extract the bootstrap source from LucasAgent/BOOTSTRAP.md
- Lex it, hash it
- Derive match sequences per gemini rules from LucasAgent/.gemini/rules/*.md
- Compare sequences against the same rules so mismatch is visible
- Output: sync_all.json with sequences + match_matrix (or no-op if already synced)
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional


ROOT = Path("C:/Users/Maria101/LucasAgent")
BOOTSTRAP_FILE = ROOT / "BOOTSTRAP.md"
RULES_DIR = ROOT / ".gemini" / "rules"
OUT_FILE = ROOT / "sync_all.json"


@dataclass(frozen=True)
class TokenSequence:
    source_path: str
    sequence_hash: str
    token_count: int
    tokens: tuple[str, ...] = field(repr=False, compare=False)
    note: str = ""


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def lex_command(text: str) -> List[str]:
    # Normalize a command string into comparable tokens
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return []
    tokens = re.findall(r"[^\s\"']+|\"[^\"]+\"|'[^']+'", text)
    return [t.strip('"').strip("'") for t in tokens if t.strip('"').strip("'")]


def extract_bootstrap_source() -> str:
    if not BOOTSTRAP_FILE.exists():
        raise FileNotFoundError(f"Missing bootstrap source: {BOOTSTRAP_FILE}")
    return BOOTSTRAP_FILE.read_text(encoding="utf-8")


def derive_sequences(rules_dir: Path) -> dict[str, TokenSequence]:
    result: dict[str, TokenSequence] = {}
    if not rules_dir.exists():
        return result
    for rule_file in sorted(rules_dir.glob("*.md")):
        rel = str(rule_file.relative_to(ROOT)).replace("\\", "/")
        text = rule_file.read_text(encoding="utf-8")
        tokens = tuple(lex_command(text))
        seq = TokenSequence(
            source_path=rel,
            sequence_hash=sha256(" ".join(tokens)),
            token_count=len(tokens),
            tokens=tokens,
        )
        result[rel] = seq
    return result


def build_match_matrix(derived: dict[str, TokenSequence], target_source_text: str) -> Dict[str, dict]:
    target_tokens = tuple(lex_command(target_source_text))
    target_hash = sha256(" ".join(target_tokens))
    out: Dict[str, dict] = {}
    for rel, seq in derived.items():
        out[rel] = {
            "sequence_hash": seq.sequence_hash,
            "target_hash": target_hash,
            "match": seq.sequence_hash == target_hash,
            "token_count_source": seq.token_count,
            "token_count_target": len(target_tokens),
        }
    return out


def build_payload(target_source_text: str) -> dict:
    source_hash = sha256(target_source_text)
    derived = derive_sequences(RULES_DIR)
    matrix = build_match_matrix(derived, target_source_text)
    synced = all(v["match"] for v in matrix.values()) if matrix else False
    payload = {
        "synced": synced,
        "source": {
            "path": str(BOOTSTRAP_FILE.relative_to(ROOT)).replace("\\", "/"),
            "length": len(target_source_text),
            "sha256": source_hash,
        },
        "derived": {
            rel: {
                "source_path": seq.source_path,
                "sequence_hash": seq.sequence_hash,
                "token_count": seq.token_count,
            }
            for rel, seq in derived.items()
        },
        "target_for_compare": {
            "length": len(target_source_text),
            "sha256": source_hash,
        },
        "match_matrix": matrix,
        "note": "No-op if already synced per gemini rules." if synced else "Mismatch detected.",
    }
    return payload


def main() -> int:
    source_text = extract_bootstrap_source()
    payload = build_payload(source_text)
    OUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if payload["synced"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
