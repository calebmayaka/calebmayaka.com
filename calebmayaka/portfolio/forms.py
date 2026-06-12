from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import (
    CaseStudy,
    DashboardUserProfile,
    Experience,
    Inquiry,
    NavItem,
    Project,
    Skill,
    SiteProfile,
    SocialLink,
    Stat,
    TechStack,
    Testimonial,
)


class SubscribeForm(forms.Form):
    email = forms.EmailField(
        label='',
        widget=forms.EmailInput(attrs={
            'placeholder': 'you@example.com',
            'autocomplete': 'email',
        }),
    )
    # Honeypot — bots fill this in, humans leave it blank
    website = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'tabindex': '-1',
            'autocomplete': 'off',
            'aria-hidden': 'true',
            'style': 'display:none',
        }),
    )

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()


class DigestForm(forms.Form):
    subject = forms.CharField(
        max_length=200,
        label='Subject line',
        widget=forms.TextInput(attrs={'placeholder': 'New on the blog — May 2026'}),
    )
    post_ids = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        label='Posts to include',
    )

    def __init__(self, *args, posts=None, **kwargs):
        super().__init__(*args, **kwargs)
        if posts:
            self.fields['post_ids'].choices = [
                (post.pk, f'{post.title} ({post.date.strftime("%b %d, %Y")})')
                for post in posts
            ]


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
        widget=forms.EmailInput(attrs={'autocomplete': 'username'}),
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
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


class SmtpTestForm(forms.Form):
    recipient = forms.EmailField(label='Recipient')
    subject = forms.CharField(
        label='Subject',
        max_length=120,
        initial='calebmayaka.com SMTP test',
    )
    message = forms.CharField(
        label='Message',
        initial='This is a test email from the calebmayaka.com /dev dashboard.',
        widget=forms.Textarea(attrs={'rows': 5}),
    )


class ListTextareaFormMixin:
    list_fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.list_fields:
            if field_name not in self.fields:
                continue
            self.fields[field_name] = forms.CharField(
                required=False,
                widget=forms.Textarea(attrs={'rows': 5}),
                help_text='Enter one item per line.',
            )
            if self.instance and self.instance.pk:
                value = getattr(self.instance, field_name, [])
                if isinstance(value, list):
                    self.initial[field_name] = '\n'.join(str(item) for item in value)

    def clean(self):
        cleaned_data = super().clean()
        for field_name in self.list_fields:
            value = cleaned_data.get(field_name, '')
            if isinstance(value, list):
                cleaned_data[field_name] = value
                continue
            cleaned_data[field_name] = [
                item.strip()
                for item in str(value).splitlines()
                if item.strip()
            ]
        return cleaned_data


class AutoSlugFormMixin:
    slug_source_field = 'title'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'slug' in self.fields:
            self.fields['slug'].required = False
            self.fields['slug'].help_text = 'Leave blank to generate from the title.'

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        if slug:
            return slugify(slug)
        source = self.cleaned_data.get(self.slug_source_field, '')
        return slugify(source)


class SiteProfileForm(forms.ModelForm):
    class Meta:
        model = SiteProfile
        fields = [
            'name',
            'initials',
            'role',
            'headline',
            'summary',
            'location',
            'email',
            'whatsapp_url',
            'availability',
            'meta_description',
        ]
        widgets = {
            'headline': forms.Textarea(attrs={'rows': 4}),
            'summary': forms.Textarea(attrs={'rows': 5}),
            'meta_description': forms.Textarea(attrs={'rows': 4}),
        }


class NavItemForm(forms.ModelForm):
    class Meta:
        model = NavItem
        fields = ['label', 'url_name', 'url', 'order']


class SocialLinkForm(forms.ModelForm):
    class Meta:
        model = SocialLink
        fields = ['label', 'url', 'order']


class StatForm(forms.ModelForm):
    class Meta:
        model = Stat
        fields = ['value', 'label', 'order']


class SkillForm(ListTextareaFormMixin, forms.ModelForm):
    list_fields = ('tags',)

    class Meta:
        model = Skill
        fields = ['title', 'description', 'tags', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class TechStackForm(forms.ModelForm):
    class Meta:
        model = TechStack
        fields = ['name', 'order']


class ProjectForm(AutoSlugFormMixin, ListTextareaFormMixin, forms.ModelForm):
    list_fields = ('tags',)

    class Meta:
        model = Project
        fields = ['title', 'slug', 'category', 'description', 'tags', 'impact', 'status', 'link', 'repo', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'impact': forms.Textarea(attrs={'rows': 4}),
        }


class ExperienceForm(ListTextareaFormMixin, forms.ModelForm):
    list_fields = ('achievements',)

    class Meta:
        model = Experience
        fields = ['role', 'company', 'period', 'description', 'achievements', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class CaseStudyForm(AutoSlugFormMixin, ListTextareaFormMixin, forms.ModelForm):
    list_fields = ('results', 'tags')

    class Meta:
        model = CaseStudy
        fields = [
            'title',
            'slug',
            'category',
            'duration',
            'role',
            'description',
            'problem',
            'solution',
            'results',
            'tags',
            'order',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'problem': forms.Textarea(attrs={'rows': 5}),
            'solution': forms.Textarea(attrs={'rows': 5}),
        }


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['quote', 'name', 'title', 'order']
        widgets = {
            'quote': forms.Textarea(attrs={'rows': 5}),
        }
