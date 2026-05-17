from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from blogcms.models import BlogPostPage

from .data import (
    case_studies,
    experience as experience_items,
    nav_items,
    profile,
    projects as project_items,
    skills,
    social_links,
    stats,
    tech_stack,
    testimonials,
)
from .forms import (
    DashboardLoginForm,
    DashboardPasswordResetForm,
    DashboardUserCreateForm,
    DashboardUserUpdateForm,
    InquiryForm,
)
from .models import DashboardUserProfile, Inquiry


def base_context(active):
    return {
        'active': active,
        'profile': profile,
        'nav_items': nav_items,
        'social_links': social_links,
    }


def ensure_dashboard_profile(user):
    default_role = DashboardUserProfile.ADMIN if user.is_superuser else DashboardUserProfile.MANAGER
    dashboard_profile, _ = DashboardUserProfile.objects.get_or_create(
        user=user,
        defaults={'role': default_role},
    )
    return dashboard_profile


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

        dashboard_profile = ensure_dashboard_profile(request.user)
        if dashboard_profile.role not in {DashboardUserProfile.ADMIN, DashboardUserProfile.MANAGER}:
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
            messages.error(request, 'Only admins can manage users.')
            return redirect('dev')
        return view_func(request, *args, **kwargs)

    return wrapped


def dashboard_context(request, active):
    inquiries = Inquiry.objects.all()
    unread_count = inquiries.filter(is_read=False).count()
    total_inquiries = inquiries.count()
    read_count = inquiries.filter(is_read=True).count()
    response_rate = round((read_count / total_inquiries) * 100) if total_inquiries else 0
    dashboard_profile = ensure_dashboard_profile(request.user)

    return {
        **base_context('dashboard'),
        'dashboard_active': active,
        'total_inquiries': total_inquiries,
        'unread_count': unread_count,
        'read_count': read_count,
        'response_rate': response_rate,
        'session_timeout_seconds': settings.SESSION_COOKIE_AGE,
        'dashboard_role': dashboard_profile.role,
        'dashboard_role_label': dashboard_profile.get_role_display(),
        'is_dashboard_admin': dashboard_profile.role == DashboardUserProfile.ADMIN,
    }


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


def home(request):
    inquiry_form = InquiryForm(request.POST or None)
    if request.method == 'POST' and inquiry_form.is_valid():
        inquiry_form.save()
        messages.success(request, 'Your inquiry has been sent successfully.')
        return redirect('home')

    context = {
        **base_context('home'),
        'page_title': f"{profile['name']} | {profile['role']}",
        'stats': stats,
        'skills': skills,
        'projects': project_items[:3],
        'blog_posts': (
            BlogPostPage.objects.live()
            .public()
            .order_by('-date', '-first_published_at')
        ),
        'experience': experience_items,
        'testimonials': testimonials,
        'inquiry_form': inquiry_form,
    }
    return render(request, 'portfolio/home.html', context)


def about(request):
    context = {
        **base_context('about'),
        'page_title': f"About | {profile['name']}",
        'skills': skills,
        'tech_stack': tech_stack,
        'stats': stats,
    }
    return render(request, 'portfolio/about.html', context)


def experience(request):
    context = {
        **base_context('experience'),
        'page_title': f"Experience | {profile['name']}",
        'experience': experience_items,
        'tech_stack': tech_stack,
    }
    return render(request, 'portfolio/experience.html', context)


def projects(request):
    context = {
        **base_context('projects'),
        'page_title': f"Projects | {profile['name']}",
        'projects': project_items,
    }
    return render(request, 'portfolio/projects.html', context)


def case_studies(request):
    context = {
        **base_context('case_studies'),
        'page_title': f"Case Studies | {profile['name']}",
        'case_studies': case_studies,
    }
    return render(request, 'portfolio/case_studies.html', context)


def contact(request):
    context = {
        **base_context('contact'),
        'page_title': f"Contact | {profile['name']}",
        'skills': skills,
    }
    return render(request, 'portfolio/contact.html', context)


def dashboard_login(request):
    next_url = request.GET.get('next') or request.POST.get('next') or reverse('dev')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = reverse('dev')

    if request.user.is_authenticated and request.user.is_active:
        dashboard_profile = ensure_dashboard_profile(request.user)
        if dashboard_profile.role in {DashboardUserProfile.ADMIN, DashboardUserProfile.MANAGER}:
            return redirect(next_url)

    form = DashboardLoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        dashboard_profile = ensure_dashboard_profile(user)
        if not user.is_active:
            messages.error(request, 'Your account is inactive.')
        elif dashboard_profile.role not in {DashboardUserProfile.ADMIN, DashboardUserProfile.MANAGER}:
            messages.error(request, 'Your account is not authorized for dashboard access.')
        else:
            login(request, user)
            return redirect(next_url)

    context = {
        **base_context('dashboard'),
        'page_title': f"Login | {profile['name']}",
        'form': form,
        'next_url': next_url,
    }
    return render(request, 'portfolio/dashboard_login.html', context)


@dashboard_access_required
def dashboard(request):
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
        'page_title': f"Dashboard | {profile['name']}",
        'latest_inquiries': inquiries[:5],
        'monthly_activity': monthly_activity,
        'type_breakdown': type_breakdown,
        'consultation_count': inquiries.filter(inquiry_type=Inquiry.CONSULTATION).count(),
        'website_count': inquiries.filter(inquiry_type=Inquiry.WEBSITE).count(),
    }
    return render(request, 'portfolio/dashboard.html', context)


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
        'page_title': f"Inquiries | {profile['name']}",
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
        'page_title': f"Inquiry Detail | {profile['name']}",
        'inquiry': inquiry,
    }
    return render(request, 'portfolio/inquiry_detail.html', context)


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
    users = list(User.objects.order_by('username'))
    for user in users:
        ensure_dashboard_profile(user)
    users = User.objects.select_related('dashboard_profile').order_by('username')
    context = {
        **dashboard_context(request, 'users'),
        'page_title': f"Users | {profile['name']}",
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
        'page_title': f"Create User | {profile['name']}",
        'form': form,
        'user_mode': 'create',
    }
    return render(request, 'portfolio/dashboard_user_form.html', context)


@admin_role_required
def dashboard_user_edit(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    target_profile = ensure_dashboard_profile(target_user)
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
        'page_title': f"Edit User | {profile['name']}",
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
    target_profile = ensure_dashboard_profile(target_user)

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
