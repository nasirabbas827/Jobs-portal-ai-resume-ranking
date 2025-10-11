from django import forms
from django.contrib.auth.hashers import make_password
from .models import JobSeeker, Recruiter, Resume, Company, Job, Application

class SeekerRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = JobSeeker
        fields = ['username', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        seeker = super().save(commit=False)
        seeker.password_hash = make_password(self.cleaned_data['password'])
        if commit:
            seeker.save()
        return seeker


class RecruiterRegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Recruiter
        fields = ['username', 'email', 'company_name', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        recruiter = super().save(commit=False)
        recruiter.password_hash = make_password(self.cleaned_data['password'])
        if commit:
            recruiter.save()
        return recruiter


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    user_type = forms.ChoiceField(choices=[('seeker', 'Job Seeker'), ('recruiter', 'Recruiter')], widget=forms.Select(attrs={'class': 'form-select'}))


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['file_path']
        widgets = {
            'file_path': forms.FileInput(attrs={'class': 'form-control'}),
        }


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'website', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'description', 'requirements', 'skills', 'location', 'salary_range', 'employment_type']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'skills': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g. Python, Django, AWS'
                }
            ),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'salary_range': forms.TextInput(attrs={'class': 'form-control'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
        }


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['resume']
        widgets = {
            'resume': forms.Select(attrs={'class': 'form-select'}),
        }