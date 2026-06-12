from django.urls import path
from django.views.generic import RedirectView

from . import views


urlpatterns = [
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('experience/', views.experience, name='experience'),
    path('case-studies/', views.case_studies, name='case_studies'),
    path('dev/login/', views.dashboard_login, name='dashboard_login'),
    path('dev/logout/', views.dashboard_logout, name='dashboard_logout'),
    path('dev/', views.dev_overview, name='dev'),
    path('dev/inquiries/', views.inquiry_dashboard, name='dev_inquiries'),
    path('dev/inquiries/<int:inquiry_id>/', views.inquiry_detail, name='inquiry_detail'),
    path('dev/inquiries/<int:inquiry_id>/toggle-read/', views.toggle_inquiry_read, name='toggle_inquiry_read'),
    path('dev/blog-analytics/', views.blog_analytics_dashboard, name='dev_blog_analytics'),
    path('dev/smtp/', views.smtp_test, name='dev_smtp'),
    path('dev/health/', views.site_health, name='dev_health'),
    path('dev/content/', views.content_overview, name='dev_content'),
    path('dev/content/<slug:content_type>/', views.content_list, name='dev_content_list'),
    path('dev/content/<slug:content_type>/new/', views.content_create, name='dev_content_create'),
    path('dev/content/<slug:content_type>/<int:item_id>/edit/', views.content_edit, name='dev_content_edit'),
    path('dev/content/<slug:content_type>/<int:item_id>/delete/', views.content_delete, name='dev_content_delete'),
    path('dev/users/', views.dashboard_users, name='dashboard_users'),
    path('dev/users/new/', views.dashboard_user_create, name='dashboard_user_create'),
    path('dev/users/<int:user_id>/edit/', views.dashboard_user_edit, name='dashboard_user_edit'),
    path('dev/users/<int:user_id>/deactivate/', views.dashboard_user_deactivate, name='dashboard_user_deactivate'),
    path('dev/users/<int:user_id>/reactivate/', views.dashboard_user_reactivate, name='dashboard_user_reactivate'),
    path('dev/users/<int:user_id>/reset-password/', views.dashboard_user_reset_password, name='dashboard_user_reset_password'),
    path('dashboard/', RedirectView.as_view(pattern_name='dev', permanent=False), name='dashboard'),
    path('dashboard/inquiries/', RedirectView.as_view(pattern_name='dev_inquiries', permanent=False, query_string=True), name='dashboard_inquiries'),
    path('dashboard/inquiries/<int:inquiry_id>/', RedirectView.as_view(pattern_name='inquiry_detail', permanent=False), name='dashboard_inquiry_detail'),
    path('dashboard/inquiries/<int:inquiry_id>/toggle-read/', views.toggle_inquiry_read, name='toggle_inquiry_read_legacy'),
    path('dashboard/logout/', RedirectView.as_view(pattern_name='dashboard_logout', permanent=False), name='dashboard_logout_legacy'),

    # Newsletter — public
    path('blog/subscribe/', views.subscribe, name='blog_subscribe'),
    path('blog/confirm/<str:token>/', views.confirm_subscription, name='blog_confirm_subscription'),
    path('blog/unsubscribe/<str:token>/', views.unsubscribe_view, name='blog_unsubscribe'),

    # Newsletter — dashboard
    path('dev/newsletter/', views.newsletter_dashboard, name='dev_newsletter'),
    path('dev/newsletter/send/', views.send_digest, name='dev_send_digest'),
]
