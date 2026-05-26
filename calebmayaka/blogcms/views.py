from django.shortcuts import render

from .models import BlogIndexPage, BlogPostPage


def blog_tag_view(request, tag):
    posts = (
        BlogPostPage.objects.live()
        .public()
        .filter(tags__slug=tag)
        .select_related('cover_image', 'owner')
        .prefetch_related('tags')
        .order_by('-date', '-first_published_at')
    )
    index = BlogIndexPage.objects.live().public().first()
    context = {
        'tag': tag,
        'posts': posts,
        'post_count': posts.count(),
        'index_url': index.url if index else '/blog/',
    }
    return render(request, 'blogcms/blog_tag_page.html', context)


def blog_search_view(request):
    query = request.GET.get('q', '').strip()
    results = []
    result_count = 0
    if query:
        results = (
            BlogPostPage.objects.live()
            .public()
            .search(query)
        )
        result_count = results.count()
    index = BlogIndexPage.objects.live().public().first()
    context = {
        'query': query,
        'results': results,
        'result_count': result_count,
        'index_url': index.url if index else '/blog/',
    }
    return render(request, 'blogcms/blog_search_page.html', context)
