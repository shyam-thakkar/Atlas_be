from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'plan_type', 'status', 'razorpay_order_id', 'razorpay_payment_id', 'created_at', 'updated_at')
    list_filter = ('status', 'plan_type', 'created_at')
    search_fields = ('user__email', 'razorpay_order_id', 'razorpay_payment_id')
    readonly_fields = ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'created_at', 'updated_at')
    
    fieldsets = (
        ('User Info', {'fields': ('user',)}),
        ('Payment Details', {'fields': ('amount', 'plan_type', 'status')}),
        ('Razorpay Details', {'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
