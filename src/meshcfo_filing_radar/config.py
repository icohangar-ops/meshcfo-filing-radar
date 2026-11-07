"""Settings for MeshCFO Filing Radar.

Design defaults (2026-11 local-first rework):
- Inference is LOCAL by default: an open-weight GGUF model run on this
  machine via llama.cpp (see local_llm.py). No network is used.
- ALL external services (Nebius Token Factory live LLM calls, Tavily
  search) are DISABLED by default. They only run when
  MESHCFO_ENABLE_EXTERNAL=1 is set AND the relevant API key is present.
"""

from __future__ import annotations

from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

HOME = Path.home()
DEFAULT_LOCAL_MODEL = HOME / "workspace" / "models" / "qwen2.5-0.5b-instruct-q4_k_m.gguf"
DEFAULT_ASK_PY = HOME / "workspace" / "tools" / "local-llm" / "ask.py"


def _read_secret_file(path: Path | None) -> str:
    if not path:
        return ""
    p = Path(path)
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8").strip()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", populate_by_name=True
    )

    # --- Inference -----------------------------------------------------
    # "local" (default): open-weight GGUF model on this machine.
    # "offline": deterministic rules only, no model at all.
    # "live": Nebius Token Factory (external; requires opt-in below).
    inference_mode: str = Field(default="local", alias="MESHCFO_INFERENCE")
    local_model_path: str = Field(
        default=str(DEFAULT_LOCAL_MODEL), alias="MESHCFO_LOCAL_MODEL"
    )
    local_llm_ask_py: str = Field(
        default=str(DEFAULT_ASK_PY), alias="MESHCFO_LOCAL_LLM_ASK_PY"
    )
    local_max_tokens_triage: int = Field(default=256, alias="MESHCFO_LOCAL_MAX_TOKENS_TRIAGE")
    local_max_tokens_deepen: int = Field(default=512, alias="MESHCFO_LOCAL_MAX_TOKENS_DEEPEN")

    # --- External services (OFF by default) ----------------------------
    enable_external_services: bool = Field(default=False, alias="MESHCFO_ENABLE_EXTERNAL")

    # Nebius Token Factory — only used in "live" inference mode AND only
    # when external services are explicitly enabled.
    nebius_api_key: str = Field(default="", alias="NEBIUS_API_KEY")
    nebius_api_key_file: str = Field(default="", alias="NEBIUS_API_KEY_FILE")
    nebius_base_url: str = Field(
        default="https://api.tokenfactory.nebius.com/v1/", alias="NEBIUS_BASE_URL"
    )
    nebius_triage_model: str = Field(
        default="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
        alias="NEBIUS_TRIAGE_MODEL",
    )
    nebius_deepen_model: str = Field(
        default="nvidia/Nemotron-3_5-Lightning",
        alias="NEBIUS_DEEPEN_MODEL",
    )

    # Tavily — market context only, never EDGAR evidence; opt-in only.
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")
    tavily_api_key_file: str = Field(default="", alias="TAVILY_API_KEY_FILE")

    deepen_severity_threshold: int = Field(default=7, alias="DEEPEN_SEVERITY_THRESHOLD")

    def resolved_nebius_key(self) -> str:
        if self.nebius_api_key.strip():
            return self.nebius_api_key.strip()
        return _read_secret_file(Path(self.nebius_api_key_file)) if self.nebius_api_key_file else ""

    def resolved_tavily_key(self) -> str:
        if self.tavily_api_key.strip():
            return self.tavily_api_key.strip()
        return _read_secret_file(Path(self.tavily_api_key_file)) if self.tavily_api_key_file else ""

    @property
    def local_model_file(self) -> Path:
        return Path(self.local_model_path).expanduser()

    @property
    def live_llm_ready(self) -> bool:
        """Live cloud LLM is usable ONLY with explicit external opt-in + key."""
        return self.enable_external_services and bool(self.resolved_nebius_key())

    @property
    def tavily_allowed(self) -> bool:
        """Tavily runs ONLY with explicit external opt-in + key."""
        return self.enable_external_services and bool(self.resolved_tavily_key())

    @property
    def tavily_ready(self) -> bool:  # backwards-compatible alias
        return self.tavily_allowed


@lru_cache
def get_settings() -> Settings:
    return Settings()
