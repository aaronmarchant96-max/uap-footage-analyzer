"""
Review queue I/O utilities.

Provides clean functions to read and write lists of NormalizedCase objects
to/from .jsonl files. This keeps the ingestion and review parts of the
pipeline round-trippable.
"""

from pathlib import Path
from typing import List
import json

from .schemas import NormalizedCase


def load_review_queue(path: Path | str) -> List[NormalizedCase]:
    """
    Load a review queue .jsonl file and return a list of NormalizedCase objects.
    """
    path = Path(path)
    if not path.exists():
        return []

    cases: List[NormalizedCase] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            cases.append(NormalizedCase.from_dict(data))
    return cases


def save_review_queue(cases: List[NormalizedCase], path: Path | str) -> None:
    """
    Write a list of NormalizedCase objects to a .jsonl file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case.to_dict(), ensure_ascii=False) + "\n")
