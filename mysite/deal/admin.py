import requests
from datetime import datetime, timedelta

from django.contrib import admin, messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.urls import path, reverse

from deal.models import Status, Commission, Offer, Deal, Payment, StatusPayment
from deal.forms import ConfirmPay, DealPayForm
from deal.utils import available_request_methods, get_balance_user, pay, check_user_balance, confirm_payment
from deal.exceptions import InternalServerError, NotFoundError, UnauthorizedError, \
    BadRequestError, OtherStatusCodes, NotEnoughMoney


class OfferListFilter(admin.SimpleListFilter):
    title = 'Предложения'
    parameter_name = 'filter'

    def lookups(self, request, model_admin):
        return (
            ('my', 'Мои'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'my':
            return queryset.filter(user=request.user)


class OfferAdmin(admin.ModelAdmin):
    exclude = ('user', 'money_to_invoice')
    list_display = ('title', 'price')
    list_filter = (OfferListFilter,)

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def has_change_permission(self, request, obj=None):
        if obj:
            return self.is_owner(current_user=request.user, owner_offer=obj.user)

    def is_owner(self, current_user, owner_offer):
        return current_user == owner_offer

    def has_delete_permission(self, request, obj=None):
        if obj:
            return self.is_owner(current_user=request.user, owner_offer=obj.user)

    def add_view(self, request, form_url='', extra_context=None):
        return super().add_view(
            request,
            form_url='',
            extra_context=None
        )

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}

        try:
            extra_context['offer'] = Offer.objects.get(pk=object_id)
        except ObjectDoesNotExist:
            self.message_user(
                request,
                'Объект не найден',
                messages.WARNING
            )
            return redirect(reverse('admin:index', current_app=self.admin_site.name))

        return super().change_view(
            request,
            object_id,
            form_url='',
            extra_context=extra_context
        )

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                '<int:offer_pk>/confirm/',
                self.admin_site.admin_view(self.confirm_offer_view),
                name='offer_confirm'
            ),
        ]
        return my_urls + urls

    def confirm_offer_view(self, request, offer_pk):
        try:
            offer = Offer.objects.get(pk=offer_pk)
        except ObjectDoesNotExist:
            self.message_user(
                request,
                'Объект не найден',
                messages.WARNING
            )
            return redirect(reverse('admin:index', current_app=self.admin_site.name))

        if request.method == 'POST':
            deal = self.create_deal(request, offer)
            return redirect(reverse('admin:deal_pay', args=[deal.pk]))

        context = dict(
            offer=offer
        )
        return TemplateResponse(request, 'offer/confirm.html', context)

    def create_deal(self, request, offer):
        status, created = Status.objects.get_or_create(
            name='Активна',
            defaults={
                'name': 'Активна'
            }
        )
        return Deal.objects.create(
            owner=request.user,
            buyer=offer.user,
            offer=offer,
            status=status,
            time_on_pay_expire=datetime.now() + timedelta(
                hours=offer.limit_hours_on_pay
            )
        )


class CommissionAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if not request.user.is_superuser:
            return False

        if Commission.objects.exists():
            return False
        return True


class DealAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(owner=request.user)

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        newurls = [
            path(
                '<int:deal_pk>/pay/',
                self.admin_site.admin_view(self.pay_view),
                name='deal_pay'
            ),
            path(
                'payment/<int:payment_pk>/confirm/',
                self.admin_site.admin_view(self.confirm_payment_view),
                name='deal_confirm_payment'
            ),
        ]
        return newurls + urls

    @available_request_methods(['GET', 'POST'])
    def pay_view(self, request, deal_pk):
        if request.method == 'GET':
            form = DealPayForm()
            # Для вывода в select всех счетов только текущего пользователя
            form.base_fields['invoice'].queryset = \
                form.base_fields['invoice'].queryset.filter(
                    user=request.user
                )
            return render(
                request,
                'deal/pay.html',
                {
                    'form': form,
                    'deal_pk': deal_pk,
                }
            )

        form = DealPayForm(request.POST)
        if form.is_valid():
            try:
                number_invoice_provider = form.cleaned_data['invoice'].num
                amount_money_payment = form.cleaned_data['amount_money']
                check_user_balance(number_invoice_provider, amount_money_payment)

                deal = Deal.objects.get(pk=deal_pk)
                number_invoice_reciever = deal.offer.money_to_invoice.num
                pay(
                    amount_money_payment,
                    number_invoice_provider,
                    number_invoice_reciever
                )
                payment = self.create_payment(
                    deal,
                    amount_money_payment,
                    number_invoice_provider,
                    number_invoice_reciever
                )

                return redirect(
                    reverse(
                        'admin:deal_confirm_payment',
                        kwargs={'payment_pk': payment.pk}
                    )
                )
            except (
                requests.exceptions.ConnectionError,
                InternalServerError,
                UnauthorizedError
            ):
                return render(request, 'errors/500.html')
            except ObjectDoesNotExist:
                self.message_user(
                    request,
                    'Нет такой сделки',
                    messages.WARNING
                )
                return redirect(
                    reverse(
                        'admin:deal_pay',
                        kwargs={'deal_pk': deal_pk},
                    )
                )
            except NotEnoughMoney:
                self.message_user(
                    request,
                    'Не хватает денег. '
                    'Используйте другой счет или заплатите меньше.',
                    messages.WARNING
                )
                return redirect(
                    reverse(
                        'admin:deal_pay',
                        kwargs={'deal_pk': deal_pk}
                    )
                )
            except NotFoundError:
                self.message_user(
                    request,
                    'Расчетный счет не валидный или не существует',
                    messages.WARNING
                )
                return redirect(
                    reverse(
                        'admin:deal_pay',
                        kwargs={'deal_pk': deal_pk}
                    )
                )
            except OtherStatusCodes:
                return render(request, 'errors/500.html')
        else:
            return render(
                request,
                'deal/pay.html',
                {
                    'form': form,
                    'deal_pk': deal_pk,
                }
            )

    def create_payment(self, deal, amount_money_payment, number_invoice_provider, number_invoice_reciever):
        status, created = StatusPayment.objects.get_or_create(
            name='не подтвержден',
            defaults={
                'name': 'не подтвержден'
            }
        )
        return Payment.objects.create(
            deal=deal,
            number_invoice_provider=number_invoice_provider,
            number_invoice_reciever=number_invoice_reciever,
            amount_money=amount_money_payment,
            status=status
        )

    @available_request_methods(['GET', 'POST'])
    def confirm_payment_view(self, request, payment_pk):
        if request.method == 'GET':
            form = ConfirmPay()
            return render(
                request,
                'deal/confirm_payment.html',
                {
                    'form': form,
                    'payment_pk': payment_pk
                }
            )

        form = ConfirmPay(request.POST)
        if form.is_valid():
            try:
                payment = Payment.objects.get(pk=payment_pk)
                key_payment = confirm_payment(
                    payment.number_invoice_provider,
                    form.cleaned_data['code_confirm']
                )
                payment.key = key_payment
                payment.save()

                # отправим задачу на операцию платежа в celery

                self.message_user(
                    request,
                    'Платеж обрабатывается. Можете продолжить работу.',
                    messages.WARNING
                )
                return redirect(
                    reverse(
                        'admin:deal_offer_changelist'
                    )
                )
            except ObjectDoesNotExist:
                self.message_user(
                    request,
                    'Нет такой сделки',
                    messages.WARNING
                )
                return redirect(
                    reverse(
                        'admin:deal_confirm_payment',
                        kwargs={'payment_pk': payment_pk},
                    )
                )
            except (
                requests.exceptions.ConnectionError,
                InternalServerError,
                UnauthorizedError
            ):
                return render(request, 'errors/500.html')
            except BadRequestError:
                self.message_user(
                    request,
                    'Не правильный код подтверждения',
                    messages.WARNING
                )
                return redirect(
                    reverse(
                        'admin:deal_confirm_payment',
                        kwargs={'payment_pk': payment_pk}
                    )
                )
            except OtherStatusCodes:
                render(request, 'errors/500.html')

        return render(
            request,
            'deal/confirm_payment.html',
            {
                'form': form,
                'payment_pk': payment_pk
            }
        )


admin.site.register(Status)
admin.site.register(Commission, CommissionAdmin)
admin.site.register(Offer, OfferAdmin)
admin.site.register(Deal, DealAdmin)