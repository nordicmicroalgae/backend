from django.contrib.admin import AdminSite
from django.urls import re_path

from synchronization.views import AdminSyncDbView


class NordicMicroalgaeAdminSite(AdminSite):
    site_header = "nµa administration"
    site_title = "nµa site admin"

    def get_urls(self):
        urls = [
            re_path(
                r"^syncdb/(?P<log_id>(syncdb-\d{4}-\d{2})-\d{2}_\d{2}-\d{2}-\d{2})?$",
                self.admin_view(AdminSyncDbView.as_view()),
                name="synchronization_syncdb",
            ),
        ]
        return urls + super().get_urls()
