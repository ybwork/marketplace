from django.contrib.auth.models import User
from django.db import models

from user.models import Invoice


class Offer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField('Заголовок', max_length=255)
    description = models.TextField('Описание')
    price = models.DecimalField('Стоимость (руб.)', max_digits=10, decimal_places=2)
    limit_hours_on_pay = models.IntegerField('Часов на оплату')
    money_to_invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        verbose_name='Деньги на счет'
    )
    AVAILABLE = 'доступно'
    NOT_AVAILABLE = 'недоступно'
    STATUS_CHOICES = (
        (AVAILABLE, 'доступно'),
        (NOT_AVAILABLE, 'недоступно'),
    )
    status = models.CharField(
        max_length=100,
        choices=STATUS_CHOICES,
        default=AVAILABLE
    )

    class Meta:
        verbose_name = 'предложение'
        verbose_name_plural = 'Предложения'

    def __str__(self):
        return self.title


class Deal(models.Model):
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='deals_by_owner',
        verbose_name='Владелец'
    )
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='deals_by_buyer',
        verbose_name='Покупатель'
    )
    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        verbose_name='Предложение'
    )
    ACTIVE = 'активна'
    COMPLETED = 'завершена'
    CANCELED = 'отменена'
    STATUS_CHOICES = (
        (ACTIVE, 'активна'),
        (COMPLETED, 'завершена'),
        (CANCELED, 'отменена')
    )
    status = models.CharField(
        verbose_name='Статус',
        max_length=100,
        choices=STATUS_CHOICES,
        default=ACTIVE
    )
    time_on_pay_expire = models.DateTimeField('Время на оплату истекает')

    class Meta:
        verbose_name = 'сделку'
        verbose_name_plural = 'Сделки'

    def __str__(self):
        return self.offer.title


class Payment(models.Model):
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE)
    number_invoice_provider = models.CharField(max_length=5)
    number_invoice_reciever = models.CharField(max_length=5)
    key = models.CharField(max_length=5, default='')
    amount_money = models.DecimalField(max_digits=10, decimal_places=2)
    NOT_CONFIRMED = 'не подтвержден'
    PAID = 'оплачен'
    STATUS_CHOICES = (
        (NOT_CONFIRMED, 'не подтвержден'),
        (PAID, 'оплачен')
    )
    status = models.CharField(
        max_length=100,
        choices=STATUS_CHOICES,
        default=NOT_CONFIRMED
    )

    class Meta:
        verbose_name = 'платеж'
        verbose_name_plural = 'Платежи'



