from django.db import models


class Taxon(models.Model):
    scientific_name = models.CharField(max_length=200, primary_key=True)
    parent_name = models.CharField(max_length=200)
    authority = models.CharField(max_length=200)
    rank = models.CharField(max_length=64)
    classification = models.JSONField(default=list)
    children = models.JSONField(default=list)
    attributes = models.JSONField(default=dict)

class Synonym(models.Model):
    scientific_name = models.CharField(max_length=200, primary_key=True)
    authority = models.CharField(max_length=200)
    current_name = models.ForeignKey(Taxon, db_column='current_name', on_delete=models.CASCADE)
    additional_info = models.JSONField(default=dict)
