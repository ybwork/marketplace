from django.contrib import admin

from deal.models import Status, Commission, Offer
from django.utils.translation import ugettext_lazy as _


class OfferListFilter(admin.SimpleListFilter):
    title = _('My offers')
    parameter_name = 'filter'

    def lookups(self, request, model_admin):
        return (
            ('my', _('My offers')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'my':
            return queryset.filter(user=request.user)


class OfferAdmin(admin.ModelAdmin):
    exclude = ('user',)
    list_filter = (OfferListFilter,)

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    # def get_queryset(self, request):
    #     return super().get_queryset(request).filter(user=request.user)


# class AllOffersAdmin(admin.ModelAdmin):
#     def has_add_permission(self, request):
#         return False
#
#     def has_change_permission(self, request, obj=None):
#         return False
#
#     def has_delete_permission(self, request, obj=None):
#         return False
#
#     def get_queryset(self, request):
#         return super().get_queryset(request).exclude(user=request.user)


class CommissionAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if Commission.objects.exists():
            return False
        return True


admin.site.register(Status)
admin.site.register(Commission, CommissionAdmin)
admin.site.register(Offer, OfferAdmin)
# admin.site.register(OfferProxy, AllOffersAdmin)
