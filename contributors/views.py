from django.contrib.auth import get_user_model

from core.views.generics import CollectionView

UserModel = get_user_model()


class ContributorCollectionView(CollectionView):
    queryset = UserModel.objects

    fields = (
        "first_name",
        "last_name",
        "date_joined",
    )

    plural_key = "contributors"

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        return qs.filter(groups__name="contributor")
