from django.db import models


from taxa.models import Taxon


class Facts(models.Model):
   taxon = models.OneToOneField(Taxon, db_column='scientific_name', on_delete=models.CASCADE, primary_key=True)
   data = models.JSONField(default=list)