import os
import operator
import yaml

from functools import reduce

from django.conf import settings
from django.db import models
from django.db.models import Q


def get_filter_config():
    config_path = os.path.join(
        settings.BASE_DIR, 'taxa', 'config', 'filters.yaml'
    )

    config = {}
    with open(config_path, 'r', encoding='utf8') as infile:
        config = yaml.safe_load(infile)

    return config


class TaxonQuerySet(models.QuerySet):

    class InvalidQuery(Exception):
        pass

    filter_config = get_filter_config()

    def with_name_like(self, name_pattern):
        return self.filter(scientific_name__icontains=name_pattern)

    def within_rank(self, rank):
        return self.filter(rank__iexact=rank)

    def helcom_peg_only(self):
        return self.filter(
            facts__data__contains=[{'provider': 'HELCOM-PEG'}]
        )

    def species_only(self):
        ranks = self.filter_config['species_or_below']

        return self.filter(
            reduce(
                operator.or_,
                [Q(rank=rank) for rank in ranks]
            )
        )

    def within_group(self, group_name):
        group_name = group_name.lower()

        if group_name == 'all':
            return self.species_only()
        
        included_taxa_by_group = {
            group['group_name'].lower(): group['included_taxa'] 
            for group in self.filter_config['groups_of_organisms']
        }

        if not group_name in included_taxa_by_group:
            valid_groups = included_taxa_by_group.keys()
            raise TaxonQuerySet.InvalidQuery(
                'The provided value for group is not valid. Please '
                'try one of the following: %s.' % ', '.join(valid_groups)
            )

        parents = included_taxa_by_group[group_name]

        filters = [
            Q(classification__contains=[{'scientific_name': parent}])
            for parent in parents
        ]

        return self.species_only().filter(
            reduce(operator.or_, filters)
        )



class Taxon(models.Model):
    id = models.PositiveBigIntegerField(primary_key=True, editable=False)
    parent_id = models.PositiveBigIntegerField(blank=True, null=True, editable=False)
    slug = models.SlugField(max_length=255, editable=False, unique=True)
    scientific_name = models.CharField(max_length=200)
    authority = models.CharField(max_length=200, blank=True, null=True)
    rank = models.CharField(max_length=64, blank=True, null=True)
    parent = models.JSONField(default=dict)
    classification = models.JSONField(default=list)
    children = models.JSONField(default=list)

    objects = TaxonQuerySet.as_manager()

    class Meta:
        ordering = ('scientific_name',)

    def __str__(self):
        return self.scientific_name
