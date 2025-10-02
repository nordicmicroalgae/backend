import os

from django.http import HttpResponse

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "openapi.yaml")


def get_openapi_schema(request):
    schema_content = ""
    with open(SCHEMA_PATH, "rb") as schema_file:
        schema_content = schema_file.read()
    return HttpResponse(schema_content, content_type="text/plain")
