# Generated by Django 3.2.13 on 2022-06-07 14:53

from datetime import datetime
import apps.utils.noid
from django.db import migrations, models

def add_dates(apps, _):
    Annotation = apps.get_model("annotations", "Annotation")  # pylint: disable=invalid-name
    for anno in Annotation.objects.all():
        anno.created_at = datetime.now()
        anno.updated_at = datetime.now()

class Migration(migrations.Migration):

    dependencies = [
        ('annotations', '0008_auto_20220607_1407'),
    ]

    operations = [
        migrations.AddField(
            model_name='annotation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='annotation',
            name='label',
            field=models.CharField(default='', max_length=1000),
        ),
        migrations.AddField(
            model_name='annotation',
            name='modified_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='annotation',
            name='pid',
            field=models.CharField(default=apps.utils.noid.encode_noid, help_text="Unique ID. Do not use _'s or spaces in the pid.", max_length=255),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='primary_selector',
            field=models.CharField(choices=[('FR', 'Fragmentselector'), ('CS', 'Cssselector'), ('XP', 'Xpathselector'), ('TQ', 'Textquoteselector'), ('TP', 'Textpositionselector'), ('DP', 'Datapositionselector'), ('SV', 'Svgselector'), ('RG', 'Rangeselector')], default='FR', max_length=2),
        ),
        migrations.AlterField(
            model_name='annotation',
            name='purpose',
            field=models.CharField(choices=[('AS', 'Assessing'), ('BM', 'Bookmarking'), ('CL', 'Classifying'), ('CM', 'Commenting'), ('DS', 'Describing'), ('ED', 'Editing'), ('HL', 'Highlighting'), ('ID', 'Identifying'), ('LK', 'Linking'), ('MO', 'Moderating'), ('QT', 'Questioning'), ('RE', 'Replying'), ('TG', 'Tagging')], default='CM', max_length=2),
        ),
        migrations.RunPython(add_dates, migrations.RunPython.noop),
    ]
