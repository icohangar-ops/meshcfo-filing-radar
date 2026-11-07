"""Local, open-weight inference via llama.cpp (no network).

The default inference path for Filing Radar. It runs a small GGUF model
on this machine:

- Preferred: in-process via the `llama_cpp` Python package (install with
  `pip install llama-cpp-python`, or use the "local" extra).
- Fallback: subprocess call to the local-llm helper `ask.py`
  (MESHCFO_LOCAL_LLM_ASK_PY), which runs the same GGUF model through its
  own llama-cpp-python venv.

Both paths are fully local: the model file never leaves the machine and
no API is called. The client is honest about scale — the verified model
is Qwen2.5-0.5B-Instruct (Q4_K_M), a very small model. It drafts the
triage headline/rationale and the deep-brief narrative fields as JSON;
the pipeline validates and clamps every field, and falls back to the
deterministic offline rules for any card whose model output does not
parse or validate.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from meshcfo_filing_radar.config import Settings
from meshcfo_filing_radar.llm import TokenFactoryError, parse_json_payload


class LocalLLMError(RuntimeError):
    pass


class LocalModelClient:
    """complete_json() backed by a local GGUF model."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model_path = settings.local_model_file
        if not self.model_path.is_file():
            raise LocalLLMError(
                f"Local model file not found: {self.model_path}. "
                "Set MESHCFO_LOCAL_MODEL to a GGUF file, or use "
                "MESHCFO_INFERENCE=offline for deterministic rules only."
            )
        self.model_label = f"local:{self.model_path.name}"
        self.last_model = self.model_label
        self.last_error: str | None = None
        self._llama = None  # lazy in-process handle
        self._backend: str | None = None

    # -- backends ------------------------------------------------------

    def _complete_inprocess(self, system: str, user: str, max_tokens: int) -> str:
        from llama_cpp import Llama  # imported lazily; optional dependency

        if self._llama is None:
            self._llama = Llama(
                model_path=str(self.model_path),
                n_ctx=4096,
                n_threads=2,
                verbose=False,
            )
        out = self._llama.create_chat_completion(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=0.0,
        )
        return out["choices"][0]["message"]["content"] or ""

    def _complete_subprocess(self, system: str, user: str, max_tokens: int) -> str:
        ask_py = Path(self.settings.local_llm_ask_py).expanduser()
        if not ask_py.is_file():
            raise LocalLLMError(
                f"llama_cpp is not importable and the ask.py helper was not "
                f"found at {ask_py}. Install llama-cpp-python or set "
                "MESHCFO_LOCAL_LLM_ASK_PY."
            )
        env = dict(os.environ)
        env["LOCAL_LLM_MODEL"] = str(self.model_path)
        proc = subprocess.run(
            [
                str(ask_py),
                "--system", system,
                "--max-tokens", str(max_tokens),
                "--temperature", "0",
                "--ctx", "4096",
                user,
            ],
            capture_output=True,
            text=True,
            timeout=900,
            env=env,
        )
        if proc.returncode != 0:
            raise LocalLLMError(
                f"ask.py exited {proc.returncode}: {(proc.stderr or '')[:300]}"
            )
        return proc.stdout or ""

    # -- public API (mirrors TokenFactoryClient.complete_json) ---------

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.0,  # accepted for API parity; local runs at 0
        max_tokens: int = 256,
        model: str | None = None,  # accepted for API parity; one local model
    ) -> dict[str, Any]:
        errors: list[str] = []
        # Try in-process first, then the ask.py helper. Whichever succeeds
        # first is the backend for this client (recorded for reporting).
        order = ["inprocess", "subprocess"]
        if self._backend == "subprocess":
            order = ["subprocess", "inprocess"]
        for backend in order:
            try:
                if backend == "inprocess":
                    text = self._complete_inprocess(system, user, max_tokens)
                else:
                    text = self._complete_subprocess(system, user, max_tokens)
            except ImportError as e:
                errors.append(f"inprocess: llama_cpp unavailable ({e})")
                continue
            except Exception as e:  # noqa: BLE001
                errors.append(f"{backend}: {e}")
                continue
            try:
                payload = parse_json_payload(text)
            except TokenFactoryError as e:
                errors.append(f"{backend}: unparseable output ({e})")
                continue
            self._backend = backend
            self.last_model = self.model_label
            return payload
        self.last_error = "; ".join(errors)
        raise LocalLLMError(f"Local model failed: {self.last_error}")

    @property
    def backend(self) -> str:
        return self._backend or "unstarted"
