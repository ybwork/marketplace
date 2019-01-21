# Generated by Django 2.1.4 on 2019-01-21 09:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('deal', '0002_auto_20190121_0827'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deal',
            name='buyer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deals_by_buyer', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='deal',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deals_by_owner', to=settings.AUTH_USER_MODEL),
        ),
    ]