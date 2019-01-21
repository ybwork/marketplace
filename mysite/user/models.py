from django.contrib.auth.models import User
from django.db import models


class Invoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    num = models.CharField(max_length=20)

    class Meta:
        verbose_name_plural = 'Банковские счета'

    def __str__(self):
        return self.num
