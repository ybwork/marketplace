# Generated by Django 2.1.4 on 2019-02-01 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deal', '0011_auto_20190201_1226'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deal',
            name='status',
            field=models.CharField(choices=[('активна', 'активна'), ('завершена', 'завершена'), ('отменена', 'отменена')], default='активна', max_length=50, verbose_name='Статус'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(choices=[('не подтвержден', 'не подтвержден'), ('оплачен', 'оплачен')], default='не подтвержден', max_length=50),
        ),
    ]
