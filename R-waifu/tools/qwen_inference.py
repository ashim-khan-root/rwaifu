"""Qwen2.5-Coder-0.5B inference via raw OpenVINO compiled_model API.

Uses the same working pattern from personal-coach (not the broken LLMPipeline).
~21ms/tok on CPU, ~35ms/tok on iGPU (not worth it for 0.5B).

Model path resolution (in order):
  1. env var QWEN_MODEL_PATH
  2. Windows default: C:/models/qwen2.5-coder-0.5b-int4
  3. Linux default: ~/.cache/openvino-models/qwen2.5-coder-0.5b-int4
"""
import sys, os, json
from pathlib import Path
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _resolve_model_path(custom=None):
    if custom:
        return Path(custom)
    env = os.environ.get("QWEN_MODEL_PATH")
    if env:
        return Path(env)
    if sys.platform == "win32":
        return Path("C:/models/qwen2.5-coder-0.5b-int4")
    return Path.home() / ".cache" / "openvino-models" / "qwen2.5-coder-0.5b-int4"


class QwenInference:
    def __init__(self, model_path=None):
        model_path = _resolve_model_path(model_path)
        xml = model_path / "openvino_model.xml"
        if not xml.exists():
            raise FileNotFoundError(
                f"Model not found at {model_path}\n"
                f"  Download/convert it first. See SETUP_GUIDE.md for instructions."
            )
        self.model_path = model_path
        self.core = None
        self._lazy_load()

    def _lazy_load(self):
        import openvino as ov
        self.core = ov.Core()
        model = self.core.read_model(str(self.model_path / "openvino_model.xml"))
        self._compiled = self.core.compile_model(model, "CPU")

        tok_path = self.model_path / "tokenizer.json"
        if tok_path.exists():
            from tokenizers import Tokenizer
            self.tok = Tokenizer.from_file(str(tok_path))
        else:
            self.tok = None

        gc_path = self.model_path / "generation_config.json"
        if gc_path.exists():
            with open(gc_path) as f:
                gc = json.load(f)
            eos = gc.get("eos_token_id", 151645)
            self.eos_token_id = eos if isinstance(eos, int) else eos[0]
        else:
            self.eos_token_id = 151645

    def generate(self, prompt, max_new_tokens=200, temperature=0.7,
                 top_p=0.9, top_k=40, repetition_penalty=1.1):
        if not self.tok:
            return "[ERROR] tokenizer.json not found in model directory"

        encoded = self.tok.encode(prompt)
        all_ids = list(encoded.ids)
        prompt_len = len(all_ids)
        generated = []

        infer = self._compiled.create_infer_request()

        for step in range(max_new_tokens):
            if step == 0:
                input_ids = np.array([all_ids], dtype=np.int64)
                pos = np.arange(input_ids.shape[1], dtype=np.int64).reshape(1, -1)
            else:
                input_ids = np.array([[generated[-1]]], dtype=np.int64)
                pos = np.array([[prompt_len + step - 1]], dtype=np.int64)

            attn = np.ones_like(input_ids, dtype=np.int64)
            beam = np.zeros(1, dtype=np.int32)

            infer.set_tensor("input_ids", input_ids)
            infer.set_tensor("attention_mask", attn)
            infer.set_tensor("position_ids", pos)
            infer.set_tensor("beam_idx", beam)
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


def query(prompt, model_path=None, max_length=256, temperature=0.7):
    try:
        qwen = QwenInference(model_path)
        result = qwen.generate(prompt, max_length, temperature)
        return result, None
    except FileNotFoundError as e:
        return None, str(e)
    except ImportError as e:
        return None, f"Missing dependency: {e}. Install: pip install openvino tokenizers numpy"
    except Exception as e:
        return None, f"Inference failed: {e}"


if __name__ == "__main__":
    result, err = query("Hello! Who are you?")
    if err:
        print(err)
    else:
        print(result)
