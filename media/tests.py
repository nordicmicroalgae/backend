import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from media.models import Media
from taxa.models import Taxon


@pytest.mark.django_db
def test_fetch_media_without_children(client):
    # Given a user
    user = get_user_model().objects.create(id=1)

    # Given a parent taxon
    parent_taxon = Taxon.objects.create(
        id=1,
        slug="parent-taxon",
        children=[
            {"slug": "child-taxon1"},
            {"slug": "child-taxon2"},
        ],
    )

    # Given child taxons
    child_taxon1 = Taxon.objects.create(id=2, slug="child-taxon1")
    child_taxon2 = Taxon.objects.create(id=3, slug="child-taxon2")

    # Given an unrelated taxon
    other_taxon = Taxon.objects.create(id=4, slug="other-taxon")

    # Given media for all taxons
    parent_media = Media.objects.create(
        slug="parent-media", taxon=parent_taxon, created_by=user
    )
    Media.objects.create(slug="child-media1", taxon=child_taxon1, created_by=user)
    Media.objects.create(slug="child-media2", taxon=child_taxon2, created_by=user)
    Media.objects.create(slug="other-media", taxon=other_taxon, created_by=user)

    # When fetching the parent taxon without requesting children
    url = reverse("media-collection-view")
    response = client.get(url, {"taxon": "parent-taxon"})
    assert response.status_code == 200

    # Then only the media for the parent taxon is returned
    all_retrieved_media = response.json()["media"]
    assert len(all_retrieved_media) == 1

    retrieved_media = all_retrieved_media[0]
    assert retrieved_media["slug"] == parent_media.slug


@pytest.mark.django_db
def test_fetch_media_with_children(client):
    # Given a user
    user = get_user_model().objects.create(id=1)

    # Given a parent taxon
    parent_taxon = Taxon.objects.create(
        id=1,
        slug="parent-taxon",
        children=[
            {"slug": "child-taxon1"},
            {"slug": "child-taxon2"},
        ],
    )

    # Given child taxons
    child_taxon1 = Taxon.objects.create(id=2, slug="child-taxon1")
    child_taxon2 = Taxon.objects.create(id=3, slug="child-taxon2")

    # Given an unrelated taxon
    other_taxon = Taxon.objects.create(id=4, slug="other-taxon")

    # Given media for all taxons
    parent_media = Media.objects.create(
        slug="parent-media", taxon=parent_taxon, created_by=user
    )
    child1_media = Media.objects.create(
        slug="child-media1", taxon=child_taxon1, created_by=user
    )
    child2_media = Media.objects.create(
        slug="child-media2", taxon=child_taxon2, created_by=user
    )
    Media.objects.create(slug="other-media", taxon=other_taxon, created_by=user)

    # When fetching the parent taxon and requesting children
    url = reverse("media-collection-view")
    response = client.get(url, {"taxon": "parent-taxon", "children": "True"})
    assert response.status_code == 200

    # Then media for the parent taxon and its children is returned
    all_retrieved_media = response.json()["media"]
    assert len(all_retrieved_media) == 3

    retrieved_media_slugs = set([media["slug"] for media in all_retrieved_media])
    assert retrieved_media_slugs == {
        parent_media.slug,
        child1_media.slug,
        child2_media.slug,
    }
