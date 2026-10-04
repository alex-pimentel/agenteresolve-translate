"""Tool logic for Translator.

Providers are injected via environment: `LLM_*` (OpenAI-compatible, defaults to OpenRouter)
and `INFERENCE_URL`/`INFERENCE_KEY` for vision/audio models. No user content is persisted —
results are ephemeral and cleaned up by the operator.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from .providers import llm_complete


@dataclass
class ToolInput:
    text: str = ""
    file_bytes: bytes | None = None
    filename: str | None = None
    content_type: str | None = None
    params: dict[str, object] | None = None


def _input_text(ti: ToolInput) -> str:
    if ti.text and ti.text.strip():
        return ti.text
    if ti.file_bytes is not None:
        name = (ti.filename or "").lower()
        ctype = (ti.content_type or "").lower()
        if "pdf" in ctype or name.endswith(".pdf"):
            try:
                from pypdf import PdfReader

                reader = PdfReader(BytesIO(ti.file_bytes))
                return "\n".join((page.extract_text() or "") for page in reader.pages)
            except Exception:  # noqa: BLE001 - fall back to raw decode
                pass
        return ti.file_bytes.decode("utf-8", errors="ignore")
    return ""


def run(ti: ToolInput) -> tuple[bytes, str, str]:
    text = _input_text(ti)
    target = str((ti.params or {}).get("target") or (ti.params or {}).get("lang") or "en")
    out = llm_complete(
        f"Translate the following text to {target}. Preserve markdown and code fences. "
        f"Return only the translation.\n\n{text}"
    )
    return out.encode("utf-8"), "text/plain; charset=utf-8", "result.txt"
