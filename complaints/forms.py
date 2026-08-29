import re

from django import forms
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email

from .models import Complaint, Status


PHONE_RE = re.compile(r"^\+?[0-9\s().-]{7,20}$")


class ComplaintForm(forms.ModelForm):

    class Meta:
        model = Complaint
        fields = [
            "citizen_name",
            "citizen_contact",
            "complaint_type",
            "location",
            "description",
        ]
        widgets = {
            "citizen_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Juan Dela Cruz"}),
            "citizen_contact": forms.TextInput(attrs={"class": "form-control", "placeholder": "email@example.com or +639171234567"}),
            "complaint_type": forms.Select(attrs={"class": "form-select"}),
            "location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Street, barangay, city, or service office"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }

    def clean_citizen_contact(self):
        contact = self.cleaned_data["citizen_contact"].strip()

        try:
            validate_email(contact)
            return contact
        except DjangoValidationError:
            pass

        digits_only = re.sub(r"\D", "", contact)
        if PHONE_RE.match(contact) and 7 <= len(digits_only) <= 15:
            return contact

        raise forms.ValidationError("Enter a valid email address or phone number.")


class StatusUpdateForm(forms.Form):

    new_status = forms.ChoiceField(
        choices=Status.CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    change_reason = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Explain why this status is being changed.",
            }
        )
    )

    def clean_change_reason(self):
        reason = self.cleaned_data["change_reason"].strip()
        if not reason:
            raise forms.ValidationError("Change reason is required.")
        return reason


class SearchFilterForm(forms.Form):

    search = forms.CharField(required=False)
    status = forms.ChoiceField(required=False, choices=[("", "All statuses")] + Status.CHOICES)
    complaint_type = forms.ChoiceField(
        required=False,
        choices=[("", "All types")] + list(Complaint.ComplaintType.choices),
    )
    priority = forms.ChoiceField(
        required=False,
        choices=[("", "All priorities")] + list(Complaint.Priority.choices),
    )


# Backward-friendly alias for older code or notes that still use this name.
ComplaintRegistrationForm = ComplaintForm
