from django.contrib.auth.models import User
from django.db import models
from django.db.models import JSONField


class Inquiry(models.Model):
    WEBSITE = 'website'
    BACKEND = 'backend'
    AI_AUTOMATION = 'ai_automation'
    CONSULTATION = 'consultation'
    OTHER = 'other'

    INQUIRY_TYPE_CHOICES = [
        (WEBSITE, 'Website or web app'),
        (BACKEND, 'Backend or API'),
        (AI_AUTOMATION, 'AI automation'),
        (CONSULTATION, 'Consultation'),
        (OTHER, 'Other'),
    ]

    email = models.EmailField()
    inquiry_type = models.CharField(max_length=40, choices=INQUIRY_TYPE_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'inquiries'

    def __str__(self):
        return f'{self.get_inquiry_type_display()} from {self.email}'


class DashboardUserProfile(models.Model):
    ADMIN = 'admin'
    MANAGER = 'manager'
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (MANAGER, 'Manager'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dashboard_profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=MANAGER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__username']
        verbose_name = 'Dashboard user profile'
        verbose_name_plural = 'Dashboard user profiles'

    def __str__(self):
        return f'{self.user.username} ({self.get_role_display()})'


# ---------------------------------------------------------------------------
# Portfolio content models
# ---------------------------------------------------------------------------

class SiteProfile(models.Model):
    name = models.CharField(max_length=100)
    initials = models.CharField(max_length=10)
    role = models.CharField(max_length=200)
    headline = models.TextField()
    summary = models.TextField()
    location = models.CharField(max_length=100)
    email = models.EmailField()
    whatsapp_url = models.CharField(max_length=300, blank=True, help_text='Full wa.me URL, e.g. https://wa.me/254798934667')
    availability = models.CharField(max_length=200)
    meta_description = models.TextField()

    class Meta:
        verbose_name = 'Site profile'
        verbose_name_plural = 'Site profile'

    def __str__(self):
        return self.name


class NavItem(models.Model):
    label = models.CharField(max_length=100)
    url_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Django URL name (e.g. "home"). Leave blank if using a raw URL.',
    )
    url = models.CharField(
        max_length=200,
        blank=True,
        help_text='Hard-coded URL (e.g. "/blog/"). Used when url_name is blank.',
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Nav item'
        verbose_name_plural = 'Nav items'

    def __str__(self):
        return self.label


class SocialLink(models.Model):
    label = models.CharField(max_length=100)
    url = models.URLField(max_length=300)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Social link'
        verbose_name_plural = 'Social links'

    def __str__(self):
        return self.label


class Stat(models.Model):
    value = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Stat'
        verbose_name_plural = 'Stats'

    def __str__(self):
        return f'{self.value} — {self.label}'


class Skill(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    tags = JSONField(default=list, help_text='List of tag strings, e.g. ["Django", "Python"]')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'

    def __str__(self):
        return self.title


class TechStack(models.Model):
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Tech stack item'
        verbose_name_plural = 'Tech stack items'

    def __str__(self):
        return self.name


class Project(models.Model):
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text='Unique identifier used in modals (e.g. "client-portal").',
    )
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    description = models.TextField()
    tags = JSONField(default=list)
    impact = models.TextField()
    status = models.CharField(max_length=100)
    link = models.CharField(max_length=300, default='#')
    repo = models.CharField(max_length=300, default='#')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'

    def __str__(self):
        return self.title

    @property
    def id(self):
        return self.slug


class Experience(models.Model):
    role = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    period = models.CharField(max_length=100)
    description = models.TextField()
    achievements = JSONField(default=list, help_text='List of achievement strings.')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Experience'
        verbose_name_plural = 'Experience'

    def __str__(self):
        return f'{self.role} at {self.company}'


class CaseStudy(models.Model):
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text='Unique identifier used in modals (e.g. "django-portfolio").',
    )
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    role = models.CharField(max_length=200)
    description = models.TextField()
    problem = models.TextField()
    solution = models.TextField()
    results = JSONField(default=list)
    tags = JSONField(default=list)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Case study'
        verbose_name_plural = 'Case studies'

    def __str__(self):
        return self.title

    @property
    def id(self):
        return self.slug


class Testimonial(models.Model):
    quote = models.TextField()
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'

    def __str__(self):
        return f'{self.name} — {self.title}'
