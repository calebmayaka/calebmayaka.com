"""
URL configuration for calebmayaka project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('site/', include('site.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from blogcms.feeds import LatestBlogPostsFeed
from blogcms.views import blog_search_view, blog_tag_view
from wagtail.contrib.sitemaps.views import sitemap

urlpatterns = [
    path('', include('portfolio.urls')),
    path('admin/', admin.site.urls),
    path('cms/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('sitemap.xml', sitemap, name='wagtail_sitemap'),
    path('blog/search/', blog_search_view, name='blog_search'),   # must be before blog/
    path('blog/tags/<slug:tag>/', blog_tag_view, name='blog_tag'),  # must be before blog/
    path('blog/feed/', LatestBlogPostsFeed(), name='blog_feed'),  # must be before blog/
    path('blog/', include(wagtail_urls)),
    re_path(r'^blog$', RedirectView.as_view(url='/blog/', permanent=True)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
