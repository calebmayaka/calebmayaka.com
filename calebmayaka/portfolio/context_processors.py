from django.core.cache import cache
from types import SimpleNamespace

from .models import SiteProfile, SocialLink


PRIMARY_NAV_ITEMS = [
    {'label': 'Home', 'url_name': 'home', 'url': '', 'active_key': 'home'},
    {'label': 'Blog', 'url_name': '', 'url': '/blog/', 'active_key': 'blog'},
]

FOOTER_NAV_ITEMS = [
    {'label': 'About', 'url_name': 'about', 'url': '', 'active_key': 'about'},
    {'label': 'Experience', 'url_name': 'experience', 'url': '', 'active_key': 'experience'},
    {'label': 'Case Studies', 'url_name': 'case_studies', 'url': '', 'active_key': 'case_studies'},
]

GENERIC_SOCIAL_URLS = {
    'https://github.com/',
    'https://www.linkedin.com/',
}

SITE_CHROME_CACHE_KEY = 'portfolio:site_chrome:v1'
SITE_CHROME_CACHE_TIMEOUT = 300


def fallback_profile():
    return SimpleNamespace(
        name='Caleb Mayaka',
        initials='CM',
        role='',
        headline='',
        summary='',
        location='',
        email='',
        whatsapp_url='',
        availability='',
        meta_description='',
    )


def get_site_chrome():
    cached = cache.get(SITE_CHROME_CACHE_KEY)
    if cached is not None:
        if cached.get('profile') is None:
            cached['profile'] = fallback_profile()
        return cached

    social_links = [
        link for link in SocialLink.objects.order_by('order')
        if link.url not in GENERIC_SOCIAL_URLS
    ]

    profile = SiteProfile.objects.first() or fallback_profile()

    chrome = {
        'profile': profile,
        'primary_nav_items': PRIMARY_NAV_ITEMS,
        'footer_nav_items': FOOTER_NAV_ITEMS,
        'social_links': social_links,
    }
    cache.set(SITE_CHROME_CACHE_KEY, chrome, SITE_CHROME_CACHE_TIMEOUT)
    return chrome


def site_chrome(request):
    return get_site_chrome()
