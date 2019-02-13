from django.contrib import admin
from django.contrib.auth.models import User

from user.models import Invoice


class InvoiceAdmin(admin.ModelAdmin):
    fields = ('num',)

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request).filter()
        return super().get_queryset(request).filter(user=request.user.pk)


admin.site.register(Invoice, InvoiceAdmin)
