from django.db import models


class Status(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Commission(models.Model):
    percent = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return '{} %'.format(self.percent)
