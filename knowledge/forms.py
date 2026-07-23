from core.forms import TenantModelForm

from .models import KnowledgeItem


class KnowledgeItemForm(TenantModelForm):
    class Meta:
        model = KnowledgeItem
        fields = ["category", "label", "value", "status", "source"]
