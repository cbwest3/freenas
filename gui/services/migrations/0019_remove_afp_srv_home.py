# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-11-27 20:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0018_normalize_tftp_umask'),
        ('sharing', '0007_afp_share_afp_home'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='afp',
            name='afp_srv_homedir',
        ),
        migrations.RemoveField(
            model_name='afp',
            name='afp_srv_homedir_enable',
        ),
        migrations.RemoveField(
            model_name='afp',
            name='afp_srv_homename',
        ),
        migrations.RemoveField(
            model_name='afp',
            name='afp_srv_hometimemachine',
        ),
    ]
