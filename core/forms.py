from django import forms


class TenantModelForm(forms.ModelForm):
    """
    Base ModelForm for tenant-scoped models. Accepts an `organisation`
    kwarg (supplied by core.base_views.Tenant{Create,Update}View) so
    subclasses can filter FK/M2M choice querysets to the active tenant,
    e.g. limiting an "owner" field to that organisation's members.
    """

    def __init__(self, *args, organisation=None, **kwargs):
        self.organisation = organisation
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            css = widget.attrs.get("class", "")
            if isinstance(widget, (forms.CheckboxInput,)):
                widget.attrs["class"] = (css + " checkbox-input").strip()
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs["class"] = (css + " form-select").strip()
            elif isinstance(widget, forms.Textarea):
                widget.attrs["class"] = (css + " form-textarea").strip()
            else:
                widget.attrs["class"] = (css + " form-input").strip()
