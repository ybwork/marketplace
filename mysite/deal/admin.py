from django.contrib import admin

from deal.models import Status, Commission, Offer
from django.template.response import TemplateResponse
from django.urls import path
from django.views.generic import FormView, DetailView

from deal.forms import BuyForm


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

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['offers'] = Offer.objects.all()
        return super().changelist_view(request, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['offer'] = Offer.objects.get(pk=object_id)
        return super().change_view(
            request,
            object_id,
            form_url='',
            extra_context=extra_context
        )

    def buy_view(self, request, offer_pk):
        context = dict(
           self.admin_site.each_context(request),
           my='hi',
        )
        return TemplateResponse(
            request,
            'deal/buy.html',
            context=context
        )

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path(
                '<int:offer_pk>/buy/',
                # self.admin_site.admin_view(BuyAdminView.as_view()),
                self.admin_site.admin_view(self.buy_view),
                name='buy'
            )
        ]
        return my_urls + urls


class CommissionAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if Commission.objects.exists():
            return False
        return True


admin.site.register(Status)
admin.site.register(Commission, CommissionAdmin)
admin.site.register(Offer, OfferAdmin)
