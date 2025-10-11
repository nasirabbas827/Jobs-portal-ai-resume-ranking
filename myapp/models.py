from django.db import models

class JobSeeker(models.Model):
    seeker_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username


class Recruiter(models.Model):
    recruiter_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

class Resume(models.Model):
    resume_id = models.AutoField(primary_key=True)
    seeker = models.OneToOneField(JobSeeker, on_delete=models.CASCADE)  # one seeker → one resume
    file_path = models.FileField(upload_to='resumes/')  # saves in MEDIA/resumes/
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Resume of {self.seeker.username}"


class Company(models.Model):
    company_id = models.AutoField(primary_key=True)
    recruiter = models.OneToOneField(Recruiter, on_delete=models.CASCADE)  # one recruiter → one company
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Job(models.Model):
    JOB_TYPES = [
        ('full-time', 'Full Time'),
        ('part-time', 'Part Time'),
        ('internship', 'Internship'),
        ('contract', 'Contract'),
    ]

    JOB_STATUS = [
        ('active', 'Active'),
        ('deactivate', 'Deactivate'),
        ('closed', 'Closed'),
    ]

    job_id = models.AutoField(primary_key=True)
    recruiter = models.ForeignKey(Recruiter, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField()

    # ✅ NEW FIELD: comma-separated skills
    skills = models.TextField(
        blank=True,
        null=True,
        help_text="Enter skills as comma-separated values, e.g., Python, Django, AWS"
    )

    location = models.CharField(max_length=255)
    salary_range = models.CharField(max_length=255, blank=True, null=True)
    employment_type = models.CharField(max_length=20, choices=JOB_TYPES)
    posted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=JOB_STATUS, default='active')

    def __str__(self):
        return f"{self.title} ({self.recruiter.username})"


class Application(models.Model):
    STATUS_CHOICES = [
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('interview', 'Interview'),
        ('rejected', 'Rejected'),
        ('hired', 'Hired'),
    ]

    application_id = models.AutoField(primary_key=True)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    seeker = models.ForeignKey(JobSeeker, on_delete=models.CASCADE, related_name="applications")
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.seeker.username} -> {self.job.title}"



class ParsedResume(models.Model):
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name="parsed_resume")
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    years_of_experience = models.FloatField(blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    certifications = models.TextField(blank=True, null=True)
    projects = models.TextField(blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)
    work_experience = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Parsed Resume of {self.resume.seeker.username}"
