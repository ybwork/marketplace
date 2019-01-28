import requests
from datetime import datetime, timedelta

from django.contrib import admin, messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.urls import path, reverse

from deal.models import Status, Commission, Offer, Deal, Payment, StatusPayment
from deal.forms import ConfirmPay, DealPayForm
from deal.utils import available_request_methods, get_balance_user, pay, \
    check_user_balance, confirm_payment
from deal.exceptions import InternalServerError, NotFoundError, \
    UnauthorizedError, BadRequestError, OtherStatusCodes, NotEnoughMoney

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
            redirect_to,
            **kwargs
    ):
        self.message_user(
            request,
            message,
            type_message
        )
        return redirect(
            reverse(
                redirect_to,
                kwargs=kwargs
            )
        )


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
            return render(
                request=request,
                template_name='deal/pay.html',
                context={
                    'form': form,
                    'deal_pk': deal_pk,
                }
            )

        form = DealPayForm(request.POST)
        if form.is_valid():
            try:
                number_invoice_provider = form.cleaned_data['invoice'].num
                amount_money_payment = form.cleaned_data['amount_money']
                check_user_balance(
                    invoice=number_invoice_provider,
                    amount_money_payment=amount_money_payment
                )
                deal = Deal.objects.get(pk=deal_pk)
                number_invoice_reciever = deal.offer.money_to_invoice.num
                pay(
                    amount_money=amount_money_payment,
                    number_invoice_provider=number_invoice_provider,
                    number_invoice_reciever=number_invoice_reciever
                )
                payment = self.create_payment(
                    deal=deal,
                    amount_money_payment=amount_money_payment,
                    number_invoice_provider=number_invoice_provider,
                    number_invoice_reciever=number_invoice_reciever
                )
                return redirect(
                    reverse(
                        viewname='admin:deal_confirm_payment',
                        kwargs={'payment_pk': payment.pk}
                    )
                )
            except (
                requests.exceptions.ConnectionError,
                InternalServerError,
                UnauthorizedError
            ):
                return render(
                    request=request,
                    template_name='errors/500.html'
                )
            except ObjectDoesNotExist:
                return self.redirect_with_message(
                    request=request,
                    message='Нет такой сделки',
                    type_message=messages.WARNING,
                    redirect_to='admin:deal_pay',
                    deal_pk=deal_pk
                )
            except NotEnoughMoney:
                return self.redirect_with_message(
                    request=request,
                    message='Не хватает денег. Используйте другой счет или '
                            'заплатите меньше.',
                    type_message=messages.WARNING,
                    redirect_to='admin:deal_pay',
                    deal_pk=deal_pk
                )
            except NotFoundError:
                return self.redirect_with_message(
                    request=request,
                    message='Расчетный счет не валидный или не существует',
                    type_message=messages.WARNING,
                    redirect_to='admin:deal_pay',
                    deal_pk=deal_pk
                )
            except OtherStatusCodes:
                return render(
                    request=request,
                    template_name='errors/500.html'
                )
        else:
            return render(
                request=request,
                template_name='deal/pay.html',
                context={
                    'form': form,
                    'deal_pk': deal_pk,
                }
            )

    def create_payment(
            self,
            deal,
            amount_money_payment,
            number_invoice_provider,
            number_invoice_reciever
    ):
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
                request=request,
                template_name='deal/confirm_payment.html',
                context={
                    'form': form,
                    'payment_pk': payment_pk
                }
            )

        form = ConfirmPay(request.POST)
        if form.is_valid():
            try:
                payment = Payment.objects.get(pk=payment_pk)
                key_payment = confirm_payment(
                    invoice=payment.number_invoice_provider,
                    code_confirm=form.cleaned_data['code_confirm']
                )
                payment.key = key_payment
                payment.save()

                # отправим задачу на операцию платежа в celery

                return self.redirect_with_message(
                    request=request,
                    message='Платеж обрабатывается. Можете продолжить работу.',
                    type_message=messages.WARNING,
                    redirect_to='admin:deal_offer_changelist'
                )
            except ObjectDoesNotExist:
                return self.redirect_with_message(
                    request=request,
                    message='Нет такой сделки',
                    type_message=messages.WARNING,
                    redirect_to='admin:deal_confirm_payment',
                    payment_pk=payment_pk
                )
            except (
                requests.exceptions.ConnectionError,
                InternalServerError,
                UnauthorizedError
            ):
                return render(
                    request=request,
                    template_name='errors/500.html'
                )
            except BadRequestError:
                return self.redirect_with_message(
                    request=request,
                    message='Не правильный код подтверждения',
                    type_message=messages.WARNING,
                    redirect_to='admin:deal_confirm_payment',
                    payment_pk=payment_pk
                )
            except OtherStatusCodes:
                render(
                    request=request,
                    template_name='errors/500.html'
                )

        return render(
            request=request,
            template_name='deal/confirm_payment.html',
            context={
                'form': form,
                'payment_pk': payment_pk
            }
        )


admin.site.register(Status)
admin.site.register(Commission, CommissionAdmin)
admin.site.register(Offer, OfferAdmin)
admin.site.register(Deal, DealAdmin)
admin.site.register(Payment)