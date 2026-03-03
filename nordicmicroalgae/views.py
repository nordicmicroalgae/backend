import os
import re

from django.http import JsonResponse
from django.views.decorators.http import require_GET

_pyproject_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "pyproject.toml",
)

try:
    with open(_pyproject_path) as f:
        _match = re.search(r'^version\s*=\s*"([^"]+)"', f.read(), re.MULTILINE)
    VERSION = _match.group(1) if _match else "unknown"
except (FileNotFoundError, OSError):
    VERSION = "unknown"


@require_GET
def get_version(request):
    return JsonResponse({"version": VERSION})
