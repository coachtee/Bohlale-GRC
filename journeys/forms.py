from django import forms

from .models import GOAL_CHOICES, InformationRequest


class OnboardingGoalForm(forms.Form):
    goal_type = forms.ChoiceField(
        choices=GOAL_CHOICES,
        widget=forms.RadioSelect,
    )


class OnboardingFrameworkForm(forms.Form):
    framework_id = forms.CharField(widget=forms.HiddenInput)


class InterviewAnswerForm(forms.Form):
    answer_text = forms.CharField(widget=forms.Textarea(attrs={"class": "form-textarea", "rows": 3, "autofocus": True}))


class InformationRequestForm(forms.ModelForm):
    class Meta:
        model = InformationRequest
        fields = ["assigned_to_user", "assigned_role_label", "assigned_email", "question_text"]
        widgets = {
            "assigned_to_user": forms.Select(attrs={"class": "form-select"}),
            "assigned_role_label": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. IT Manager"}),
            "assigned_email": forms.EmailInput(attrs={"class": "form-input", "placeholder": "external@example.com (optional)"}),
            "question_text": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
        }

    def __init__(self, *args, organisation=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organisation is not None:
            from tenancy.models import Membership

            self.fields["assigned_to_user"].queryset = Membership.objects.filter(
                organisation=organisation, is_active=True
            ).values_list("user", flat=True)
            from accounts.models import User

            self.fields["assigned_to_user"].queryset = User.objects.filter(
                id__in=Membership.objects.filter(organisation=organisation, is_active=True).values("user_id")
            )
        self.fields["assigned_to_user"].required = False


class InformationResponseForm(forms.Form):
    response_text = forms.CharField(widget=forms.Textarea(attrs={"class": "form-textarea", "rows": 5, "autofocus": True}))
