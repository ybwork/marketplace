from datetime import datetime, timedelta
from django.contrib import admin, messages
from deal.models import Status, Commission, Offer, Deal
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
from django.template.response import TemplateResponse
from django.urls import path, reverse

from deal.forms import DealPayForm
from deal.utils import available_request_methods
from deal.utils import is_enough_user_balance


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
    exclude = ('user',)
    list_display = ('name', 'price')
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
                '<int:deal_pk>/pay/',
                self.admin_site.admin_view(self.deal_pay_view),
                name='deal_pay'
            ),
            path(
                '<int:offer_pk>/confirm/',
                self.admin_site.admin_view(self.offer_confirm_view),
                name='offer_confirm'
            ),
        ]
        return my_urls + urls

    @available_request_methods(['GET', 'POST'])
    def deal_pay_view( self, request, deal_pk):
        if request.method == 'POST':
            form = DealPayForm(request.POST)
            if form.is_valid():
                if is_enough_user_balance(
                    invoice=form.cleaned_data['invoice'],
                    payment_amount=form.cleaned_data['payment_amount']
                ):
                    # редирект на окно для ввода кода для подтверждения
                    pass
                else:
                    self.message_user(
                        request=request,
                        message='Не хватает денег. '
                                'Используйте другой счет или заплатите меньше.',
                        level=messages.WARNING
                    )
                    return redirect(
                        reverse(
                            'admin:deal_pay',
                            kwargs={'deal_pk': deal_pk}
                        )
                    )

        form = DealPayForm()

        # Для вывода в select счетов текущего пользователя
        form.base_fields['invoice'].queryset = \
            form.base_fields['invoice'].queryset.filter(
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

    def offer_confirm_view(self, request, offer_pk):
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


admin.site.register(Status)
admin.site.register(Commission, CommissionAdmin)
admin.site.register(Offer, OfferAdmin)
admin.site.register(Deal, DealAdmin)