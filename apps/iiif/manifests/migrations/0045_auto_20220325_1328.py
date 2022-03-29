# Generated by Django 3.2.12 on 2022-03-25 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manifests', '0044_auto_20220323_1620'),
    ]

    operations = [
        migrations.AddField(
            model_name='imageserver',
            name='private_key_path',
            field=models.CharField(default='~/.ssh/id_rsa.pem', max_length=500),
        ),
        migrations.AddField(
            model_name='imageserver',
            name='sftp_port',
            field=models.IntegerField(default=22),
        ),
    ]