from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from .models import JobSeeker, Recruiter , Job , Application
from .forms import SeekerRegisterForm, RecruiterRegisterForm, LoginForm , JobForm , ApplicationForm


def register_seeker(request):
    if request.method == 'POST':
        form = SeekerRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Job Seeker registered successfully. Please login.")
            return redirect('login')
        else:
            messages.error(request, "Error in registration form. Please check your inputs.")
    else:
        form = SeekerRegisterForm()
    return render(request, 'register_seeker.html', {'form': form})


def register_recruiter(request):
    if request.method == 'POST':
        form = RecruiterRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Recruiter registered successfully. Please login.")
            return redirect('login')
        else:
            messages.error(request, "Error in registration form. Please check your inputs.")
    else:
        form = RecruiterRegisterForm()
    return render(request, 'register_recruiter.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user_type = form.cleaned_data['user_type']

            if user_type == 'seeker':
                try:
                    seeker = JobSeeker.objects.get(username=username)
                    if check_password(password, seeker.password_hash):
                        request.session['user_id'] = seeker.seeker_id
                        request.session['user_type'] = 'seeker'
                        messages.success(request, f"Welcome back, {seeker.username}!")
                        return redirect('seeker_home')
                except JobSeeker.DoesNotExist:
                    pass

            elif user_type == 'recruiter':
                try:
                    recruiter = Recruiter.objects.get(username=username)
                    if check_password(password, recruiter.password_hash):
                        request.session['user_id'] = recruiter.recruiter_id
                        request.session['user_type'] = 'recruiter'
                        messages.success(request, f"Welcome back, {recruiter.username}!")
                        return redirect('recruiter_home')
                except Recruiter.DoesNotExist:
                    pass

            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    request.session.flush()
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


from django.shortcuts import render
from django.db.models import Q
from .models import Job, Application, Resume  # Ensure all necessary models are imported

def seeker_home(request):
    """Handles job search and filtering for job seekers."""
    
    query = request.GET.get('q', '').strip()
    location = request.GET.get('location', '').strip()
    job_type = request.GET.get('job_type', '').strip()
    min_salary = request.GET.get('min_salary', '').strip()
    max_salary = request.GET.get('max_salary', '').strip()
    experience = request.GET.get('experience', '').strip()

    # Start with all active jobs
    jobs = Job.objects.filter(status="active")

    # Keyword-based search: title, description, requirements, skills
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(requirements__icontains=query) |
            Q(skills__icontains=query) |
            Q(recruiter__company__name__icontains=query)  # Add company name search
        )

    # Location filter
    if location:
        jobs = jobs.filter(location__icontains=location)

    # Job type filter
    if job_type:
        jobs = jobs.filter(employment_type=job_type)

    # Salary range filter (Note: This uses regex, which can be complex to maintain. 
    # It assumes the salary_range field is a text string like "50k-80k")
    if min_salary:
        # Filter where the string starts with or contains the minimum value
        jobs = jobs.filter(salary_range__regex=rf'^{min_salary}|{min_salary,}')
    if max_salary:
        # Filter where the string ends with or contains the maximum value
        jobs = jobs.filter(salary_range__regex=rf'.*{max_salary}$|{max_salary,}')

    if experience:
        jobs = jobs.filter(requirements__icontains=experience)

    context = {
        # Prefetch the company name to avoid N+1 queries in the template
        "jobs": jobs.select_related("recruiter__company").order_by('-posted_at'), 
    }
    return render(request, "seeker_home.html", context)


def job_detail(request, job_id):
    job = get_object_or_404(Job, pk=job_id)

    # Safely split comma-separated skills
    skills_list = job.skills.split(',') if job.skills else []

    return render(request, 'job_detail.html', {
        'job': job,
        'skills_list': skills_list
    })



from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Job, Resume, Application, JobSeeker, Recruiter

def apply_job(request, job_id):
    if not request.session.get("user_id") or request.session.get("user_type") != "seeker":
        messages.error(request, "You must be logged in as a job seeker to apply.")
        return redirect("login")

    seeker_id = request.session["user_id"]
    job = get_object_or_404(Job, pk=job_id, status="active")

    try:
        resume = Resume.objects.get(seeker_id=seeker_id)
    except Resume.DoesNotExist:
        messages.error(request, "You must upload a resume before applying.")
        return redirect("seeker_home")

    existing = Application.objects.filter(job=job, seeker_id=seeker_id).first()
    if existing:
        messages.info(request, "You have already applied for this job.")
        return redirect("seeker_home")

    application = Application.objects.create(
        job=job,
        seeker_id=seeker_id,
        resume=resume,
        status="applied",
        applied_at=timezone.now(),
        updated_at=timezone.now(),
    )

    seeker = JobSeeker.objects.get(pk=seeker_id)
    recruiter = job.recruiter  # Already tied through FK

    # Email to Seeker (Confirmation)
    seeker_subject = f"Application Submitted: {job.title}"
    seeker_message = (
        f"Hello {seeker.username},\n\n"
        f"You have successfully applied for the job '{job.title}'.\n"
        f"The recruiter will review your application and update the status.\n\n"
        "Best of luck!\nJob Portal Team"
    )
    send_mail(
        seeker_subject,
        seeker_message,
        settings.DEFAULT_FROM_EMAIL,
        [seeker.email],
        fail_silently=True
    )

    # Email to Recruiter (Notification)
    recruiter_subject = f"New Application for {job.title}"
    recruiter_message = (
        f"Hello {recruiter.username},\n\n"
        f"{seeker.username} has applied for your job posting '{job.title}'.\n"
        f"Please review the application from your dashboard.\n\n"
        "Regards,\nJob Portal System"
    )
    send_mail(
        recruiter_subject,
        recruiter_message,
        settings.DEFAULT_FROM_EMAIL,
        [recruiter.email],
        fail_silently=True
    )

    messages.success(request, "Application submitted successfully.")
    return redirect("seeker_home")


def my_applications(request):
    if request.session.get('user_type') != 'seeker':
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    seeker = JobSeeker.objects.get(pk=request.session['user_id'])
    applications = Application.objects.filter(seeker=seeker).select_related('job', 'resume')

    return render(request, 'my_applications.html', {'applications': applications})




from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Count
# Ensure you have imported your models: from .models import Recruiter, Job, Application

def recruiter_home(request):
    """
    Renders the Recruiter Dashboard, showing job summaries and application insights.
    """
    # 1. Authentication and Setup (Keep this intact)
    if not request.session.get("user_id") or request.session.get("user_type") != "recruiter":
        messages.error(request, "Please log in as a recruiter.")
        return redirect("login")

    recruiter_id = request.session["user_id"]
    try:
        recruiter = Recruiter.objects.get(pk=recruiter_id)
    except Recruiter.DoesNotExist:
        messages.error(request, "Recruiter profile not found.")
        return redirect("login")


    # 2. Core Data Retrieval
    jobs = Job.objects.filter(recruiter=recruiter).order_by('-posted_at')
    total_jobs = jobs.count()

    # Get applications related to the recruiter's jobs
    applications = Application.objects.filter(job__in=jobs)
    total_applications = applications.count()


    # 3. Data Visualization & Insights Calculation (NEW)
    
    # Calculate applications grouped by status
    status_counts = applications.values('status').annotate(count=Count('status'))
    
    # Convert the queryset result into a dictionary for easier template access
    status_dict = {item['status']: item['count'] for item in status_counts}
    
    # Prepare the data for the template (matching the defined STATUS_CHOICES)
    status_data = []
    # Use the choices from the Application model to ensure all statuses are present
    for value, label in Application.STATUS_CHOICES:
        count = status_dict.get(value, 0)
        
        # Determine color for visualization
        color = 'info'
        if value == 'shortlisted':
            color = 'secondary'
        elif value == 'interview':
            color = 'primary'
        elif value == 'hired':
            color = 'success'
        elif value == 'rejected':
            color = 'danger'
            
        status_data.append({
            'label': label,
            'count': count,
            'value': value,
            'color': color,
            'percentage': (count / total_applications * 100) if total_applications else 0
        })

    
    # 4. Context for Template
    context = {
        "recruiter": recruiter,
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "jobs": jobs[:5],  # show recent 5 jobs
        "status_data": status_data,
        "total_active_jobs": jobs.filter(status='active').count(),
    }
    return render(request, "recruiter_home.html", context)


def index(request):
    return render(request, 'index.html')


from django.shortcuts import get_object_or_404
from .forms import ResumeForm, CompanyForm
from .models import Resume, Company


# Seeker Resume Upload/Edit
def seeker_resume(request):
    if 'user_id' not in request.session or request.session.get('user_type') != 'seeker':
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    seeker_id = request.session['user_id']
    resume, created = Resume.objects.get_or_create(seeker_id=seeker_id)

    if request.method == 'POST':
        form = ResumeForm(request.POST, request.FILES, instance=resume)
        if form.is_valid():
            form.save()
            messages.success(request, "Resume uploaded/updated successfully.")
            return redirect('seeker_home')
    else:
        form = ResumeForm(instance=resume)

    return render(request, 'seeker_resume.html', {'form': form})


# Recruiter Company Profile Add/Edit
def recruiter_company(request):
    if 'user_id' not in request.session or request.session.get('user_type') != 'recruiter':
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    recruiter_id = request.session['user_id']
    company, created = Company.objects.get_or_create(recruiter_id=recruiter_id)

    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Company profile updated successfully.")
            return redirect('recruiter_home')
    else:
        form = CompanyForm(instance=company)

    return render(request, 'recruiter_company.html', {'form': form})


# List Jobs
def job_list(request):
    if request.session.get('user_type') != 'recruiter':
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    recruiter_id = request.session['user_id']
    jobs = Job.objects.filter(recruiter_id=recruiter_id)
    return render(request, 'jobs/job_list.html', {'jobs': jobs})



from django.core.mail import send_mass_mail
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Job, JobSeeker
from .forms import JobForm


# Create Job
def job_create(request):
    if request.session.get('user_type') != 'recruiter':
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.recruiter_id = request.session['user_id']
            job.save()

            #  Send email notifications to all seekers
            seekers = JobSeeker.objects.all().values_list('email', flat=True)

            subject = f"New Job Posted: {job.title}"
            message = (
                f"A new job has been posted that may match your skills.\n\n"
                f"Title: {job.title}\n"
                f"Description: {job.description}\n"
                f"Requirements: {job.requirements}\n\n"
                f"Visit the portal to apply."
            )
            from_email = settings.DEFAULT_FROM_EMAIL

            email_messages = [
                (subject, message, from_email, [email]) for email in seekers
            ]

            if email_messages:
                send_mass_mail(email_messages, fail_silently=True)

            messages.success(request, "Job posted successfully, and notifications sent.")
            return redirect('job_list')
    else:
        form = JobForm()

    return render(request, 'jobs/job_form.html', {'form': form, 'action': 'Create'})


# Update Job
def job_update(request, job_id):
    job = get_object_or_404(Job, pk=job_id, recruiter_id=request.session.get('user_id'))

    if request.session.get('user_type') != 'recruiter':
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully.")
            return redirect('job_list')
    else:
        form = JobForm(instance=job)

    return render(request, 'jobs/job_form.html', {'form': form, 'action': 'Update'})

# Delete Job
def job_delete(request, job_id):
    job = get_object_or_404(Job, pk=job_id, recruiter_id=request.session.get('user_id'))
    if request.session.get('user_type') != 'recruiter':
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    if request.method == 'POST':
        job.delete()
        messages.success(request, "Job deleted successfully.")
        return redirect('job_list')

    return render(request, 'jobs/job_confirm_delete.html', {'job': job})



from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Resume, ParsedResume
from .utils import parse_resume
import os

def resume_ranking(request):
    if not request.session.get("user_id") or request.session.get("user_type") != "seeker":
        messages.error(request, "You must be logged in as a job seeker.")
        return redirect("login")

    seeker_id = request.session["user_id"]

    try:
        # Always fetch latest resume (since OneToOneField ensures only one resume per seeker)
        resume = Resume.objects.get(seeker_id=seeker_id)
    except Resume.DoesNotExist:
        messages.error(request, "You must upload a resume first.")
        return redirect("seeker_home")

    # Force re-parse if resume file is updated or parsed_resume missing
    parsed_resume, created = ParsedResume.objects.get_or_create(resume=resume)

    # Check if parsing is needed (new upload or empty fields)
    if created or not parsed_resume.skills or parsed_resume.created_at < resume.updated_at:
        file_path = resume.file_path.path
        parsed_data = parse_resume(file_path)

        parsed_resume.full_name = parsed_data.get("full_name")
        parsed_resume.email = parsed_data.get("email")
        parsed_resume.phone = parsed_data.get("phone")
        parsed_resume.skills = parsed_data.get("skills")
        parsed_resume.education = parsed_data.get("education")
        parsed_resume.keywords = parsed_data.get("keywords")
        parsed_resume.work_experience = parsed_data.get("work_experience")
        parsed_resume.years_of_experience = parsed_data.get("years_of_experience")
        parsed_resume.save()

        messages.success(request, "Resume parsed successfully from latest upload!")

    return render(request, "resume_ranking.html", {"parsed_resume": parsed_resume})


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ParsedResume, Job
from .job_matching import rank_resume_for_job


def match_jobs_for_seeker(request):
    if 'user_id' not in request.session or request.session.get('user_type') != 'seeker':
        messages.error(request, "Unauthorized access.")
        return redirect('login')

    seeker_id = request.session['user_id']

    parsed_resume = ParsedResume.objects.filter(resume__seeker__seeker_id=seeker_id).first()
    if not parsed_resume:
        messages.error(request, "You must upload and parse a resume first.")
        return redirect('seeker_home')

    seeker_resume_dict = {
        "resume_id": parsed_resume.resume.resume_id,
        "full_name": parsed_resume.full_name,
        "email": parsed_resume.email,
        "skills": parsed_resume.skills,
        "work_experience": parsed_resume.work_experience,
        "education": parsed_resume.education,
        "keywords": parsed_resume.keywords,
        "years_of_experience": parsed_resume.years_of_experience
    }

    ranked_jobs = []
    all_jobs = Job.objects.all()

    for job in all_jobs:
        job_dict = {
            "title": job.title,
            "description": job.description,
            "requirements": job.requirements,
            "skills": job.requirements.split(", ") if job.requirements else [],  # Use ", " to avoid splitting on commas within skill names
            "min_experience": job.min_experience if hasattr(job, "min_experience") else None
        }
        score_data = rank_resume_for_job(job_dict, seeker_resume_dict)
        # Only include jobs with a final score >= 0.5
        if score_data.get("final_score", 0) >= 0.5:
            ranked_jobs.append({
                "job": job,
                "score": score_data.get("final_score", 0),
                "matched_skills": score_data.get("matched_skills", []),
                "technical_skill_score": score_data.get("technical_skill_overlap", 0),
                "soft_skill_score": score_data.get("soft_skill", 0),
                "experience_score": score_data.get("experience_score", 0),
                "keyword_relevance_score": score_data.get("keyword_relevance", 0),
                "semantic_sim_score": score_data.get("semantic_sim", 0)
            })

    ranked_jobs.sort(key=lambda x: x["score"], reverse=True)

    return render(request, "matched_jobs.html", {
        "ranked_jobs": ranked_jobs
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Application, Job, ParsedResume
from .job_matching import rank_resume_for_job

def recruiter_applications(request):
    if not request.session.get("user_id") or request.session.get("user_type") != "recruiter":
        messages.error(request, "Please log in as a recruiter.")
        return redirect("login")

    recruiter_id = request.session["user_id"]
    jobs = Job.objects.filter(recruiter_id=recruiter_id)
    applications = Application.objects.filter(job__in=jobs).select_related('job', 'seeker', 'resume')

    # --- Get filter from query params ---
    min_score_param = request.GET.get("min_score")
    try:
        min_score = float(min_score_param) / 100 if min_score_param else 0
    except ValueError:
        min_score = 0

    ranked_applications = []
    for app in applications:
        parsed_resume = ParsedResume.objects.filter(resume=app.resume).first()
        if not parsed_resume:
            continue

        seeker_resume_dict = {
            "resume_id": parsed_resume.resume.resume_id,
            "full_name": parsed_resume.full_name,
            "email": parsed_resume.email,
            "skills": parsed_resume.skills,
            "work_experience": parsed_resume.work_experience,
            "education": parsed_resume.education,
            "keywords": parsed_resume.keywords,
            "years_of_experience": parsed_resume.years_of_experience
        }

        job = app.job
        job_dict = {
            "title": job.title,
            "description": job.description,
            "requirements": job.requirements,
            "skills": job.requirements.split(", ") if job.requirements else [],
            "min_experience": getattr(job, "min_experience", None)
        }

        score_data = rank_resume_for_job(job_dict, seeker_resume_dict)
        final_score = score_data.get("final_score", 0)

        # Apply filter here
        if final_score >= min_score:
            ranked_applications.append({
                "application": app,
                "score": final_score,
                "score_percentage": round(final_score * 100, 2)
            })

    ranked_applications.sort(key=lambda x: x["score"], reverse=True)

    return render(request, 'recruiter_applications.html', {
        "ranked_applications": ranked_applications,
        "applications": applications,
        "min_score": min_score_param if min_score_param else ""
    })


from django.core.mail import send_mail
from django.conf import settings

def update_application_status(request, application_id):
    if not request.session.get("user_id") or request.session.get("user_type") != "recruiter":
        messages.error(request, "Unauthorized access.")
        return redirect("login")

    application = get_object_or_404(Application, pk=application_id)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(Application.STATUS_CHOICES):
            application.status = new_status
            application.save()

            # Send email to applicant
            seeker_email = application.seeker.email
            subject = f"Application Status Updated: {application.job.title}"
            message = (
                f"Hello {application.seeker.username},\n\n"
                f"The status of your application for the job '{application.job.title}' "
                f"has been updated to: {application.get_status_display()}.\n\n"
                f"Best regards,\n"
                f"Recruitment Team"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [seeker_email],
                fail_silently=True,
            )

            messages.success(request, "Application status updated and email sent.")
        else:
            messages.error(request, "Invalid status selected.")

    return redirect("recruiter_applications")


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Communication, Application, Recruiter, JobSeeker
from .forms import CommunicationForm

def send_message(request, application_id):
    user_type = request.session.get("user_type")
    user_id = request.session.get("user_id")

    if not user_id:
        messages.error(request, "Please log in.")
        return redirect("login")

    application = get_object_or_404(Application, pk=application_id)

    # Determine other user (just for UI/display)
    if user_type == "recruiter":
        other_user = application.seeker
    elif user_type == "seeker":
        other_user = application.job.recruiter
    else:
        messages.error(request, "Unauthorized access.")
        return redirect("login")

    # Fetch all communications for this application
    messages_qs = Communication.objects.filter(
        application=application
    ).order_by("sent_at")

    if request.method == "POST":
        form = CommunicationForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.application = application
            msg.save()
            return redirect("send_message", application_id=application_id)
    else:
        form = CommunicationForm()

    return render(request, "messages.html", {
        "form": form,
        "messages": messages_qs,
        "other_user": other_user
    })
