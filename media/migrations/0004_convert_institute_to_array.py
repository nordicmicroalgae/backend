from django.db import migrations


def convert_institute_to_array(apps, schema_editor):
    """Convert institute from string to array"""
    Media = apps.get_model('media', 'Media')

    updated_count = 0
    for media in Media.objects.all():
        if 'institute' in media.attributes:
            institute = media.attributes['institute']
            # If it's already a list, skip
            if isinstance(institute, list):
                continue
            # If it's a string, convert to list
            if isinstance(institute, str) and institute:
                media.attributes['institute'] = [institute]
                media.save(update_fields=['attributes'])
                updated_count += 1

    print(f"Converted {updated_count} institute fields to arrays")


def reverse_convert(apps, schema_editor):
    """Convert back to string (for rollback)"""
    Media = apps.get_model('media', 'Media')

    for media in Media.objects.all():
        if 'institute' in media.attributes:
            institute = media.attributes['institute']
            if isinstance(institute, list) and len(institute) > 0:
                # Take first value
                media.attributes['institute'] = institute[0]
                media.save(update_fields=['attributes'])


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0003_imagelabelingimage'),
    ]

    operations = [
        migrations.RunPython(convert_institute_to_array, reverse_convert),
    ]
