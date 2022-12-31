from django.db import models
from django.db.models import Q


class TaxonQuerySet(models.QuerySet):

    def with_name_like(self, name_pattern):
        return self.filter(scientific_name__contains=name_pattern)

    def with_rank(self, rank):
        return self.filter(rank__iexact=rank)

    def harmful_only(self):
        return self.filter(
            facts__data__contains=[{'collection': 'Harmfulness'}]
        )

    def helcom_peg_only(self):
        return self.filter(
            facts__data__contains=[{'provider': 'HELCOM-PEG'}]
        )

    def species_only(self):
        return self.filter(
            Q(rank='Species') |
            Q(rank='Subspecies') |
            Q(rank='Variety') |
            Q(rank='Form') |
            Q(rank='Hybrid')
        )

    def cyanobacteria_only(self):
        return self.species_only().filter(
            classification__contains=[{'name': 'Cyanobacteria'}]
        )

    def diatoms_only(self):
        return self.species_only().filter(
            classification__contains=[{'name': 'Bacillariophyta'}]
        )

    def dinoflagellates_only(self):
        return self.species_only().filter(
            classification__contains=[{'name': 'Dinophyceae'}]
        )

    def ciliates_only(self):
        return self.species_only().filter(
            classification__contains=[{'name': 'Ciliophora'}]
        )

    def other_microalgae_only(self):
        return self.species_only().filter(
            Q(classification__contains=[{'name': 'Cryptophyceae'}]) |
            Q(classification__contains=[{'name': 'Haptophyta'}]) |
            Q(classification__contains=[{'name': 'Bolidophyceae'}]) |
            Q(classification__contains=[{'name': 'Chrysophyceae'}]) |
            Q(classification__contains=[{'name': 'Dictyochophyceae'}]) |
            Q(classification__contains=[{'name': 'Eustigmatophyceae'}]) |
            Q(classification__contains=[{'name': 'Pelagophyceae'}]) |
            Q(classification__contains=[{'name': 'Raphidophyceae'}]) |
            Q(classification__contains=[{'name': 'Synurophyceae'}]) |
            Q(classification__contains=[{'name': 'Chlorophyta'}]) |
            Q(classification__contains=[{'name': 'Glaucophyta'}]) |
            Q(classification__contains=[{'name': 'Coleochaetophyceae'}]) |
            Q(classification__contains=[{'name': 'Klebsormidiophyceae'}]) |
            Q(classification__contains=[{'name': 'Mesostigmatophyceae'}]) |
            Q(classification__contains=[{'name': 'Zygnematophyceae'}]) |
            Q(classification__contains=[{'name': 'Euglenophyceae'}])
        )

    def other_protozoa_only(self):
        return self.species_only().filter(
            Q(classification__contains=[{'name': 'Cryptophyta, ordines incertae sedis'}]) |
            Q(classification__contains=[{'name': 'Bicosoecophyceae'}]) |
            Q(classification__contains=[{'name': 'Bodonophyceae'}]) |
            Q(classification__contains=[{'name': 'Heterokontophyta, ordines incertae sedis'}]) |
            Q(classification__contains=[{'name': 'Cercozoa'}]) |
            Q(classification__contains=[{'name': 'Craspedophyceae'}]) |
            Q(classification__contains=[{'name': 'Ellobiopsea'}]) |
            Q(classification__contains=[{'name': 'Protozoa, classes incertae sedis'}])
        )



class Taxon(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    parent_id = models.IntegerField(blank=True, null=True, editable=False)
    slug = models.SlugField(max_length=255, editable=False)
    scientific_name = models.CharField(max_length=200)
    authority = models.CharField(max_length=200, blank=True, null=True)
    rank = models.CharField(max_length=64, blank=True, null=True)
    parent = models.JSONField(default=dict)
    classification = models.JSONField(default=list)
    children = models.JSONField(default=list)
    objects = TaxonQuerySet.as_manager()
