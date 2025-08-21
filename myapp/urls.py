from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/seeker/', views.register_seeker, name='register_seeker'),
    path('register/recruiter/', views.register_recruiter, name='register_recruiter'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('seeker/home/', views.seeker_home, name='seeker_home'),
    path('recruiter/home/', views.recruiter_home, name='recruiter_home'),
    path('seeker/resume/', views.seeker_resume, name='seeker_resume'),
    path('recruiter/company/', views.recruiter_company, name='recruiter_company'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/update/<int:job_id>/', views.job_update, name='job_update'),
    path('jobs/delete/<int:job_id>/', views.job_delete, name='job_delete'),
    path('seeker/apply/<int:job_id>/', views.apply_job, name='apply_job'),
    path('seeker/applications/', views.my_applications, name='my_applications'),
    path('seeker/resume-ranking/', views.resume_ranking, name="resume_ranking"),
]
