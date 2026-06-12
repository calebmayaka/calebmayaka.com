import logging
from functools import wraps
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.mail import EmailMultiAlternatives, get_connection, send_mail
from django.db import connection
from django.db.models import Count, Q, Sum
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from blogcms.models import BlogPostPage, BlogVisit

from .context_processors import get_site_chrome
from .forms import (
    CaseStudyForm,
    DashboardLoginForm,
    DashboardPasswordResetForm,
    DashboardUserCreateForm,
    DashboardUserUpdateForm,
    DigestForm,
    ExperienceForm,
    InquiryForm,
    NavItemForm,
    ProjectForm,
    SmtpTestForm,
    SiteProfileForm,
    SkillForm,
    SocialLinkForm,
    StatForm,
    SubscribeForm,
    TechStackForm,
    TestimonialForm,
)
from .models import (
    CaseStudy,
    DashboardUserProfile,
    DigestLog,
    Experience,
    Inquiry,
    NavItem,
    Project,
    Skill,
    SiteProfile,
    SocialLink,
    Stat,
    Subscriber,
    TechStack,
    Testimonial,
)


def _get_profile_name():
    p = get_site_chrome().get('profile')
    return p.name if p else ''


def base_context(active):
    return {
        'active': active,
    }


def get_dashboard_profile(user):
    try:
        return user.dashboard_profile
    except DashboardUserProfile.DoesNotExist:
        return None


def rate_limit_client_ip(group, request):
    for header in ('HTTP_CF_CONNECTING_IP', 'HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR'):
        value = request.META.get(header, '').strip()
        if value:
            return value.split(',', 1)[0].strip()
    return 'unknown'


def _safe_referer(request, fallback='/blog/'):
    """Return the HTTP Referer header only when it points to the same host.

    HTTP_REFERER is user-controlled; passing it straight to redirect() is an
    open-redirect vulnerability.  This helper validates it with Django's own
    utility (already used in the login view) before using it.
    """
    referer = request.META.get('HTTP_REFERER', fallback)
    if not url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}):
        return fallback
    return referer


def dashboard_login_redirect(request):
    query = urlencode({'next': request.get_full_path()})
    return redirect(f"{reverse('dashboard_login')}?{query}")


def dashboard_access_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return dashboard_login_redirect(request)
        if not request.user.is_active:
            logout(request)
            messages.error(request, 'Your account is inactive.')
            return redirect('dashboard_login')

        dashboard_profile = get_dashboard_profile(request.user)
        if not dashboard_profile or dashboard_profile.role not in {DashboardUserProfile.ADMIN, DashboardUserProfile.MANAGER}:
            logout(request)
            messages.error(request, 'Your account is not authorized for the dashboard.')
            return redirect('dashboard_login')

        request.dashboard_profile = dashboard_profile
        return view_func(request, *args, **kwargs)

    return wrapped


def admin_role_required(view_func):
    @dashboard_access_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.dashboard_profile.role != DashboardUserProfile.ADMIN:
            messages.error(request, 'Only admins can access this dashboard area.')
            return redirect('dev')
        return view_func(request, *args, **kwargs)

    return wrapped


def dashboard_context(request, active):
    inquiries = Inquiry.objects.all()
    unread_count = inquiries.filter(is_read=False).count()
    total_inquiries = inquiries.count()
    read_count = inquiries.filter(is_read=True).count()
    response_rate = round((read_count / total_inquiries) * 100) if total_inquiries else 0
    dashboard_profile = getattr(request, 'dashboard_profile', None) or get_dashboard_profile(request.user)

    return {
        **base_context('dashboard'),
        'dashboard_active': active,
        'total_inquiries': total_inquiries,
        'unread_count': unread_count,
        'read_count': read_count,
        'response_rate': response_rate,
        'session_timeout_seconds': settings.SESSION_COOKIE_AGE,
        'dashboard_role': dashboard_profile.role if dashboard_profile else '',
        'dashboard_role_label': dashboard_profile.get_role_display() if dashboard_profile else '',
        'is_dashboard_admin': (dashboard_profile.role == DashboardUserProfile.ADMIN) if dashboard_profile else False,
    }


CONTENT_REGISTRY = {
    'profile': {
        'model': SiteProfile,
        'form': SiteProfileForm,
        'label': 'Site Profile',
        'plural': 'Site Profile',
        'description': 'Identity, contact, headline, and metadata for the public site.',
        'group': 'Site',
        'primary_field': 'name',
        'secondary_fields': ['role', 'email'],
        'badge_field': 'location',
        'side_fields': ['initials', 'email', 'location', 'whatsapp_url', 'availability'],
        'list_fields': ['name', 'role', 'email', 'location'],
        'empty_label': 'No site profile',
        'singleton': True,
        'protected_delete': True,
    },
    'nav': {
        'model': NavItem,
        'form': NavItemForm,
        'label': 'Nav Item',
        'plural': 'Navigation',
        'description': 'Primary navigation labels, named routes, custom URLs, and order.',
        'group': 'Site',
        'primary_field': 'label',
        'secondary_fields': ['url_name', 'url'],
        'badge_field': 'order',
        'side_fields': ['url_name', 'url', 'order'],
        'list_fields': ['label', 'url_name', 'url', 'order'],
        'empty_label': 'No navigation items',
    },
    'socials': {
        'model': SocialLink,
        'form': SocialLinkForm,
        'label': 'Social Link',
        'plural': 'Social Links',
        'description': 'External profile and contact links shown across the site.',
        'group': 'Site',
        'primary_field': 'label',
        'secondary_fields': ['url'],
        'badge_field': 'order',
        'side_fields': ['url', 'order'],
        'list_fields': ['label', 'url', 'order'],
        'empty_label': 'No social links',
    },
    'stats': {
        'model': Stat,
        'form': StatForm,
        'label': 'Stat',
        'plural': 'Stats',
        'description': 'Short proof points and metrics displayed on public pages.',
        'group': 'Homepage',
        'primary_field': 'label',
        'secondary_fields': ['value'],
        'badge_field': 'order',
        'side_fields': ['value', 'order'],
        'list_fields': ['value', 'label', 'order'],
        'empty_label': 'No stats',
    },
    'skills': {
        'model': Skill,
        'form': SkillForm,
        'label': 'Skill',
        'plural': 'Skills',
        'description': 'Capabilities, descriptions, tags, and display order.',
        'group': 'Homepage',
        'primary_field': 'title',
        'secondary_fields': ['description'],
        'badge_field': 'order',
        'side_fields': ['tags', 'order'],
        'list_fields': ['title', 'description', 'order'],
        'empty_label': 'No skills',
    },
    'tech-stack': {
        'model': TechStack,
        'form': TechStackForm,
        'label': 'Tech Stack Item',
        'plural': 'Tech Stack',
        'description': 'Technology names shown in the rotating site stack.',
        'group': 'Homepage',
        'primary_field': 'name',
        'secondary_fields': [],
        'badge_field': 'order',
        'side_fields': ['order'],
        'list_fields': ['name', 'order'],
        'empty_label': 'No tech stack items',
    },
    'projects': {
        'model': Project,
        'form': ProjectForm,
        'label': 'Project',
        'plural': 'Projects',
        'description': 'Portfolio project cards, links, tags, and status copy.',
        'group': 'Work',
        'primary_field': 'title',
        'secondary_fields': ['category', 'status'],
        'badge_field': 'order',
        'side_fields': ['slug', 'category', 'status', 'link', 'repo', 'tags', 'order'],
        'list_fields': ['title', 'category', 'status', 'order'],
        'empty_label': 'No projects',
    },
    'experience': {
        'model': Experience,
        'form': ExperienceForm,
        'label': 'Experience',
        'plural': 'Experience',
        'description': 'Professional experience entries and achievement lists.',
        'group': 'Work',
        'primary_field': 'role',
        'secondary_fields': ['company', 'period'],
        'badge_field': 'order',
        'side_fields': ['company', 'period', 'achievements', 'order'],
        'list_fields': ['role', 'company', 'period', 'order'],
        'empty_label': 'No experience',
    },
    'case-studies': {
        'model': CaseStudy,
        'form': CaseStudyForm,
        'label': 'Case Study',
        'plural': 'Case Studies',
        'description': 'Detailed case study content, results, tags, and ordering.',
        'group': 'Work',
        'primary_field': 'title',
        'secondary_fields': ['category', 'duration'],
        'badge_field': 'order',
        'side_fields': ['slug', 'category', 'duration', 'role', 'results', 'tags', 'order'],
        'list_fields': ['title', 'category', 'duration', 'order'],
        'empty_label': 'No case studies',
    },
    'testimonials': {
        'model': Testimonial,
        'form': TestimonialForm,
        'label': 'Testimonial',
        'plural': 'Testimonials',
        'description': 'Quotes and attribution displayed on the site.',
        'group': 'Homepage',
        'primary_field': 'name',
        'secondary_fields': ['title'],
        'badge_field': 'order',
        'side_fields': ['name', 'title', 'order'],
        'list_fields': ['name', 'title', 'order'],
        'empty_label': 'No testimonials',
    },
}


def get_content_config(content_type):
    config = CONTENT_REGISTRY.get(content_type)
    if not config:
        raise Http404('Content type not found.')
    return config


def content_queryset(config):
    queryset = config['model'].objects.all()
    field_names = {field.name for field in config['model']._meta.fields}
    if 'order' in field_names:
        return queryset.order_by('order', 'pk')
    return queryset.order_by('pk')


def content_item_label(item):
    return str(item)


def content_field_label(field_name):
    return field_name.replace('_', ' ').title()


def content_field_value(item, field_name):
    value = getattr(item, field_name, '')
    if isinstance(value, list):
        return ', '.join(str(item) for item in value)
    if value is None:
        return ''
    return value


def content_navigation(active_type=None):
    groups = []
    group_index = {}
    for key, config in CONTENT_REGISTRY.items():
        group_name = config.get('group', 'Content')
        if group_name not in group_index:
            group_index[group_name] = {
                'label': group_name,
                'items': [],
            }
            groups.append(group_index[group_name])
        queryset = content_queryset(config)
        group_index[group_name]['items'].append({
            'key': key,
            'label': config['plural'],
            'count': queryset.count(),
            'active': key == active_type,
            'can_create': not (config.get('singleton') and queryset.exists()),
        })

    groups.append({
        'label': 'Blog',
        'items': [{
            'key': 'blog',
            'label': 'Wagtail CMS',
            'count': BlogPostPage.objects.count(),
            'active': False,
            'url': '/cms/',
            'can_create': False,
        }],
    })
    return groups


def content_summary_item(key, config):
    queryset = content_queryset(config)
    latest = queryset.first()
    return {
        'key': key,
        'label': config['label'],
        'plural': config['plural'],
        'group': config.get('group', 'Content'),
        'description': config.get('description', ''),
        'count': queryset.count(),
        'latest': latest,
        'latest_label': content_item_label(latest) if latest else '',
        'can_create': not (config.get('singleton') and queryset.exists()),
    }


def content_row(item, config):
    secondary = []
    for field_name in config.get('secondary_fields', []):
        value = content_field_value(item, field_name)
        if value:
            secondary.append({
                'label': content_field_label(field_name),
                'value': value,
            })
    badge_field = config.get('badge_field')
    badge_value = content_field_value(item, badge_field) if badge_field else ''
    return {
        'item': item,
        'label': content_field_value(item, config.get('primary_field')) or content_item_label(item),
        'secondary': secondary,
        'badge': badge_value,
        'badge_label': content_field_label(badge_field) if badge_field else '',
    }


def split_content_form_fields(form, config):
    side_field_names = set(config.get('side_fields', []))
    main_fields = []
    side_fields = []
    for field in form:
        if field.name in side_field_names:
            side_fields.append(field)
        else:
            main_fields.append(field)
    return main_fields, side_fields


def content_row_values(item, fields):
    return [
        {
            'label': field.replace('_', ' ').title(),
            'value': getattr(item, field, ''),
        }
        for field in fields
    ]


def content_overview_items():
    items = []
    for key, config in CONTENT_REGISTRY.items():
        items.append(content_summary_item(key, config))
    return items


def mask_secret(value):
    if not value:
        return 'Not set'
    if len(value) <= 4:
        return '*' * len(value)
    return f"{value[:2]}{'*' * max(len(value) - 4, 4)}{value[-2:]}"


def setting_status(value, healthy_label='Configured', missing_label='Missing'):
    if value:
        return {'state': 'healthy', 'status_label': healthy_label}
    return {'state': 'missing', 'status_label': missing_label}


def smtp_config_snapshot():
    password_set = bool(getattr(settings, 'EMAIL_HOST_PASSWORD', ''))
    host_set = bool(getattr(settings, 'EMAIL_HOST', ''))
    user_set = bool(getattr(settings, 'EMAIL_HOST_USER', ''))
    backend = getattr(settings, 'EMAIL_BACKEND', '')
    is_smtp_backend = backend == 'django.core.mail.backends.smtp.EmailBackend'
    ready = all([password_set, host_set, user_set, is_smtp_backend])

    return {
        'ready': ready,
        'status': 'healthy' if ready else 'warning',
        'backend': backend,
        'host': getattr(settings, 'EMAIL_HOST', '') or 'Not set',
        'port': getattr(settings, 'EMAIL_PORT', ''),
        'username': mask_secret(getattr(settings, 'EMAIL_HOST_USER', '')),
        'password': 'Set' if password_set else 'Not set',
        'use_tls': getattr(settings, 'EMAIL_USE_TLS', False),
        'use_ssl': getattr(settings, 'EMAIL_USE_SSL', False),
        'default_from': getattr(settings, 'DEFAULT_FROM_EMAIL', ''),
        'notify_email': getattr(settings, 'NOTIFY_EMAIL', ''),
    }


BLOG_ANALYTICS_RANGES = {
    '7d': 7,
    '30d': 30,
    '90d': 90,
}


def blog_visit_table_exists():
    return BlogVisit._meta.db_table in connection.introspection.table_names()


def blog_analytics_summary(days=7):
    if not blog_visit_table_exists():
        return {
            'days': days,
            'total_visits': 0,
            'unique_ips': 0,
            'bot_visits': 0,
            'top_country': None,
            'top_post': None,
            'is_available': False,
        }

    since = timezone.now() - timezone.timedelta(days=days)
    visits = BlogVisit.objects.filter(visited_at__gte=since)
    top_country = (
        visits.exclude(country_name='')
        .values('country_name', 'country_code')
        .annotate(count=Count('id'))
        .order_by('-count', 'country_name')
        .first()
    )
    top_post = (
        visits.values('post__title')
        .annotate(count=Count('id'))
        .order_by('-count', 'post__title')
        .first()
    )
    return {
        'days': days,
        'total_visits': visits.count(),
        'unique_ips': visits.values('ip_address').distinct().count(),
        'bot_visits': visits.filter(is_likely_bot=True).count(),
        'top_country': top_country,
        'top_post': top_post,
        'is_available': True,
    }


def content_status_snapshot():
    latest_posts = (
        BlogPostPage.objects
        .order_by('-date', '-first_published_at')[:5]
    )
    top_posts = (
        BlogPostPage.objects.live().public()
        .order_by('-view_count')
        .select_related('cover_image')[:5]
    )
    total_views = BlogPostPage.objects.aggregate(t=Sum('view_count'))['t'] or 0
    return {
        'counts': [
            {'label': 'Blog posts', 'count': BlogPostPage.objects.count(), 'url': '/cms/'},
            {'label': 'Projects', 'count': Project.objects.count(), 'url': '/dev/content/projects/'},
            {'label': 'Case studies', 'count': CaseStudy.objects.count(), 'url': '/dev/content/case-studies/'},
            {'label': 'Skills', 'count': Skill.objects.count(), 'url': '/dev/content/skills/'},
            {'label': 'Experience', 'count': Experience.objects.count(), 'url': '/dev/content/experience/'},
            {'label': 'Testimonials', 'count': Testimonial.objects.count(), 'url': '/dev/content/testimonials/'},
            {'label': 'Site profiles', 'count': SiteProfile.objects.count(), 'url': '/dev/content/profile/'},
        ],
        'latest_posts': latest_posts,
        'published_posts': BlogPostPage.objects.live().public().count(),
        'draft_posts': BlogPostPage.objects.filter(live=False).count(),
        'total_views': total_views,
        'top_posts': top_posts,
        'analytics': blog_analytics_summary(7),
    }


def health_checks():
    allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
    csrf_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
    public_url = getattr(settings, 'PUBLIC_SITE_URL', '')
    wagtail_url = getattr(settings, 'WAGTAILADMIN_BASE_URL', '')
    smtp = smtp_config_snapshot()

    return [
        {
            'label': 'Debug mode',
            'value': 'Off' if not settings.DEBUG else 'On',
            'state': 'healthy' if not settings.DEBUG else 'warning',
            'detail': 'Production-safe' if not settings.DEBUG else 'Disable before public production traffic.',
        },
        {
            'label': 'Allowed hosts',
            'value': ', '.join(allowed_hosts) if allowed_hosts else 'Not set',
            **setting_status(allowed_hosts),
            'detail': 'Hosts Django will serve.',
        },
        {
            'label': 'CSRF trusted origins',
            'value': ', '.join(csrf_origins) if csrf_origins else 'Not set',
            **setting_status(csrf_origins),
            'detail': 'Origins allowed to submit protected forms.',
        },
        {
            'label': 'Public site URL',
            'value': public_url or 'Not set',
            **setting_status(public_url),
            'detail': 'Canonical public URL used by the app.',
        },
        {
            'label': 'Wagtail admin URL',
            'value': wagtail_url or 'Not set',
            **setting_status(wagtail_url),
            'detail': 'CMS base URL for Wagtail.',
        },
        {
            'label': 'Secure cookies',
            'value': 'Enabled' if settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE else 'Review',
            'state': 'healthy' if settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE else 'warning',
            'detail': 'Session and CSRF cookies should be HTTPS-only.',
        },
        {
            'label': 'SSL redirect',
            'value': 'Enabled' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'Off',
            'state': 'healthy' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'warning',
            'detail': 'IIS may already enforce HTTPS; review before changing.',
        },
        {
            'label': 'Email backend',
            'value': smtp['backend'] or 'Not set',
            'state': smtp['status'],
            'detail': 'SMTP is ready.' if smtp['ready'] else 'SMTP settings need attention.',
        },
    ]


def month_starts(month_count=7):
    today = timezone.localdate()
    months = []
    for offset in range(month_count - 1, -1, -1):
        month = today.month - offset
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        months.append(today.replace(year=year, month=month, day=1))
    return months


@ratelimit(key='ip', rate='3/h', method='POST', block=False)
def home(request):
    was_limited = getattr(request, 'limited', False)
    inquiry_form = InquiryForm(request.POST or None)
    if request.method == 'POST':
        if was_limited:
            messages.error(request, 'Too many submissions. Please wait an hour before trying again.')
            return redirect('home')
        if inquiry_form.is_valid():
            if inquiry_form.cleaned_data.get('website'):
                messages.success(request, 'Your inquiry has been sent successfully.')
                return redirect('home')
            inquiry_form.save()
            messages.success(request, 'Your inquiry has been sent successfully.')
            return redirect('home')

    _profile = get_site_chrome().get('profile')
    context = {
        **base_context('home'),
        'page_title': f"{_profile.name} | {_profile.role}" if _profile else '',
        'stats': Stat.objects.order_by('order'),
        'skills': Skill.objects.order_by('order'),
        'projects': Project.objects.order_by('order')[:3],
        'blog_posts': (
            BlogPostPage.objects.live()
            .public()
            .order_by('-date', '-first_published_at')
        ),
        'experience': Experience.objects.order_by('order'),
        'testimonials': Testimonial.objects.order_by('order'),
        'tech_stack': list(TechStack.objects.order_by('order').values_list('name', flat=True)),
        'inquiry_form': inquiry_form,
    }
    return render(request, 'portfolio/home.html', context)


def about(request):
    context = {
        **base_context('about'),
        'page_title': f"About | {_get_profile_name()}",
        'skills': Skill.objects.order_by('order'),
        'tech_stack': list(TechStack.objects.order_by('order').values_list('name', flat=True)),
        'stats': Stat.objects.order_by('order'),
    }
    return render(request, 'portfolio/about.html', context)


def experience(request):
    context = {
        **base_context('experience'),
        'page_title': f"Experience | {_get_profile_name()}",
        'experience': Experience.objects.order_by('order'),
        'tech_stack': list(TechStack.objects.order_by('order').values_list('name', flat=True)),
    }
    return render(request, 'portfolio/experience.html', context)


def projects(request):
    context = {
        **base_context('projects'),
        'page_title': f"Projects | {_get_profile_name()}",
        'projects': Project.objects.order_by('order'),
    }
    return render(request, 'portfolio/projects.html', context)


def case_studies(request):
    context = {
        **base_context('case_studies'),
        'page_title': f"Case Studies | {_get_profile_name()}",
        'case_studies': CaseStudy.objects.order_by('order'),
    }
    return render(request, 'portfolio/case_studies.html', context)


@ratelimit(key=rate_limit_client_ip, rate='5/m', method='POST', block=False)
def dashboard_login(request):
    next_url = request.GET.get('next') or request.POST.get('next') or reverse('dev')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = reverse('dev')

    if request.user.is_authenticated and request.user.is_active:
        dashboard_profile = get_dashboard_profile(request.user)
        if dashboard_profile and dashboard_profile.role in {DashboardUserProfile.ADMIN, DashboardUserProfile.MANAGER}:
            return redirect(next_url)

    form = DashboardLoginForm(request, data=request.POST or None)
    if request.method == 'POST' and getattr(request, 'limited', False):
        messages.error(request, 'Too many login attempts. Please wait before trying again.')
        return render(request, 'portfolio/dashboard_login.html', {
            **base_context('dashboard'),
            'page_title': f"Login | {_get_profile_name()}",
            'form': form,
            'next_url': next_url,
        })

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        dashboard_profile = get_dashboard_profile(user)
        if not user.is_active:
            messages.error(request, 'Your account is inactive.')
        elif not dashboard_profile or dashboard_profile.role not in {DashboardUserProfile.ADMIN, DashboardUserProfile.MANAGER}:
            messages.error(request, 'Your account is not authorized for dashboard access.')
        else:
            login(request, user)
            return redirect(next_url)

    context = {
        **base_context('dashboard'),
        'page_title': f"Login | {_get_profile_name()}",
        'form': form,
        'next_url': next_url,
    }
    return render(request, 'portfolio/dashboard_login.html', context)


@dashboard_access_required
def dev_overview(request):
    inquiries = Inquiry.objects.all()
    monthly_counts = {}
    for inquiry in inquiries:
        month_key = timezone.localtime(inquiry.created_at).date().replace(day=1)
        monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
    monthly_activity = []
    highest_month = 1
    for month_start in month_starts():
        count = monthly_counts.get(month_start, 0)
        highest_month = max(highest_month, count)
        monthly_activity.append({
            'label': month_start.strftime('%b'),
            'count': count,
        })
    for item in monthly_activity:
        item['height'] = max(8, round((item['count'] / highest_month) * 100))

    inquiry_counts = {
        item['inquiry_type']: item['count']
        for item in inquiries.values('inquiry_type').annotate(count=Count('id'))
    }
    type_breakdown = []
    total_inquiries = inquiries.count() or 1
    for inquiry_type, label in Inquiry.INQUIRY_TYPE_CHOICES:
        count = inquiry_counts.get(inquiry_type, 0)
        type_breakdown.append({
            'label': label,
            'count': count,
            'percent': round((count / total_inquiries) * 100),
        })

    context = {
        **dashboard_context(request, 'overview'),
        'page_title': f"Dashboard | {_get_profile_name()}",
        'latest_inquiries': inquiries[:5],
        'monthly_activity': monthly_activity,
        'type_breakdown': type_breakdown,
        'consultation_count': inquiries.filter(inquiry_type=Inquiry.CONSULTATION).count(),
        'website_count': inquiries.filter(inquiry_type=Inquiry.WEBSITE).count(),
        'smtp_config': smtp_config_snapshot(),
        'content_status': content_status_snapshot(),
        'health_checks': health_checks()[:4],
    }
    return render(request, 'portfolio/dashboard.html', context)


@admin_role_required
def blog_analytics_dashboard(request):
    range_key = request.GET.get('range', '7d')
    if range_key not in BLOG_ANALYTICS_RANGES:
        range_key = '7d'
    days = BLOG_ANALYTICS_RANGES[range_key]
    analytics_available = blog_visit_table_exists()
    if not analytics_available:
        messages.warning(
            request,
            'Blog analytics storage is not ready yet. Run database migrations to enable visit logs.',
        )
        context = {
            **dashboard_context(request, 'blog_analytics'),
            'page_title': f"Blog Analytics | {_get_profile_name()}",
            'range_key': range_key,
            'range_options': [
                {'key': key, 'label': f'Last {value} days'}
                for key, value in BLOG_ANALYTICS_RANGES.items()
            ],
            'post_filter': '',
            'country_filter': '',
            'search_query': '',
            'filter_query': '',
            'posts': BlogPostPage.objects.live().public().order_by('-date', '-first_published_at'),
            'countries': [],
            'kpis': {
                'total_visits': 0,
                'unique_ips': 0,
                'bot_visits': 0,
                'top_country': None,
            },
            'top_posts': [],
            'top_countries': [],
            'top_cities': [],
            'page_obj': [],
            'paginator': None,
            'analytics_available': False,
        }
        return render(request, 'portfolio/blog_analytics.html', context)

    since = timezone.now() - timezone.timedelta(days=days)

    visits = (
        BlogVisit.objects.select_related('post')
        .filter(visited_at__gte=since)
        .order_by('-visited_at')
    )
    range_visits = visits

    post_filter = request.GET.get('post', '').strip()
    country_filter = request.GET.get('country', '').strip()
    search_query = request.GET.get('q', '').strip()

    if post_filter.isdigit():
        visits = visits.filter(post_id=int(post_filter))
    if country_filter:
        visits = visits.filter(country_code__iexact=country_filter)
    if search_query:
        visits = visits.filter(
            Q(ip_address__icontains=search_query)
            | Q(city__icontains=search_query)
            | Q(region__icontains=search_query)
            | Q(country_name__icontains=search_query)
            | Q(user_agent__icontains=search_query)
            | Q(referer__icontains=search_query)
            | Q(post__title__icontains=search_query)
        )

    top_country = (
        visits.exclude(country_name='')
        .values('country_name', 'country_code')
        .annotate(count=Count('id'))
        .order_by('-count', 'country_name')
        .first()
    )
    top_posts = (
        visits.values('post_id', 'post__title')
        .annotate(count=Count('id'))
        .order_by('-count', 'post__title')[:10]
    )
    top_countries = (
        visits.exclude(country_name='')
        .values('country_name', 'country_code')
        .annotate(count=Count('id'))
        .order_by('-count', 'country_name')[:10]
    )
    top_cities = (
        visits.exclude(city='')
        .values('city', 'region', 'country_name')
        .annotate(count=Count('id'))
        .order_by('-count', 'city')[:10]
    )

    paginator = Paginator(visits, 50)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)

    filter_query = request.GET.copy()
    filter_query.pop('page', None)

    context = {
        **dashboard_context(request, 'blog_analytics'),
        'page_title': f"Blog Analytics | {_get_profile_name()}",
        'range_key': range_key,
        'range_options': [
            {'key': key, 'label': f'Last {value} days'}
            for key, value in BLOG_ANALYTICS_RANGES.items()
        ],
        'post_filter': post_filter,
        'country_filter': country_filter,
        'search_query': search_query,
        'filter_query': filter_query.urlencode(),
        'posts': BlogPostPage.objects.live().public().order_by('-date', '-first_published_at'),
        'countries': (
            range_visits.exclude(country_code='')
            .values('country_code', 'country_name')
            .annotate(count=Count('id'))
            .order_by('country_name', 'country_code')
        ),
        'kpis': {
            'total_visits': visits.count(),
            'unique_ips': visits.values('ip_address').distinct().count(),
            'bot_visits': visits.filter(is_likely_bot=True).count(),
            'top_country': top_country,
        },
        'top_posts': top_posts,
        'top_countries': top_countries,
        'top_cities': top_cities,
        'page_obj': page_obj,
        'paginator': paginator,
        'analytics_available': True,
    }
    return render(request, 'portfolio/blog_analytics.html', context)


@dashboard_access_required
def inquiry_dashboard(request):
    inquiries = Inquiry.objects.all()
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'all')
    type_filter = request.GET.get('type', 'all')

    if search_query:
        inquiries = inquiries.filter(Q(email__icontains=search_query) | Q(message__icontains=search_query))
    if status_filter == 'unread':
        inquiries = inquiries.filter(is_read=False)
    elif status_filter == 'read':
        inquiries = inquiries.filter(is_read=True)
    if type_filter != 'all':
        inquiries = inquiries.filter(inquiry_type=type_filter)

    context = {
        **dashboard_context(request, 'inquiries'),
        'page_title': f"Inquiries | {_get_profile_name()}",
        'inquiries': inquiries,
        'search_query': search_query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'inquiry_types': Inquiry.INQUIRY_TYPE_CHOICES,
    }
    return render(request, 'portfolio/inquiries.html', context)


@dashboard_access_required
def inquiry_detail(request, inquiry_id):
    inquiry = get_object_or_404(Inquiry, id=inquiry_id)
    context = {
        **dashboard_context(request, 'inquiries'),
        'page_title': f"Inquiry Detail | {_get_profile_name()}",
        'inquiry': inquiry,
    }
    return render(request, 'portfolio/inquiry_detail.html', context)


@admin_role_required
def smtp_test(request):
    form = SmtpTestForm(request.POST or None)
    smtp_config = smtp_config_snapshot()

    if request.method == 'POST' and form.is_valid():
        try:
            send_mail(
                form.cleaned_data['subject'],
                form.cleaned_data['message'],
                settings.DEFAULT_FROM_EMAIL,
                [form.cleaned_data['recipient']],
                fail_silently=False,
            )
            messages.success(request, f"Test email sent to {form.cleaned_data['recipient']}.")
            return redirect('dev_smtp')
        except Exception:
            messages.error(request, 'SMTP test failed. Review the configured host, username, password, and port.')

    context = {
        **dashboard_context(request, 'smtp'),
        'page_title': f"SMTP Test | {_get_profile_name()}",
        'form': form,
        'smtp_config': smtp_config,
    }
    return render(request, 'portfolio/dev_smtp.html', context)


@dashboard_access_required
def site_health(request):
    context = {
        **dashboard_context(request, 'health'),
        'page_title': f"Site Health | {_get_profile_name()}",
        'health_checks': health_checks(),
        'smtp_config': smtp_config_snapshot(),
        'content_status': content_status_snapshot(),
    }
    return render(request, 'portfolio/dev_health.html', context)


@admin_role_required
def content_overview(request):
    context = {
        **dashboard_context(request, 'content'),
        'page_title': f"Content | {_get_profile_name()}",
        'content_nav_groups': content_navigation(),
        'content_items': content_overview_items(),
        'blog_status': content_status_snapshot(),
    }
    return render(request, 'portfolio/dev_content.html', context)


@admin_role_required
def content_list(request, content_type):
    config = get_content_config(content_type)
    queryset = content_queryset(config)
    rows = [content_row(item, config) for item in queryset]
    context = {
        **dashboard_context(request, 'content'),
        'page_title': f"{config['plural']} | {_get_profile_name()}",
        'content_nav_groups': content_navigation(content_type),
        'content_type': content_type,
        'config': config,
        'rows': rows,
        'can_create': not (config.get('singleton') and queryset.exists()),
    }
    return render(request, 'portfolio/dev_content_list.html', context)


@admin_role_required
def content_create(request, content_type):
    config = get_content_config(content_type)
    queryset = content_queryset(config)
    if config.get('singleton') and queryset.exists():
        item = queryset.first()
        messages.info(request, f'{config["label"]} already exists. Edit the existing item instead.')
        return redirect('dev_content_edit', content_type=content_type, item_id=item.pk)

    form = config['form'](request.POST or None)
    if request.method == 'POST' and form.is_valid():
        item = form.save()
        messages.success(request, f'{config["label"]} created successfully.')
        return redirect('dev_content_edit', content_type=content_type, item_id=item.pk)
    main_fields, side_fields = split_content_form_fields(form, config)

    context = {
        **dashboard_context(request, 'content'),
        'page_title': f"Create {config['label']} | {_get_profile_name()}",
        'content_nav_groups': content_navigation(content_type),
        'content_type': content_type,
        'config': config,
        'form': form,
        'main_fields': main_fields,
        'side_fields': side_fields,
        'mode': 'create',
    }
    return render(request, 'portfolio/dev_content_form.html', context)


@admin_role_required
def content_edit(request, content_type, item_id):
    config = get_content_config(content_type)
    item = get_object_or_404(config['model'], pk=item_id)
    form = config['form'](request.POST or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{config["label"]} updated successfully.')
        return redirect('dev_content_edit', content_type=content_type, item_id=item.pk)
    main_fields, side_fields = split_content_form_fields(form, config)

    context = {
        **dashboard_context(request, 'content'),
        'page_title': f"Edit {config['label']} | {_get_profile_name()}",
        'content_nav_groups': content_navigation(content_type),
        'content_type': content_type,
        'config': config,
        'form': form,
        'main_fields': main_fields,
        'side_fields': side_fields,
        'item': item,
        'mode': 'edit',
    }
    return render(request, 'portfolio/dev_content_form.html', context)


@admin_role_required
def content_delete(request, content_type, item_id):
    config = get_content_config(content_type)
    item = get_object_or_404(config['model'], pk=item_id)
    if config.get('protected_delete'):
        messages.error(request, f'{config["label"]} cannot be deleted from /dev.')
        return redirect('dev_content_list', content_type=content_type)

    if request.method == 'POST':
        label = content_item_label(item)
        item.delete()
        messages.success(request, f'{config["label"]} "{label}" deleted successfully.')
        return redirect('dev_content_list', content_type=content_type)

    context = {
        **dashboard_context(request, 'content'),
        'page_title': f"Delete {config['label']} | {_get_profile_name()}",
        'content_nav_groups': content_navigation(content_type),
        'content_type': content_type,
        'config': config,
        'item': item,
    }
    return render(request, 'portfolio/dev_content_delete.html', context)


@dashboard_access_required
@require_POST
def toggle_inquiry_read(request, inquiry_id):
    inquiry = get_object_or_404(Inquiry, id=inquiry_id)
    inquiry.is_read = not inquiry.is_read
    inquiry.save(update_fields=['is_read'])
    state = 'read' if inquiry.is_read else 'unread'
    messages.success(request, f'Inquiry marked as {state}.')
    next_url = request.POST.get('next')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = reverse('dev')
    return redirect(next_url)


def active_admin_count():
    return DashboardUserProfile.objects.filter(
        role=DashboardUserProfile.ADMIN,
        user__is_active=True,
    ).count()


@admin_role_required
def dashboard_users(request):
    users = (
        User.objects.filter(dashboard_profile__isnull=False)
        .select_related('dashboard_profile')
        .order_by('username')
    )
    context = {
        **dashboard_context(request, 'users'),
        'page_title': f"Users | {_get_profile_name()}",
        'users': users,
    }
    return render(request, 'portfolio/dashboard_users.html', context)


@admin_role_required
def dashboard_user_create(request):
    form = DashboardUserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        user = User(username=username, email=username, is_active=form.cleaned_data['is_active'])
        user.set_password(form.cleaned_data['temp_password'])
        user.save()
        DashboardUserProfile.objects.create(
            user=user,
            role=form.cleaned_data['role'],
        )
        messages.success(request, 'User created successfully.')
        return redirect('dashboard_users')

    context = {
        **dashboard_context(request, 'users'),
        'page_title': f"Create User | {_get_profile_name()}",
        'form': form,
        'user_mode': 'create',
    }
    return render(request, 'portfolio/dashboard_user_form.html', context)


@admin_role_required
def dashboard_user_edit(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    target_profile = get_object_or_404(DashboardUserProfile, user=target_user)
    form = DashboardUserUpdateForm(
        request.POST or None,
        user_instance=target_user,
        initial={
            'username': target_user.username,
            'role': target_profile.role,
            'is_active': target_user.is_active,
        },
    )

    if request.method == 'POST' and form.is_valid():
        next_role = form.cleaned_data['role']
        next_active = form.cleaned_data['is_active']
        if (
            target_user.is_active
            and target_profile.role == DashboardUserProfile.ADMIN
            and (not next_active or next_role != DashboardUserProfile.ADMIN)
            and active_admin_count() <= 1
        ):
            form.add_error(None, 'At least one active Admin account must remain.')
        else:
            target_user.username = form.cleaned_data['username']
            target_user.email = form.cleaned_data['username']
            target_user.is_active = next_active
            target_user.save(update_fields=['username', 'email', 'is_active'])
            target_profile.role = next_role
            target_profile.save(update_fields=['role', 'updated_at'])
            messages.success(request, 'User updated successfully.')
            return redirect('dashboard_users')

    context = {
        **dashboard_context(request, 'users'),
        'page_title': f"Edit User | {_get_profile_name()}",
        'form': form,
        'target_user': target_user,
        'target_profile': target_profile,
        'user_mode': 'edit',
    }
    return render(request, 'portfolio/dashboard_user_form.html', context)


@admin_role_required
@require_POST
def dashboard_user_deactivate(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    target_profile = get_object_or_404(DashboardUserProfile, user=target_user)

    if request.user.id == target_user.id:
        messages.error(request, 'You cannot deactivate your own account.')
        return redirect('dashboard_users')
    if not target_user.is_active:
        messages.info(request, 'User is already inactive.')
        return redirect('dashboard_users')
    if target_profile.role == DashboardUserProfile.ADMIN and active_admin_count() <= 1:
        messages.error(request, 'At least one active Admin account must remain.')
        return redirect('dashboard_users')

    target_user.is_active = False
    target_user.save(update_fields=['is_active'])
    messages.success(request, 'User deactivated successfully.')
    return redirect('dashboard_users')


@admin_role_required
@require_POST
def dashboard_user_reactivate(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    get_object_or_404(DashboardUserProfile, user=target_user)
    if target_user.is_active:
        messages.info(request, 'User is already active.')
        return redirect('dashboard_users')

    target_user.is_active = True
    target_user.save(update_fields=['is_active'])
    messages.success(request, 'User reactivated successfully.')
    return redirect('dashboard_users')


@admin_role_required
@require_POST
def dashboard_user_reset_password(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    get_object_or_404(DashboardUserProfile, user=target_user)
    form = DashboardPasswordResetForm(request.POST)
    if not form.is_valid():
        for field_errors in form.errors.values():
            messages.error(request, field_errors[0])
        return redirect('dashboard_user_edit', user_id=target_user.id)

    target_user.set_password(form.cleaned_data['temp_password'])
    target_user.save(update_fields=['password'])
    messages.success(request, 'Temporary password has been updated.')
    return redirect('dashboard_user_edit', user_id=target_user.id)


@dashboard_access_required
@require_POST
def dashboard_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('dashboard_login')


def robots_txt(request):
    lines = [
        'User-agent: *',
        'Allow: /',
        'Sitemap: https://calebmayaka.com/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


# ---------------------------------------------------------------------------
# Newsletter helpers
# ---------------------------------------------------------------------------

def _site_url():
    return getattr(settings, 'PUBLIC_SITE_URL', '').rstrip('/')


def _send_confirmation_email(subscriber):
    site_url = _site_url()
    confirm_url = f'{site_url}/blog/confirm/{subscriber.confirm_token}/'
    unsub_url = f'{site_url}/blog/unsubscribe/{subscriber.unsubscribe_token}/'
    ctx = {
        'confirm_url': confirm_url,
        'unsubscribe_url': unsub_url,
        'public_site_url': site_url,
    }
    subject = 'Confirm your subscription — calebmayaka.com'
    text = render_to_string('blogcms/email/confirm_subscription.txt', ctx)
    html = render_to_string('blogcms/email/confirm_subscription.html', ctx)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[subscriber.email],
    )
    msg.attach_alternative(html, 'text/html')
    try:
        msg.send(fail_silently=False)
    except Exception:
        # Don't let a broken SMTP config surface a 500 to the subscriber,
        # but log it loudly so it's visible in the rotating log file.
        logger.exception(
            'Failed to send confirmation email to %s', subscriber.email
        )


# ---------------------------------------------------------------------------
# Newsletter public views
# ---------------------------------------------------------------------------

@ratelimit(key='ip', rate='5/h', method='POST', block=False)
def subscribe(request):
    if request.method != 'POST':
        return redirect('/blog/')

    if getattr(request, 'limited', False):
        messages.error(request, 'Too many attempts. Please wait before trying again.')
        return redirect(_safe_referer(request))

    form = SubscribeForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Please enter a valid email address.')
        return redirect(_safe_referer(request))

    # Honeypot check
    if form.cleaned_data.get('website'):
        messages.success(request, "You're subscribed!")
        return redirect(_safe_referer(request))

    email = form.cleaned_data['email']

    try:
        subscriber = Subscriber.objects.get(email=email)
        if subscriber.is_confirmed:
            messages.info(request, 'This email is already subscribed.')
        else:
            _send_confirmation_email(subscriber)
            messages.success(request, 'Check your inbox — a confirmation link is on its way.')
    except Subscriber.DoesNotExist:
        subscriber = Subscriber.objects.create(email=email)
        _send_confirmation_email(subscriber)
        messages.success(request, 'Almost done! Check your inbox and click the confirmation link.')

    return redirect(_safe_referer(request))


def confirm_subscription(request, token):
    try:
        subscriber = Subscriber.objects.get(confirm_token=token)
        if not subscriber.is_confirmed:
            subscriber.is_confirmed = True
            subscriber.confirmed_at = timezone.now()
            subscriber.save(update_fields=['is_confirmed', 'confirmed_at'])
            messages.success(request, "You're subscribed! New articles will land in your inbox.")
        else:
            messages.info(request, 'Your subscription is already confirmed.')
    except Subscriber.DoesNotExist:
        messages.error(request, 'Invalid or expired confirmation link.')
    return redirect('/blog/')


def unsubscribe_view(request, token):
    try:
        subscriber = Subscriber.objects.get(unsubscribe_token=token)
        subscriber.delete()
        messages.success(request, "You've been unsubscribed. No more emails from us.")
    except Subscriber.DoesNotExist:
        messages.info(request, 'This unsubscribe link has already been used.')
    return redirect('/blog/')


# ---------------------------------------------------------------------------
# Newsletter dashboard views
# ---------------------------------------------------------------------------

@admin_role_required
def newsletter_dashboard(request):
    recent_posts = (
        BlogPostPage.objects.live().public()
        .order_by('-date', '-first_published_at')[:12]
    )
    digest_form = DigestForm(posts=recent_posts)
    subscribers = Subscriber.objects.all()
    digest_logs = DigestLog.objects.all()[:10]

    context = {
        **dashboard_context(request, 'newsletter'),
        'page_title': f'Newsletter | {_get_profile_name()}',
        'digest_form': digest_form,
        'subscribers': subscribers,
        'total_subscribers': subscribers.count(),
        'confirmed_count': subscribers.filter(is_confirmed=True).count(),
        'pending_count': subscribers.filter(is_confirmed=False).count(),
        'digest_logs': digest_logs,
    }
    return render(request, 'portfolio/newsletter.html', context)


@admin_role_required
@require_POST
def send_digest(request):
    recent_posts = (
        BlogPostPage.objects.live().public()
        .order_by('-date', '-first_published_at')[:12]
    )
    form = DigestForm(request.POST, posts=recent_posts)

    if not form.is_valid():
        messages.error(request, 'Please fix the form errors before sending.')
        return redirect('dev_newsletter')

    post_ids = [int(pk) for pk in form.cleaned_data['post_ids']]
    subject = form.cleaned_data['subject']
    selected_posts = list(
        BlogPostPage.objects.filter(pk__in=post_ids).order_by('-date')
    )
    confirmed = list(Subscriber.objects.filter(is_confirmed=True))

    if not confirmed:
        messages.warning(request, 'No confirmed subscribers to send to yet.')
        return redirect('dev_newsletter')

    site_url = _site_url()
    emails = []
    connection = get_connection()

    for subscriber in confirmed:
        ctx = {
            'posts': selected_posts,
            'subject': subject,
            'public_site_url': site_url,
            'unsubscribe_url': f'{site_url}/blog/unsubscribe/{subscriber.unsubscribe_token}/',
        }
        text = render_to_string('blogcms/email/digest.txt', ctx)
        html = render_to_string('blogcms/email/digest.html', ctx)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[subscriber.email],
            connection=connection,
        )
        msg.attach_alternative(html, 'text/html')
        msg.extra_headers['List-Unsubscribe'] = (
            f'<{site_url}/blog/unsubscribe/{subscriber.unsubscribe_token}/>'
        )
        msg.extra_headers['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
        emails.append(msg)

    try:
        connection.open()
        connection.send_messages(emails)
        connection.close()
    except Exception:
        logger.exception('Digest send failed (subject=%r, recipients=%d)', subject, len(emails))
        messages.error(request, 'Failed to send digest — check the server logs for details.')
        return redirect('dev_newsletter')

    DigestLog.objects.create(
        subject=subject,
        recipient_count=len(emails),
        post_count=len(post_ids),
    )
    s = 's' if len(emails) != 1 else ''
    messages.success(request, f'Digest sent to {len(emails)} subscriber{s}.')
    return redirect('dev_newsletter')
