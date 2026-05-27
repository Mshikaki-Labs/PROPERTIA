from django.contrib import admin

from .models import Invitation, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number', 'notification_enabled')
    list_filter = ('role', 'notification_enabled')
    search_fields = ('user__username', 'user__email', 'phone_number')


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'role', 'status', 'invited_by', 'expires_at', 'accepted_at')
    list_filter = ('role', 'status')
    search_fields = ('email', 'invited_by__username')
    readonly_fields = ('token', 'created_at', 'accepted_at')
