from django import forms


def build_register_form(register_type, data=None, initial=None):
    """Dynamically builds a Django Form from a RegisterType's
    field_schema, so new generic registers need no code changes."""

    fields = {}
    for field_spec in register_type.field_schema:
        field_type = field_spec.get("type", "text")
        label = field_spec.get("label", field_spec["name"])
        required = field_spec.get("required", False)
        if field_type == "textarea":
            widget = forms.Textarea(attrs={"class": "form-textarea", "rows": 3})
            fields[field_spec["name"]] = forms.CharField(label=label, required=required, widget=widget)
        elif field_type == "date":
            widget = forms.DateInput(attrs={"class": "form-input", "type": "date"})
            fields[field_spec["name"]] = forms.DateField(label=label, required=required, widget=widget)
        elif field_type == "select":
            choices = [(c, c) for c in field_spec.get("choices", [])]
            widget = forms.Select(attrs={"class": "form-select"})
            fields[field_spec["name"]] = forms.ChoiceField(label=label, required=required, choices=choices, widget=widget)
        else:
            widget = forms.TextInput(attrs={"class": "form-input"})
            fields[field_spec["name"]] = forms.CharField(label=label, required=required, widget=widget)

    form_class = type("RegisterEntryForm", (forms.Form,), fields)
    return form_class(data=data, initial=initial)
