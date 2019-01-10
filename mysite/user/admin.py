from django.contrib import admin

from user.models import Invoice


class InvoiceAdmin(admin.ModelAdmin):
    fields = ('num',)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(user=request.user.pk)

    def save_model(self, request, obj, form, change):
        obj.user_id = request.user.pk
        obj.save()


admin.site.register(Invoice, InvoiceAdmin)
