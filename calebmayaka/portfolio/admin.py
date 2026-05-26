from django.contrib import admin

from .models import (
    CaseStudy,
    DashboardUserProfile,
    Experience,
    Inquiry,
    NavItem,
    Project,
    Skill,
    SiteProfile,
    SocialLink,
    Stat,
    TechStack,
    Testimonial,
)


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


@admin.register(SiteProfile)
class SiteProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'email', 'location')

    def has_add_permission(self, request):
        return not SiteProfile.objects.exists()


@admin.register(NavItem)
class NavItemAdmin(admin.ModelAdmin):
    list_display = ('label', 'url_name', 'url', 'order')
    ordering = ('order',)


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ('label', 'url', 'order')
    ordering = ('order',)


@admin.register(Stat)
class StatAdmin(admin.ModelAdmin):
    list_display = ('value', 'label', 'order')
    ordering = ('order',)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    search_fields = ('title', 'description')
    ordering = ('order',)


@admin.register(TechStack)
class TechStackAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering = ('order',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'order')
    search_fields = ('title', 'description', 'category')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order',)


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('role', 'company', 'period', 'order')
    search_fields = ('role', 'company')
    ordering = ('order',)


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'duration', 'order')
    search_fields = ('title', 'description', 'category')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order',)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'title', 'order')
    search_fields = ('name', 'quote')
    ordering = ('order',)
