# Generated by Django 3.2.12 on 2023-12-05 16:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("manifests", "0057_alter_manifest_languages"),
    ]

    operations = [
        migrations.AlterField(
            model_name="relatedlink",
            name="data_type",
            field=models.CharField(
                default="Dataset",
                help_text="Leave as 'Dataset' for structured data describing this document (e.g. a remote manifest) and this link will appear in 'seeAlso'; change to any other value and it will only appear in the 'related' property of the manifest.",
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="relatedlink",
            name="format",
            field=models.CharField(
                blank=True,
                choices=[
                    ("text/html", "HTML or web page"),
                    ("application/json", "JSON"),
                    ("application/ld+json", "JSON-LD"),
                    ("application/pdf", "PDF"),
                    ("text/plain", "Text"),
                    ("application/xml", "XML"),
                    ("application/octet-stream", "Other"),
                ],
                max_length=255,
                null=True,
            ),
        ),
    ]
