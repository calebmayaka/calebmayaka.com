from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('experience/', views.experience, name='experience'),
    path('projects/', views.projects, name='projects'),
    path('case-studies/', views.case_studies, name='case_studies'),
    path('contact/', views.contact, name='contact'),
    path('dev/login/', views.dashboard_login, name='dashboard_login'),
    path('dev/', views.inquiry_dashboard, name='dev'),
    path('dev/inquiries/<int:inquiry_id>/', views.inquiry_detail, name='inquiry_detail'),
    path('dev/users/', views.dashboard_users, name='dashboard_users'),
    path('dev/users/new/', views.dashboard_user_create, name='dashboard_user_create'),
    path('dev/users/<int:user_id>/edit/', views.dashboard_user_edit, name='dashboard_user_edit'),
    path('dev/users/<int:user_id>/deactivate/', views.dashboard_user_deactivate, name='dashboard_user_deactivate'),
    path('dev/users/<int:user_id>/reactivate/', views.dashboard_user_reactivate, name='dashboard_user_reactivate'),
    path('dev/users/<int:user_id>/reset-password/', views.dashboard_user_reset_password, name='dashboard_user_reset_password'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/inquiries/', views.inquiry_dashboard, name='dashboard_inquiries'),
    path('dashboard/inquiries/<int:inquiry_id>/toggle-read/', views.toggle_inquiry_read, name='toggle_inquiry_read'),
    path('dashboard/logout/', views.dashboard_logout, name='dashboard_logout'),
]
