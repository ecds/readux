# Generated by Django 2.2.10 on 2020-07-30 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_styles', '0002_auto_20200424_1927'),
    ]

    operations = [
        migrations.AlterField(
            model_name='style',
            name='primary_color',
            field=models.CharField(help_text='Bold color to be used for links and navigation.', max_length=50),
        ),
    ]
