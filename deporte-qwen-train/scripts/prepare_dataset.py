#!/usr/bin/env python3
"""Valida y prepara los datasets JSONL para entrenamiento conversacional."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_ROLES = {"system", "user", "assistant"}


def validate_line(obj: dict, line_no: int, file_path: Path) -> None:
    if "messages" not in obj or not isinstance(obj["messages"], list):
        raise ValueError(f"{file_path}:{line_no} debe contener una lista 'messages'.")

    roles = {m.get("role") for m in obj["messages"] if isinstance(m, dict)}
    if not REQUIRED_ROLES.issubset(roles):
        raise ValueError(
            f"{file_path}:{line_no} debe incluir roles system, user y assistant."
        )

    for message in obj["messages"]:
        if not isinstance(message, dict):
            raise ValueError(f"{file_path}:{line_no} contiene un mensaje inválido.")
        if "role" not in message or "content" not in message:
            raise ValueError(
                f"{file_path}:{line_no} cada mensaje requiere 'role' y 'content'."
            )


def validate_jsonl(file_path: Path) -> int:
    count = 0
    with file_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            validate_line(obj, line_no, file_path)
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida archivos JSONL de entrenamiento.")
    parser.add_argument(
        "--train",
        default="../data/train.jsonl",
        help="Ruta al archivo train.jsonl",
    )
    parser.add_argument(
        "--val",
        default="../data/val.jsonl",
        help="Ruta al archivo val.jsonl",
    )
    args = parser.parse_args()

    train_path = Path(__file__).resolve().parent.joinpath(args.train).resolve()
    val_path = Path(__file__).resolve().parent.joinpath(args.val).resolve()

    train_count = validate_jsonl(train_path)
    val_count = validate_jsonl(val_path)

    print(f"Dataset OK. train={train_count} ejemplos, val={val_count} ejemplos")


if __name__ == "__main__":
    main()
