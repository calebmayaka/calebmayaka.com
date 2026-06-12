from django.shortcuts import render
from wagtail.search.backends import get_search_backend

from .models import BlogIndexPage, BlogPostPage


def _blog_index():
    return BlogIndexPage.objects.live().public().first()


def _published_blog_posts(index):
    posts = BlogPostPage.objects.live().public()
    if index:
        posts = posts.descendant_of(index)
    return posts


def blog_tag_view(request, tag):
    index = _blog_index()
    posts = (
        _published_blog_posts(index)
        .filter(tags__slug=tag)
        .select_related('cover_image', 'owner')
        .prefetch_related('tags')
        .order_by('-date', '-first_published_at')
    )
    context = {
        'tag': tag,
        'posts': posts,
        'post_count': posts.count(),
        'index_url': index.url if index else '/blog/',
    }
    return render(request, 'blogcms/blog_tag_page.html', context)


def blog_search_view(request):
    query = request.GET.get('q', '').strip()
    index = _blog_index()
    results = []
    result_count = 0

    if query:
        backend = get_search_backend()
        base_qs = (
            _published_blog_posts(index)
            .select_related('cover_image', 'owner')
            .prefetch_related('tags')
        )
        search_results = backend.search(query, base_qs, order_by_relevance=True)

        # Materialise to a list so we can get a count and iterate without a
        # second DB round-trip.  Search results from the DB backend are already
        # in-memory after the first evaluation.
        results = list(search_results)
        result_count = len(results)

    context = {
        'query': query,
        'results': results,
        'result_count': result_count,
        'index_url': index.url if index else '/blog/',
    }
    return render(request, 'blogcms/blog_search_page.html', context)
