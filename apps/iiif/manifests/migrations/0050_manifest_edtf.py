# Generated by Django 3.2.12 on 2022-04-08 18:00

import edtf.fields
from edtf import text_to_edtf
from django.db import migrations, models
import apps.iiif.manifests.validators


def dates_to_edtf(apps, _):  # pylint: disable=redefined-outer-name
    """Migration function to attempt to convert all existing publication dates to EDTF dates."""
    Manifest = apps.get_model("manifests", "Manifest")  # pylint: disable=invalid-name
    manifests = Manifest.objects.filter(published_date__isnull=False).exclude(published_date="")
    for manifest in manifests:
        edtf_date = text_to_edtf(manifest.published_date)
        if edtf_date:
            manifest.published_date_edtf = edtf_date
        else:
            print(f"""
            Failed to convert {manifest.published_date} to EDTF (manifest with pid {
                manifest.pid
            } and label {manifest.label}).""")
    Manifest.objects.bulk_update(manifests, ["published_date_edtf"])


class Migration(migrations.Migration):

    dependencies = [
        ('manifests', '0049_merge_20220401_1254'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manifest',
            name='date_edtf',
            field=edtf.fields.EDTFField(
                blank=True,
                lower_fuzzy_field='date_earliest',
                lower_strict_field='date_sort_ascending',
                natural_text_field='published_date_edtf',
                null=True,
                upper_fuzzy_field='date_latest',
                upper_strict_field='date_sort_descending',
                verbose_name='Date of publication (EDTF)',
            ),
        ),
        migrations.AlterField(
            model_name='manifest',
            name='published_date',
            field=models.CharField(
                blank=True,
                help_text='Used for display only.',
                max_length=255,
                null=True,
                verbose_name='Published date (display)',
            ),
        ),
        migrations.AlterField(
            model_name='manifest',
            name='published_date_edtf',
            field=models.CharField(
                blank=True,
                help_text="Must be valid date conforming to the\n        <a href='https://www.loc.gov/standards/datetime/'>EDTF</a> standard. If left blank, volume\n        will be excluded from sorting and filtering by date of publication.",
                max_length=255,
                null=True,
                validators=[apps.iiif.manifests.validators.validate_edtf],
                verbose_name='Published date (EDTF)',
            ),
        ),
        migrations.RunPython(dates_to_edtf, migrations.RunPython.noop),
    ]
