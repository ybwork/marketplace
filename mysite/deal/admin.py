from datetime import datetime, timedelta

from django.contrib import admin
from deal.models import Status, Commission, Offer
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse, reverse_lazy
from django.views.generic import FormView
from deal.forms import BuyForm

from deal.models import Deal


class OfferListFilter(admin.SimpleListFilter):
    title = 'My offers'
    parameter_name = 'filter'

    def lookups(self, request, model_admin):
        return (
            ('my', 'My offers'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'my':
            return queryset.filter(user=request.user)


class BuyAdminView(FormView):
    template_name = 'deal/buy.html'
    form_class = BuyForm
    success_url = reverse_lazy('admin:deal_offer_changelist')

    def get_context_data(self, **kwargs):
        self.form_class.base_fields['invoice'].queryset = \
            self.form_class.base_fields['invoice']\
                .queryset.filter(user=self.request.user)
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        # Будет отправка данных в банк клиент
        return super().form_valid(form)


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
            self._get_obj_does_not_exist_redirect(
                request,
                opts=self.model._meta,
                object_id=object_id
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
                '<int:offer_pk>/buy/',
                self.admin_site.admin_view(BuyAdminView.as_view()),
                name='buy'
            ),
            path(
                '<int:offer_pk>/confirm',
                self.admin_site.admin_view(self.offer_confirm_view),
                name='offer_confirm'
            ),
        ]
        return my_urls + urls

    def offer_confirm_view(self, request, offer_pk):
        try:
            offer = Offer.objects.get(pk=offer_pk)
        except ObjectDoesNotExist:
            return self._get_obj_does_not_exist_redirect(
                request,
                opts=self.model._meta,
                object_id=str(offer_pk)
            )

        if request.method == 'POST':
            status, created = Status.objects.get_or_create(
                name='Активна',
                defaults={
                    'name': 'Активна'
                }
            )
            deal = Deal.objects.create(
                user=request.user,
                buyer=offer.user,
                offer=offer,
                status=status,
                time_on_pay_expire=datetime.now() + timedelta(
                    hours=offer.limit_hours_on_pay
                )
            )
            return redirect(reverse('admin:user_invoice_changelist'))

        context = dict(
            offer=offer
        )
        return TemplateResponse(request, 'offer/confirm.html', context)


class CommissionAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if Commission.objects.exists():
            return False
        return True


admin.site.register(Status)
admin.site.register(Commission, CommissionAdmin)
admin.site.register(Offer, OfferAdmin)
