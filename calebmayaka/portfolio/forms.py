from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import DashboardUserProfile, Inquiry


class InquiryForm(forms.ModelForm):
    # Honeypot: bots fill it in, humans leave it blank
    website = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'tabindex': '-1',
            'autocomplete': 'off',
            'aria-hidden': 'true',
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inquiry_type'].choices = [('', 'Select inquiry type'), *Inquiry.INQUIRY_TYPE_CHOICES]

    class Meta:
        model = Inquiry
        fields = ['email', 'inquiry_type', 'message']
        widgets = {
            'email': forms.EmailInput(attrs={'id': 'inquiry-email'}),
            'inquiry_type': forms.Select(attrs={'id': 'inquiry-type'}),
            'message': forms.Textarea(attrs={'id': 'inquiry-message', 'rows': 7}),
        }
        labels = {
            'email': 'Email',
            'inquiry_type': 'Inquiry type',
            'message': 'Inquiry',
        }


class DashboardLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'autocomplete': 'username', 'placeholder': 'you@example.com'}),
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'placeholder': 'Password'}),
    )


class DashboardUserCreateForm(forms.Form):
    username = forms.EmailField(label='Email')
    role = forms.ChoiceField(choices=DashboardUserProfile.ROLE_CHOICES, initial=DashboardUserProfile.MANAGER)
    is_active = forms.BooleanField(required=False, initial=True, label='Active account')
    temp_password = forms.CharField(label='Temporary password', min_length=8, widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data['username'].strip().lower()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('A user with this email already exists.')
        return username


class DashboardUserUpdateForm(forms.Form):
    username = forms.EmailField(label='Email')
    role = forms.ChoiceField(choices=DashboardUserProfile.ROLE_CHOICES)
    is_active = forms.BooleanField(required=False, label='Active account')

    def __init__(self, *args, **kwargs):
        self.user_instance = kwargs.pop('user_instance')
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data['username'].strip().lower()
        exists = User.objects.filter(username__iexact=username).exclude(id=self.user_instance.id).exists()
        if exists:
            raise ValidationError('A user with this email already exists.')
        return username


class DashboardPasswordResetForm(forms.Form):
    temp_password = forms.CharField(label='Temporary password', min_length=8, widget=forms.PasswordInput)
