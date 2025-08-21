from django.contrib import admin
from .models import JobSeeker, Recruiter, Resume, Company, Job, Application, ParsedResume


@admin.register(JobSeeker)
class JobSeekerAdmin(admin.ModelAdmin):
    list_display = ("seeker_id", "username", "email", "created_at", "updated_at")
    search_fields = ("username", "email")
    ordering = ("-created_at",)


@admin.register(Recruiter)
class RecruiterAdmin(admin.ModelAdmin):
    list_display = ("recruiter_id", "username", "email", "company_name", "created_at")
    search_fields = ("username", "email", "company_name")
    ordering = ("-created_at",)


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("resume_id", "seeker", "uploaded_at", "updated_at")
    search_fields = ("seeker__username", "seeker__email")
    ordering = ("-uploaded_at",)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("company_id", "name", "recruiter", "website", "created_at")
    search_fields = ("name", "recruiter__username")
    ordering = ("-created_at",)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("job_id", "title", "recruiter", "employment_type", "status", "posted_at")
    search_fields = ("title", "recruiter__username", "location")
    list_filter = ("employment_type", "status", "posted_at")
    ordering = ("-posted_at",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("application_id", "job", "seeker", "status", "applied_at")
    search_fields = ("job__title", "seeker__username")
    list_filter = ("status", "applied_at")
    ordering = ("-applied_at",)


@admin.register(ParsedResume)
class ParsedResumeAdmin(admin.ModelAdmin):
    list_display = ("id", "resume", "full_name", "email", "phone", "years_of_experience", "created_at")
    search_fields = ("full_name", "email", "phone", "skills", "keywords")
    ordering = ("-created_at",)
