# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_image_tools', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectionImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('collection', models.CharField(unique=True, max_length=255)),
                ('banner', models.ForeignKey(related_name='bannerimage_set', blank=True, to='django_image_tools.Image', null=True)),
                ('cover', models.ForeignKey(related_name='coverimage_set', to='django_image_tools.Image')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
