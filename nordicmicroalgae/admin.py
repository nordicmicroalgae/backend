from axes.helpers import get_client_ip_address
from axes.models import AccessAttempt
from django.conf import settings
from django.contrib.admin import AdminSite
from django.urls import re_path

from synchronization.views import AdminSyncDbView


class NordicMicroalgaeAdminSite(AdminSite):
    site_header = "nµa administration"
    site_title = "nµa site admin"
    login_template = "admin/login.html"

    def login(self, request, extra_context=None):
        extra_context = extra_context or {}
        ip_address = get_client_ip_address(request)
        attempts = AccessAttempt.objects.filter(ip_address=ip_address)
        failures = attempts.values_list("failures_since_start", flat=True).first() or 0
        remaining = max(settings.AXES_FAILURE_LIMIT - failures, 0)
        if failures > 0:
            extra_context["axes_remaining_attempts"] = remaining
            extra_context["axes_failure_limit"] = settings.AXES_FAILURE_LIMIT
        return super().login(request, extra_context=extra_context)

    def get_urls(self):
        urls = [
            re_path(
                r"^syncdb/(?P<log_id>(syncdb-\d{4}-\d{2})-\d{2}_\d{2}-\d{2}-\d{2})?$",
                self.admin_view(AdminSyncDbView.as_view()),
                name="synchronization_syncdb",
            ),
        ]
        return urls + super().get_urls()
