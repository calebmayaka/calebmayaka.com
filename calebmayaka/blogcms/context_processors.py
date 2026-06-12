from django.conf import settings


def public_urls(request):
    public_site_url = getattr(settings, 'PUBLIC_SITE_URL', '').rstrip('/')
    if not public_site_url:
        public_site_url = f'{request.scheme}://{request.get_host()}'

    return {
        'public_site_url': public_site_url,
        'public_current_url': f'{public_site_url}{request.get_full_path()}',
        'public_canonical_url': f'{public_site_url}{request.path}',
    }


def giscus(request):
    return {
        'GISCUS_REPO': getattr(settings, 'GISCUS_REPO', ''),
        'GISCUS_REPO_ID': getattr(settings, 'GISCUS_REPO_ID', ''),
        'GISCUS_CATEGORY': getattr(settings, 'GISCUS_CATEGORY', ''),
        'GISCUS_CATEGORY_ID': getattr(settings, 'GISCUS_CATEGORY_ID', ''),
    }
