# Generated by Django 4.2.9 on 2024-02-13 17:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('taxa', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Synonym',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('authority', models.CharField(max_length=200, null=True)),
                ('synonym_name', models.CharField(max_length=200)),
                ('taxon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='taxa.taxon')),
            ],
            options={
                'db_table': 'taxon_synonym',
                'ordering': ('synonym_name',),
            },
        ),
    ]