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


def get_site_chrome():
    social_links = [
        link for link in SocialLink.objects.order_by('order')
        if link.url not in GENERIC_SOCIAL_URLS
    ]

    return {
        'profile': SiteProfile.objects.first(),
        'primary_nav_items': PRIMARY_NAV_ITEMS,
        'footer_nav_items': FOOTER_NAV_ITEMS,
        'social_links': social_links,
    }


def site_chrome(request):
    return get_site_chrome()
