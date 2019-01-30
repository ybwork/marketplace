import requests
from datetime import datetime, timedelta

from django.contrib import admin, messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Subquery
from django.shortcuts import redirect, render
from django.urls import path, reverse

from deal.models import Status, Commission, Offer, Deal, Payment, StatusPayment
from deal.forms import ConfirmPay, DealPayForm
from deal.utils import available_request_methods, get_balance_user, pay, \
    check_user_balance, confirm_payment, handle_api_response
from deal.tasks import perform_payment

from user.models import Invoice


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


class RedirectMixin:
    def redirect_with_message(
            self,
            request,
            message,
            type_message,
            redirect_to
    ):
        self.message_user(
            request,
            message,
            type_message
        )
        return redirect(redirect_to)


class OfferAdmin(RedirectMixin, admin.ModelAdmin):
    exclude = ('user',)
    list_display = ('title', 'price')
    list_filter = (OfferListFilter,)

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def has_change_permission(self, request, obj=None):
        if obj:
            return self.is_owner(
                current_user=request.user,
                owner_offer=obj.user
            )

    def is_owner(self, current_user, owner_offer):
        return current_user == owner_offer

    def has_delete_permission(self, request, obj=None):
        if obj:
            return self.is_owner(
                current_user=request.user,
                owner_offer=obj.user
            )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'money_to_invoice':
            kwargs['queryset'] = Invoice.objects.filter(user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        try:
            extra_context['offer'] = Offer.objects.get(pk=object_id)
        except ObjectDoesNotExist:
            return self.redirect_with_message(
                request=request,
                message='Предложение не найдено',
                type_message=messages.WARNING,
                redirect_to='admin:index',
            )
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
                route='<int:offer_pk>/confirm/',
                view=self.admin_site.admin_view(self.confirm_offer_view),
                name='offer_confirm'
            ),
        ]
        return my_urls + urls

    def confirm_offer_view(self, request, offer_pk):
        try:
            offer = Offer.objects.get(pk=offer_pk)
        except ObjectDoesNotExist:
            return self.redirect_with_message(
                request=request,
                message='Предложение не найдено',
                type_message=messages.WARNING,
                redirect_to='admin:index',
            )
        if offer.user == request.user:
            return redirect(
                reverse(
                    viewname='admin:deal_offer_changelist',
                )
            )
        if request.method == 'POST':
            deal = self.create_deal(request=request, offer=offer)
            return redirect(
                reverse(
                    viewname='admin:deal_pay',
                    args=[deal.pk]
                )
            )
        context = dict(
            offer=offer
        )
        return render(
            request=request,
            template_name='offer/confirm.html',
            context=context
        )

    def create_deal(self, request, offer):
        status, created = Status.objects.get_or_create(
            name='Активна',
            defaults={
                'name': 'Активна'
            }
        )
        return Deal.objects.create(
            owner=offer.user,
            buyer=request.user,
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


class DealAdmin(RedirectMixin, admin.ModelAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(buyer=request.user)

    def changelist_view(self, request, extra_context=None):
        return super().changelist_view(request, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        newurls = [
            path(
                route='<int:deal_pk>/pay/',
                view=self.admin_site.admin_view(self.pay_view),
                name='deal_pay'
            ),
            path(
                route='payment/<int:payment_pk>/confirm/',
                view=self.admin_site.admin_view(self.confirm_payment_view),
                name='deal_confirm_payment'
            ),
        ]
        return newurls + urls

    @available_request_methods(['GET', 'POST'])
    def pay_view(self, request, deal_pk):
        if request.method == 'GET':
            form = DealPayForm()
            # Для вывода в select всех счетов только текущего пользователя
            form.fields['invoice'].queryset = \
                form.fields['invoice'].queryset.filter(
                    user=request.user
                )
        else:
            form = DealPayForm(request.POST)
            if form.is_valid():
                return self.pay_process(
                    request,
                    number_invoice_provider=form.cleaned_data['invoice'].num,
                    amount_money_payment=form.cleaned_data['amount_money'],
                    deal_pk=deal_pk
                )
        return render(
            request=request,
            template_name='deal/pay.html',
            context={
                'form': form,
                'deal_pk': deal_pk,
            }
        )

    @handle_api_response
    def pay_process(
            self,
            request,
            number_invoice_provider,
            amount_money_payment,
            deal_pk
        ):
        check_user_balance(
            invoice=number_invoice_provider,
            amount_money_payment=amount_money_payment
        )

        try:
            deal = Deal.objects.get(pk=deal_pk)
            number_invoice_reciever = deal.offer.money_to_invoice.num
        except ObjectDoesNotExist:
            return self.redirect_with_message(
                request=request,
                message='Нет такой сделки',
                type_message=messages.WARNING,
                redirect_to=request.META['HTTP_REFERER'],
            )

        pay(
            amount_money=amount_money_payment,
            number_invoice_provider=number_invoice_provider,
            number_invoice_reciever=number_invoice_reciever
        )

        status, created = StatusPayment.objects.get_or_create(
            name='не подтвержден',
            defaults={
                'name': 'не подтвержден'
            }
        )
        payment = Payment.objects.create(
            deal=deal,
            number_invoice_provider=number_invoice_provider,
            number_invoice_reciever=number_invoice_reciever,
            amount_money=amount_money_payment,
            status=status
        )

        return redirect(
            reverse(
                viewname='admin:deal_confirm_payment',
                kwargs={'payment_pk': payment.pk}
            )
        )

    @available_request_methods(['GET', 'POST'])
    def confirm_payment_view(self, request, payment_pk):
        if request.method == 'GET':
            form = ConfirmPay()
        else:
            form = ConfirmPay(request.POST)
            if form.is_valid():
                return self.confirm_payment_process(
                    request=request,
                    code_confirm=form.cleaned_data['code_confirm'],
                    payment_pk=payment_pk
                )
        return render(
            request=request,
            template_name='deal/confirm_payment.html',
            context={
                'form': form,
                'payment_pk': payment_pk
            }
        )

    @handle_api_response
    def confirm_payment_process(
            self,
            request,
            code_confirm,
            payment_pk
        ):
        try:
            payment = Payment.objects.get(pk=payment_pk)
            key_payment = confirm_payment(
                invoice=payment.number_invoice_provider,
                code_confirm=code_confirm
            )
            payment.key = key_payment
            payment.save()

            # отправим задачу на операцию платежа в celery
            # если celery ответил да, то нужно изменить статус платежа

            self.message_user(
                request=request,
                message='Платеж обрабатывается. Можете продолжить работу',
                level=messages.SUCCESS,
            )
            return redirect(
                reverse(
                    viewname='admin:deal_offer_changelist'
                )
            )
        except ObjectDoesNotExist:
            return self.redirect_with_message(
                request=request,
                message='Нет такой сделки',
                type_message=messages.WARNING,
                redirect_to=request.META['HTTP_REFERER'],
            )


class PaymentAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            deal__buyer=request.user
        )


admin.site.register(Status)
admin.site.register(Commission, CommissionAdmin)
admin.site.register(Offer, OfferAdmin)
admin.site.register(Deal, DealAdmin)
admin.site.register(Payment, PaymentAdmin)