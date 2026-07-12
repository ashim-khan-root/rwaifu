import openvino as ov
import numpy as np
from tokenizers import Tokenizer
import json
from pathlib import Path
import re
import time

MODEL_PATH = Path.home() / ".cache" / "openvino-models" / "qwen2.5-coder-0.5b-int4"


class QwenInference:
    def __init__(self, model_path=MODEL_PATH):
        model_path = Path(model_path)
        if not (model_path / "openvino_model.xml").exists():
            raise FileNotFoundError(f"Model not found at {model_path}")
        self.model_path = model_path
        self.core = ov.Core()
        self.tok = Tokenizer.from_file(str(model_path / "tokenizer.json"))
        with open(model_path / "generation_config.json") as f:
            gen_config = json.load(f)
        eos = gen_config.get("eos_token_id", 151645)
        self.eos_token_id = eos if isinstance(eos, int) else eos[0]
        self._compiled = None
        self.chat_template = self._load_chat_template()

    def _load_chat_template(self):
        ct_path = self.model_path / "chat_template.jinja"
        tok_cfg_path = self.model_path / "tokenizer_config.json"
        if ct_path.exists():
            return ct_path.read_text()
        if tok_cfg_path.exists():
            cfg = json.loads(tok_cfg_path.read_text())
            return cfg.get("chat_template")
        return None

    def _apply_chat_template(self, messages):
        parts = []
        has_system = messages[0]["role"] == "system" if messages else False
        if not has_system:
            parts.append("<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\n")
        for m in messages:
            role = m["role"]
            content = m["content"]
            if role == "system":
                parts.append(f"<|im_start|>system\n{content}<|im_end|>\n")
            elif role == "user":
                parts.append(f"<|im_start|>user\n{content}<|im_end|>\n")
            elif role == "assistant":
                parts.append(f"<|im_start|>assistant\n{content}<|im_end|>\n")
        parts.append("<|im_start|>assistant\n")
        return "".join(parts)

    def _ensure_compiled(self):
        if self._compiled is None:
            model = self.core.read_model(str(self.model_path / "openvino_model.xml"))
            self._compiled = self.core.compile_model(model, "CPU")
        return self._compiled.create_infer_request()

    def generate(self, prompt, max_new_tokens=200, temperature=0.7, top_p=0.9, top_k=40, repetition_penalty=1.1):
        encoded = self.tok.encode(prompt)
        all_ids = list(encoded.ids)
        prompt_len = len(all_ids)
        generated = []

        infer = self._ensure_compiled()

        for step in range(max_new_tokens):
            if step == 0:
                input_ids = np.array([all_ids], dtype=np.int64)
                pos = np.arange(input_ids.shape[1], dtype=np.int64).reshape(1, -1)
            else:
                input_ids = np.array([[generated[-1]]], dtype=np.int64)
                pos = np.array([[prompt_len + step - 1]], dtype=np.int64)

            attn = np.ones_like(input_ids, dtype=np.int64)
            beam = np.zeros(1, dtype=np.int32)

            infer.set_tensor("input_ids", ov.Tensor(input_ids))
            infer.set_tensor("attention_mask", ov.Tensor(attn))
            infer.set_tensor("position_ids", ov.Tensor(pos))
            infer.set_tensor("beam_idx", ov.Tensor(beam))
            infer.infer()

            logits = infer.get_output_tensor(0).data[0, -1, :].copy()

            if repetition_penalty != 1.0:
                for tid in set(all_ids):
                    if logits[tid] < 0:
                        logits[tid] *= repetition_penalty
                    else:
                        logits[tid] /= repetition_penalty

            if temperature > 0:
                logits = logits / temperature
                probs = np.exp(logits - np.max(logits))
                probs /= probs.sum()
                sorted_idx = np.argsort(probs)[::-1]
                if top_k > 0 and top_k < len(probs):
                    probs[sorted_idx[top_k:]] = 0
                    probs /= probs.sum()
                if top_p < 1.0:
                    cumsum = np.cumsum(probs[sorted_idx])
                    cutoff = np.searchsorted(cumsum, top_p) + 1
                    mask = np.zeros_like(probs, dtype=bool)
                    mask[sorted_idx[:cutoff]] = True
                    probs[~mask] = 0
                    probs /= probs.sum()
                next_id = int(np.random.choice(len(probs), p=probs))
            else:
                next_id = int(np.argmax(logits))

            if next_id == self.eos_token_id:
                break
            generated.append(next_id)
            all_ids.append(next_id)

        return self.tok.decode(generated)

    def generate_stream(self, prompt, max_new_tokens=200, temperature=0.7, top_p=0.9, top_k=40, repetition_penalty=1.1):
        encoded = self.tok.encode(prompt)
        all_ids = list(encoded.ids)
        prompt_len = len(all_ids)
        generated = []

        infer = self._ensure_compiled()

        for step in range(max_new_tokens):
            if step == 0:
                input_ids = np.array([all_ids], dtype=np.int64)
                pos = np.arange(input_ids.shape[1], dtype=np.int64).reshape(1, -1)
            else:
                input_ids = np.array([[generated[-1]]], dtype=np.int64)
                pos = np.array([[prompt_len + step - 1]], dtype=np.int64)

            attn = np.ones_like(input_ids, dtype=np.int64)
            beam = np.zeros(1, dtype=np.int32)

            infer.set_tensor("input_ids", ov.Tensor(input_ids))
            infer.set_tensor("attention_mask", ov.Tensor(attn))
            infer.set_tensor("position_ids", ov.Tensor(pos))
            infer.set_tensor("beam_idx", ov.Tensor(beam))
            infer.infer()

            logits = infer.get_output_tensor(0).data[0, -1, :].copy()

            if repetition_penalty != 1.0:
                for tid in set(all_ids):
                    if logits[tid] < 0:
                        logits[tid] *= repetition_penalty
                    else:
                        logits[tid] /= repetition_penalty

            if temperature > 0:
                logits = logits / temperature
                probs = np.exp(logits - np.max(logits))
                probs /= probs.sum()
                sorted_idx = np.argsort(probs)[::-1]
                if top_k > 0 and top_k < len(probs):
                    probs[sorted_idx[top_k:]] = 0
                    probs /= probs.sum()
                if top_p < 1.0:
                    cumsum = np.cumsum(probs[sorted_idx])
                    cutoff = np.searchsorted(cumsum, top_p) + 1
                    mask = np.zeros_like(probs, dtype=bool)
                    mask[sorted_idx[:cutoff]] = True
                    probs[~mask] = 0
                    probs /= probs.sum()
                next_id = int(np.random.choice(len(probs), p=probs))
            else:
                next_id = int(np.argmax(logits))

            if next_id == self.eos_token_id:
                break
            generated.append(next_id)
            all_ids.append(next_id)
            yield self.tok.decode([next_id])

    def chat(self, messages, **kwargs):
        prompt = self._apply_chat_template(messages)
        return self.generate(prompt, **kwargs)

    def chat_stream(self, messages, **kwargs):
        prompt = self._apply_chat_template(messages)
        yield from self.generate_stream(prompt, **kwargs)


if __name__ == "__main__":
    qwen = QwenInference()
    result = qwen.generate("The meaning of life is")
    print(result)

    print("\n--- Chat example ---")
    result = qwen.chat([
        {"role": "user", "content": "What is Python used for? Answer in one sentence."}
    ], max_new_tokens=60)
    print(result)
