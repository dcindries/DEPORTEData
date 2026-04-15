#!/usr/bin/env python3
"""Prueba de inferencia con modelo base + adaptador LoRA entrenado."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prueba inferencia con Qwen + LoRA")
    parser.add_argument("--model_name", default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--adapter_path", default="../outputs")
    parser.add_argument("--system_prompt_path", default="../configs/training.md")
    parser.add_argument("--question", default=None, help="Pregunta opcional por CLI")
    parser.add_argument("--max_new_tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--do_sample", action="store_true", help="Activa muestreo estocástico")
    return parser


def load_system_prompt(system_prompt_path: str) -> str:
    path = Path(__file__).resolve().parent.joinpath(system_prompt_path).resolve()
    return path.read_text(encoding="utf-8").strip()


def main() -> None:
    args = build_parser().parse_args()

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model_name, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base_model = AutoModelForCausalLM.from_pretrained(
        args.model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )

    adapter_path = str(Path(__file__).resolve().parent.joinpath(args.adapter_path).resolve())
    print(f"Cargando adapter LoRA desde: {adapter_path}")
    model = PeftModel.from_pretrained(base_model, adapter_path)
    model.eval()

    question = args.question.strip() if args.question else input("Escribe tu pregunta: ").strip()
    if not question:
        print("No se recibió pregunta.")
        return

    system_prompt = load_system_prompt(args.system_prompt_path)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    gen_kwargs = {
        "max_new_tokens": args.max_new_tokens,
        "do_sample": args.do_sample,
        "repetition_penalty": 1.1,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
    }
    if args.do_sample:
        gen_kwargs["temperature"] = args.temperature
        gen_kwargs["top_p"] = 0.9

    with torch.inference_mode():
        outputs = model.generate(**inputs, **gen_kwargs)

    response_ids = outputs[0][inputs["input_ids"].shape[1] :]
    response = tokenizer.decode(response_ids, skip_special_tokens=True)

    print("\nRespuesta:\n")
    print(response.strip())


if __name__ == "__main__":
    main()
