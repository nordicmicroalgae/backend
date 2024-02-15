from django.db import models


from taxa.models import Taxon


class Facts(models.Model):
   taxon = models.OneToOneField(
      Taxon,
      on_delete=models.CASCADE,
      primary_key=True,
   )

   data = models.JSONField(default=list)

   class Meta:
      db_table = 'taxon_facts'

   def add_or_replace(self, facts_to_add):
      compare_keys = ('collection', 'provider',)

      def differs_from_dict_to_add(facts_dict):
         return not all(
               facts_dict[key] == facts_to_add[key]
               for key in compare_keys
         )

      filtered_data = filter(differs_from_dict_to_add, self.data)

      self.data = list(filtered_data) + [facts_to_add]
