from django.contrib.admin.apps import AdminConfig


class NordicMicroalgaeAdminConfig(AdminConfig):
    default_site = "nordicmicroalgae.admin.NordicMicroalgaeAdminSite"

    def ready(self):
        super().ready()

        from django.contrib import admin
        from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
        from django.contrib.auth.models import User

        class UserAdmin(BaseUserAdmin):
            def get_fieldsets(self, request, obj=None):
                fieldsets = super().get_fieldsets(request, obj)
                if request.user.is_superuser:
                    return fieldsets
                return [
                    (name, {**opts, "fields": tuple(
                        f for f in opts["fields"] if f != "is_superuser"
                    )})
                    for name, opts in fieldsets
                ]

        admin.site.unregister(User)
        admin.site.register(User, UserAdmin)
