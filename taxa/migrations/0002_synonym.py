# Generated by Django 3.2.7 on 2021-11-16 11:59

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
                ('scientific_name', models.CharField(max_length=200, primary_key=True, serialize=False)),
                ('authority', models.CharField(max_length=200)),
                ('additional_info', models.JSONField(default=dict)),
                ('current_name', models.ForeignKey(db_column='current_name', on_delete=django.db.models.deletion.CASCADE, to='taxa.taxon')),
            ],
        ),
    ]