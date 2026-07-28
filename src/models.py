"""Model providers. Common interface: .complete(system, user) -> str.

Everything runs through OpenRouter (one key, hundreds of models). MockProvider
lets you test the pipeline offline with no key and no cost.
"""
from __future__ import annotations


class Provider:
    name = "base"

    def complete(self, system: str, user: str, **kw) -> str:
        raise NotImplementedError


class OpenRouterProvider(Provider):
    """OpenRouter via its OpenAI-compatible API: one key, hundreds of models.

    Temperature is only sent if you set it, because many reasoning/free models
    reject a temperature argument and would error otherwise.
    """
    name = "openrouter"

    def __init__(self, model: str = "nvidia/nemotron-3-ultra-550b-a55b:free",
                 temperature: float | None = None, **kw):
        import os
        from openai import OpenAI  # OpenRouter is OpenAI-compatible, so we use the OpenAI SDK
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ.get("OPENROUTER_API_KEY"),
        )
        self.model = model
        self.kw = dict(kw)
        if temperature is not None:
            self.kw["temperature"] = temperature

    def complete(self, system, user, **kw):
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": user})
        r = self.client.chat.completions.create(
            model=self.model, messages=msgs, **{**self.kw, **kw}
        )
        return r.choices[0].message.content or ""


class MockProvider(Provider):
    """Offline provider for testing the pipeline with no API key or cost."""
    name = "mock"

    def __init__(self, canned: dict | None = None,
                 default: str = "Opo, Lola. Sasama po ako sa inyo sa probinsya. Salamat po.",
                 **kw):
        self.canned = canned or {}
        self.default = default

    def complete(self, system, user, **kw):
        for key, val in self.canned.items():
            if key in user:
                return val
        return self.default


PROVIDERS = {
    "openrouter": OpenRouterProvider,
    "mock": MockProvider,
}


def get_provider(name: str, model: str | None = None, **kw) -> Provider:
    cls = PROVIDERS[name]
    if name == "mock":
        return cls()
    if model:
        return cls(model=model, **kw)
    return cls(**kw)