"""
AI Service Layer (spec §37). This is the single entry point every app
uses for AI assistance — guided interviews, document drafting, gap
explanations, evidence suggestions, framework extraction, executive
summaries. Callers never talk to a provider directly, and every call
is logged to AIGeneration for governance/traceability (spec §38).
"""

from django.conf import settings

from .models import AIGeneration
from .providers.mock import MockProvider
from .providers.openai_compatible import OpenAICompatibleProvider

DEFAULT_SYSTEM_PROMPT = (
    "You are the Bohlale GRC assistant. You help South African SMEs, NPOs and "
    "consultants implement governance, risk and compliance management systems. "
    "You draft practical, plain-language content grounded only in the "
    "organisational facts provided to you. You never invent organisational facts. "
    "Everything you produce is a DRAFT that a qualified human must review before "
    "it becomes an approved or published record. You never claim to guarantee "
    "certification or legal compliance."
)


def get_provider():
    if settings.AI_PROVIDER == "openai_compatible" and settings.AI_API_KEY:
        return OpenAICompatibleProvider(
            base_url=settings.AI_API_BASE, api_key=settings.AI_API_KEY, model=settings.AI_MODEL
        )
    return MockProvider()


def generate(
    *,
    organisation,
    user,
    purpose,
    user_prompt,
    context_reference="",
    system_prompt=None,
    related_object=None,
    max_tokens=1200,
):
    """
    Run one AI generation and record it. Returns the created
    AIGeneration instance (output text is on `.output_text`).

    Tenant boundary: only `context_reference`/`user_prompt` passed in
    by the caller are ever sent to the provider — callers are
    responsible for building that text from the target organisation's
    own verified data (see knowledge.services.verified_context_text),
    never another tenant's.
    """
    provider = get_provider()
    output = provider.complete(
        system_prompt=system_prompt or DEFAULT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        purpose=purpose,
        max_tokens=max_tokens,
    )
    model_name = getattr(provider, "model", provider.name)
    generation = AIGeneration.objects.create(
        organisation=organisation,
        requested_by=user if getattr(user, "is_authenticated", False) else None,
        purpose=purpose,
        provider=provider.name,
        model=model_name,
        context_reference=context_reference,
        output_text=output,
    )
    if related_object is not None:
        generation.related_object = related_object
        generation.save(update_fields=["content_type", "object_id"])
    return generation
