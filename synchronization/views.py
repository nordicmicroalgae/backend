import os
import threading

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import HttpResponseRedirect, HttpResponse
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect


LOGS = os.path.join(settings.CONTENT_DIR, '.syncdb')

def get_log_file(log_id):
    log_name = '{}.log'.format(log_id)
    return os.path.join(LOGS, os.path.basename(log_name))


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

class AdminSyncDbView(AdminRequiredMixin, View):
    def get(self, request, log_id=None):
        log_text = ''

        if log_id:
            with open(get_log_file(log_id), 'r') as log_file:
                log_text = str(log_file.read())

        context = {
            **{
                'log_id': log_id,
                'log_text': log_text,
            },
            **admin.site.each_context(request),
        }

        if request.accepts('text/html'):
            return TemplateResponse(request, 'admin/syncdb.html', context)

        return HttpResponse(log_text, content_type='text/plain')

    @method_decorator(csrf_protect)
    def post(self, request):
        log_id = 'syncdb-{}'.format(
            timezone.now().strftime('%Y-%m-%d_%H-%M-%S')
        )

        thread = threading.Thread(
            target=self._syncdb_thread_func,
            args=[log_id]
        )
        thread.start()

        return HttpResponseRedirect(
            reverse('admin:synchronization_syncdb', args=[log_id])
        )

    def _syncdb_thread_func(self, log_id):
        os.makedirs(LOGS, exist_ok=True)
        with open(get_log_file(log_id), 'a', buffering=1) as log_file:
            try:
                call_command(
                    'syncdb',
                    verbosity=2,
                    no_color=True,
                    stdout=log_file
                )
            except CommandError as e:
                log_file.write('Error: %s\n' % str(e))
            except Exception:
                log_file.write(
                    'Something went wrong. '
                    'Sysadmin should check logs.\n'
                )
                raise
            finally:
                log_file.write('[job completed]')
