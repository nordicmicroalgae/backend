import os

from django.conf import settings
from django.http import JsonResponse

from .readers import MarkdownReader

readers = {
    "news": MarkdownReader(os.path.join(settings.CONTENT_DIR, "_posts")),
    "page": MarkdownReader(settings.CONTENT_DIR),
}


def get_page_list(request):
    article_type = request.GET.get("type", "page")
    article_limit = abs(int(request.GET.get("limit", 0)))

    if article_type not in readers.keys():
        return JsonResponse({"message": "Unkown article type"}, status=400)

    reader = readers[article_type]

    reverse_sort = article_type in ["news"]
    article_list = sorted(reader.documents, reverse=reverse_sort)

    if article_limit > 0:
        article_list = article_list[:article_limit]

    return JsonResponse({"articles": article_list})


def get_page(request, article_id):
    article = None

    for article_type in readers.keys():
        reader = readers[article_type]
        if article_id in reader.documents:
            content, meta = reader.read_document(article_id)
            article = {"id": article_id, **meta, "content": content}
            break

    if article is None:
        return JsonResponse({"message": "Article not found"}, status=404)

    return JsonResponse(article)
