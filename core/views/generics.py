from django.core.exceptions import BadRequest
from django.http import JsonResponse
from django.views import View


class ClientError(BadRequest):
    pass


class SelectableFieldsMixin:
    fields = None

    def get_fields(self, selected_fields=[]):
        user_selected_fields = list(filter(
            lambda field: field in self.fields,
            map(str.strip, selected_fields)
        ))
        return (user_selected_fields or self.fields, {})


class SingleObjectMixin(SelectableFieldsMixin):
    queryset = None

    def get_queryset(self):
        return self.queryset.all()

    def get_object_dict(self, queryset, *args, **kwargs):
        fields, expressions = self.get_fields(kwargs.get('fields', []))
        queryset = queryset.values(*fields, **expressions)
        return dict(queryset.get(slug=kwargs.get('slug')))


class MultipleObjectMixin(SelectableFieldsMixin):
    queryset = None

    def get_queryset(self):
        return self.queryset.all()

    def get_object_list(self, queryset, *args, **kwargs):
        fields, expressions = self.get_fields(kwargs.get('fields', []))
        queryset = queryset.values(*fields, **expressions)

        offset = abs(int(kwargs.get('offset', 0)))
        limit = abs(int(kwargs.get('limit', 0)))

        if limit > 0:
            queryset = queryset[offset:(offset+limit)]
        elif offset > 0:
            queryset = queryset[offset:]

        return list(queryset)


class ResourceView(SingleObjectMixin, View):

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()

            response_object = self.get_object_dict(
                queryset,
                slug=kwargs.get('slug'),
                fields=request.GET.get('fields', '').split(','),
            )
        except queryset.model.DoesNotExist:
            return JsonResponse({
                'message': 
                    '%(resource)s does not exist.'
                    % {'resource': queryset.model._meta.verbose_name.title()}
                },
                status=404
            )
        except ClientError as exc:
            return JsonResponse({'message': str(exc)}, status=400)

        return JsonResponse(response_object)


class CollectionView(MultipleObjectMixin, View):
    plural_key = 'results'

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()

            object_list = self.get_object_list(
                queryset,
                offset=request.GET.get('offset', 0),
                limit=request.GET.get('limit', 0),
                fields=request.GET.get('fields', '').split(','),
            )
        except ClientError as exc:
            return JsonResponse({'message': str(exc)}, status=400)

        response_objects = {
            self.plural_key: object_list
        }

        return JsonResponse(response_objects)
