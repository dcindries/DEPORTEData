#!/usr/bin/env python3
"""Entrenamiento local QLoRA para Qwen2.5-3B-Instruct."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
)
from trl import SFTTrainer

DEFAULT_TARGET_MODULES = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "up_proj",
    "down_proj",
    "gate_proj",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Entrena Qwen2.5-3B-Instruct con QLoRA")
    parser.add_argument("--model_name", default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--train_file", default="../data/train.jsonl")
    parser.add_argument("--val_file", default="../data/val.jsonl")
    parser.add_argument("--output_dir", default="../outputs")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--grad_accum", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max_length", type=int, default=1024)
    return parser


def to_chat_text(example: dict, tokenizer: AutoTokenizer) -> dict:
    text = tokenizer.apply_chat_template(
        example["messages"],
        tokenize=False,
        add_generation_prompt=False,
    )
    return {"text": text}


def detect_linear_modules(model: AutoModelForCausalLM) -> set[str]:
    linear_names: set[str] = set()
    for name, module in model.named_modules():
        class_name = module.__class__.__name__.lower()
        if isinstance(module, torch.nn.Linear) or "linear" in class_name:
            linear_names.add(name.split(".")[-1])
    return linear_names


def choose_optimizer() -> str:
    try:
        _ = TrainingArguments(output_dir="/tmp/opt-check", optim="paged_adamw_8bit")
        return "paged_adamw_8bit"
    except Exception:
        return "adamw_torch"


def main() -> int:
    args = build_parser().parse_args()

    if not torch.cuda.is_available():
        print(
            "ERROR: No se detectó CUDA. QLoRA en 4-bit con bitsandbytes requiere GPU NVIDIA.\n"
            "Sugerencia: ejecuta este script en una máquina con CUDA disponible."
        )
        return 1

    base_dir = Path(__file__).resolve().parent
    train_file = str(base_dir.joinpath(args.train_file).resolve())
    val_file = str(base_dir.joinpath(args.val_file).resolve())
    output_dir = str(base_dir.joinpath(args.output_dir).resolve())
    logging_dir = str(Path(output_dir).joinpath("logs"))

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)
    model.config.use_cache = False

    detected_modules = detect_linear_modules(model)
    print(f"Módulos lineales detectados ({len(detected_modules)}): {sorted(detected_modules)}")

    adjusted_targets = [m for m in DEFAULT_TARGET_MODULES if m in detected_modules]
    missing_targets = [m for m in DEFAULT_TARGET_MODULES if m not in detected_modules]
    if missing_targets:
        print(f"Aviso: target_modules no encontrados y excluidos: {missing_targets}")
    if not adjusted_targets:
        raise RuntimeError(
            "No se encontró ningún target_module válido para LoRA. Revisa la arquitectura del modelo."
        )

    dataset = load_dataset(
        "json",
        data_files={"train": train_file, "validation": val_file},
    )
    dataset = dataset.map(lambda x: to_chat_text(x, tokenizer))

    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=adjusted_targets,
    )

    optim_name = choose_optimizer()
    print(f"Optimizador seleccionado: {optim_name}")

    training_args = TrainingArguments(
        output_dir=output_dir,
        logging_dir=logging_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        seed=42,
        logging_steps=10,
        eval_steps=50,
        save_steps=50,
        save_total_limit=2,
        evaluation_strategy="steps",
        save_strategy="steps",
        load_best_model_at_end=False,
        bf16=True,
        fp16=False,
        optim=optim_name,
        report_to="none",
        gradient_checkpointing=True,
        warmup_ratio=0.05,
        lr_scheduler_type="cosine",
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        peft_config=peft_config,
        dataset_text_field="text",
        max_seq_length=args.max_length,
        args=training_args,
    )

    trainer.train()
    trainer.model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)

    print(f"Adapter guardado en: {output_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR durante el entrenamiento: {exc}")
        raise SystemExit(1) from exc
