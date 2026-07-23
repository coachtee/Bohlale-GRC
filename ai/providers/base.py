class AIProvider:
    """
    Provider adapter interface (spec §37). Every provider — mock,
    OpenAI-compatible, a future Qwen-specific adapter, etc. — implements
    this same shape, so `ai/service.py` and every caller in the app
    never needs to know which provider is active.
    """

    name = "base"

    def complete(self, *, system_prompt, user_prompt, purpose="general", max_tokens=1200):
        """Return a plain-text completion. Must not raise for normal
        operation — callers should get a usable (even if degraded)
        string back so a flaky AI provider never blocks a human
        workflow that has a manual fallback."""
        raise NotImplementedError
