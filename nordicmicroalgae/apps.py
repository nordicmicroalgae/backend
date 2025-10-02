from django.contrib.admin.apps import AdminConfig


class NordicMicroalgaeAdminConfig(AdminConfig):
    default_site = "nordicmicroalgae.admin.NordicMicroalgaeAdminSite"
