from django.contrib import admin

from deal.models import Status, Commission, Offer
from django.template import response


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
    list_display = ('name', 'price', 'limit_hours_on_pay')
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


class CommissionAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if Commission.objects.exists():
            return False
        return True


admin.site.register(Status)
admin.site.register(Commission, CommissionAdmin)
admin.site.register(Offer, OfferAdmin)
