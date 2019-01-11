from django.contrib import admin

from deal.models import Status, Commission, Offer


class OfferAdmin(admin.ModelAdmin):
    exclude = ('user',)

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def get_queryset(self, request):
        return super().get_queryset(request).filter(user=request.user)


class CommissionAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if Commission.objects.exists():
            return False
        return True


admin.site.register(Status)
admin.site.register(Commission, CommissionAdmin)
admin.site.register(Offer, OfferAdmin)
