from django import forms


class SignatureForm(forms.Form):
    decision = forms.ChoiceField(
        choices=[("approved", "Approve"), ("rejected", "Reject")],
        widget=forms.RadioSelect,
    )
    typed_signature = forms.CharField(
        label="Type your full name to sign",
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Your full name"}),
    )
    consent = forms.BooleanField(
        label="I confirm this typed signature constitutes my electronic signature and that I have reviewed the document above.",
        required=True,
    )

    def __init__(self, *args, expected_name="", **kwargs):
        self.expected_name = expected_name
        super().__init__(*args, **kwargs)

    def clean_typed_signature(self):
        value = self.cleaned_data["typed_signature"].strip()
        if self.expected_name and value.lower() != self.expected_name.strip().lower():
            raise forms.ValidationError("Please type your full name exactly as it appears on your profile to sign.")
        return value
