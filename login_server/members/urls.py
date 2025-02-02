from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='members/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('profile/', views.profile, name='profile'),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),
    path('optimize-resume/', views.optimize_resume, name='optimize_resume'),
    path('tools/resume-optimizer/', views.resume_optimizer_page, name='resume_optimizer'),
    path('profile/<int:profile_id>/', views.profile_view, name='profile'),
    path('profile/<int:profile_id>/skills-gap/', views.skills_gap_analyzer, name='skills_gap_analyzer'),
    path('skills-gap-analyzer/', views.skills_gap_analyzer, name='skills_gap_analyzer'),
    path('update-score/', views.update_score, name='update_score'),
    path('apply-optimization/', views.apply_optimization, name='apply_optimization'),
    path('career-roadmap/', views.career_roadmap, name='career_roadmap'),
    path('chat/', views.chatbot_view, name='chatbot'),
    path('chat/response/', views.chat_response, name='chat_response'),
    path('profile/<int:user_id>/', views.profile_detail, name='profile_detail'),

]
