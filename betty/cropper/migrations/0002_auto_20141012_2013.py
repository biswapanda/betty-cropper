# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cropper', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='status',
            field=models.IntegerField(default=1, choices=[(0, b'Pending'), (1, b'Done'), (2, b'Failed')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='image',
            name='url',
            field=models.URLField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
