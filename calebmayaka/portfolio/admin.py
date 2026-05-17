from django.contrib import admin

from .models import DashboardUserProfile, Inquiry


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('email', 'inquiry_type', 'is_read', 'created_at')
    list_filter = ('inquiry_type', 'is_read', 'created_at')
    search_fields = ('email', 'message')
    readonly_fields = ('email', 'inquiry_type', 'message', 'created_at')
    ordering = ('-created_at',)


@admin.register(DashboardUserProfile)
class DashboardUserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_at', 'updated_at')
    list_filter = ('role',)
    search_fields = ('user__username',)
