from django.contrib.auth.models import User
from django.db import models


class Status(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Commission(models.Model):
    percent = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return '{} %'.format(self.percent)


class Offer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    limit_days_on_pay = models.IntegerField()

    class Meta:
        verbose_name = 'Offer'

    def __str__(self):
        return self.name
