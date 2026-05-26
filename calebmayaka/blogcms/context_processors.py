from django.conf import settings


def giscus(request):
    return {
        'GISCUS_REPO': getattr(settings, 'GISCUS_REPO', ''),
        'GISCUS_REPO_ID': getattr(settings, 'GISCUS_REPO_ID', ''),
        'GISCUS_CATEGORY': getattr(settings, 'GISCUS_CATEGORY', ''),
        'GISCUS_CATEGORY_ID': getattr(settings, 'GISCUS_CATEGORY_ID', ''),
    }
