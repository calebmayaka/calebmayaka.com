import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


YOUTUBE_ID_RE = re.compile(
    r'(?:youtube\.com/watch\?(?:[^#]*&)?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
)
YOUTUBE_SHORTS_RE = re.compile(r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})')
YOUTUBE_LIVE_RE = re.compile(r'youtube\.com/live/([a-zA-Z0-9_-]{11})')
VIMEO_RE = re.compile(r'vimeo\.com/(\d+)')


def _with_origin(url, origin=None):
    if not origin:
        return url

    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.setdefault('origin', origin.rstrip('/'))
    return urlunsplit((
        parts.scheme,
        parts.netloc,
        parts.path,
        urlencode(query),
        parts.fragment,
    ))


def embed_url(url, origin=None):
    if not url:
        return ''

    url = str(url).strip()
    if 'youtube.com/embed/' in url or 'youtube-nocookie.com/embed/' in url:
        return _with_origin(url, origin)

    match = YOUTUBE_ID_RE.search(url)
    if match:
        return _with_origin(f'https://www.youtube.com/embed/{match.group(1)}?rel=0', origin)

    match = YOUTUBE_SHORTS_RE.search(url)
    if match:
        return _with_origin(f'https://www.youtube.com/embed/{match.group(1)}?rel=0', origin)

    match = YOUTUBE_LIVE_RE.search(url)
    if match:
        return _with_origin(f'https://www.youtube.com/embed/{match.group(1)}?rel=0', origin)

    match = VIMEO_RE.search(url)
    if match:
        return f'https://player.vimeo.com/video/{match.group(1)}?dnt=1'

    return ''


def is_supported_video_url(url):
    return bool(embed_url(url))
