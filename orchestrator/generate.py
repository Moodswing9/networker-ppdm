"""Generate automation scripts using NVIDIA Qwen2.5-Coder via NIM."""

from __future__ import annotations

import os

from openai import OpenAI

_MODEL = "qwen/qwen2.5-coder-32b-instruct"


def generate_script(description: str) -> str:
    """Return a Python or bash script matching the given description.

    Uses Qwen2.5-Coder-32B for accurate data-protection domain code generation.
    Set NVIDIA_API_KEY in your environment before calling.
    """
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.environ["NVIDIA_API_KEY"],
    )

    system_prompt = (
        "You are an expert Dell EMC NetWorker and PowerProtect Data Manager (PPDM) "
        "automation engineer. Generate clean, production-ready Python or bash scripts "
        "that interact with the NetWorker REST API or PPDM REST API. "
        "Include error handling, logging, and comments only where the logic is non-obvious. "
        "Return only the script — no markdown fences, no prose."
    )

    resp = client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": description},
        ],
        temperature=0.1,
        max_tokens=2048,
    )
    return resp.choices[0].message.content or ""
