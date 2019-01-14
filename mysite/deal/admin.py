from django.contrib import admin

from deal.models import Status, Commission, Offer, NewOffer


class OfferAdmin(admin.ModelAdmin):
    exclude = ('user',)

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def get_queryset(self, request):
        return super().get_queryset(request).filter(user=request.user)


class AllOffersAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CommissionAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if Commission.objects.exists():
            return False
        return True


admin.site.register(Status)
admin.site.register(Commission, CommissionAdmin)
admin.site.register(Offer, OfferAdmin)
admin.site.register(NewOffer, AllOffersAdmin)
