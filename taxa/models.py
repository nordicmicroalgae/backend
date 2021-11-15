from django.db import models


class Taxon(models.Model):
    scientific_name = models.CharField(max_length=200, primary_key=True)
    parent_name = models.CharField(max_length=200)
    authority = models.CharField(max_length=200)
    rank = models.CharField(max_length=64)
    classification = models.JSONField(default=list)
    children = models.JSONField(default=list)
    attributes = models.JSONField(default=dict)
