from django.contrib import admin

from user.models import Invoice
from deal.tasks import add


class InvoiceAdmin(admin.ModelAdmin):
    fields = ('num',)

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def get_queryset(self, request):
        add.delay(1, 2)
        if request.user.is_superuser:
            return super().get_queryset(request).filter()
        return super().get_queryset(request).filter(user=request.user.pk)


admin.site.register(Invoice, InvoiceAdmin)
