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


def seeker_home(request):
    query = request.GET.get('q', '')
    location = request.GET.get('location', '')

    jobs = Job.objects.filter(status="active")

    if query:
        jobs = jobs.filter(title__icontains=query)
    if location:
        jobs = jobs.filter(location__icontains=location)

    context = {
        "jobs": jobs.select_related("recruiter__company"),  # fetch recruiter + company efficiently
    }
    return render(request, "seeker_home.html", context)

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Job, Application, Resume

def apply_job(request, job_id):
    if not request.session.get("user_id") or request.session.get("user_type") != "seeker":
        messages.error(request, "You must be logged in as a job seeker to apply.")
        return redirect("login")

    seeker_id = request.session["user_id"]
    job = get_object_or_404(Job, pk=job_id, status="active")

    try:
        resume = Resume.objects.get(seeker_id=seeker_id)  # get the seeker's single resume
    except Resume.DoesNotExist:
        messages.error(request, "You must upload a resume before applying.")
        return redirect("seeker_home")

    # check if already applied
    existing = Application.objects.filter(job=job, seeker_id=seeker_id).first()
    if existing:
        messages.info(request, "You have already applied for this job.")
        return redirect("seeker_home")

    Application.objects.create(
        job=job,
        seeker_id=seeker_id,
        resume=resume,
        status="applied",
        applied_at=timezone.now(),
        updated_at=timezone.now(),
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




def recruiter_home(request):
    if not request.session.get("user_id") or request.session.get("user_type") != "recruiter":
        messages.error(request, "Please log in as a recruiter.")
        return redirect("login")

    recruiter_id = request.session["user_id"]
    recruiter = Recruiter.objects.get(pk=recruiter_id)

    # Recruiter’s jobs
    jobs = Job.objects.filter(recruiter=recruiter)
    total_jobs = jobs.count()

    # Applications related to recruiter’s jobs
    applications = Application.objects.filter(job__in=jobs)
    total_applications = applications.count()


    context = {
        "recruiter": recruiter,
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "jobs": jobs[:5],  # show recent 5 jobs
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
            messages.success(request, "Job posted successfully.")
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