# Generated by Django 3.2.7 on 2022-12-31 06:30

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Taxon',
            fields=[
                ('id', models.AutoField(editable=False, primary_key=True, serialize=False)),
                ('parent_id', models.IntegerField(blank=True, editable=False, null=True)),
                ('slug', models.SlugField(editable=False, max_length=255)),
                ('scientific_name', models.CharField(max_length=200)),
                ('authority', models.CharField(blank=True, max_length=200, null=True)),
                ('rank', models.CharField(blank=True, max_length=64, null=True)),
                ('parent', models.JSONField(default=dict)),
                ('classification', models.JSONField(default=list)),
                ('children', models.JSONField(default=list)),
            ],
        ),
    ]
