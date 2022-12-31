from django.db import models


from taxa.models import Taxon


class Facts(models.Model):
   id = models.AutoField(primary_key=True, editable=False)
   taxon = models.OneToOneField(Taxon, on_delete=models.CASCADE)
   data = models.JSONField(default=list)
