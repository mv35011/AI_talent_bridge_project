import tiktoken
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required

from transformers import pipeline
import time
from .forms import UserRegistrationForm, UserProfileForm
from .models import UserProfile
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .resume_utils import ResumeOptimizer
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from fpdf import FPDF
import tempfile
import os
from django.core.files.base import ContentFile
from asgiref.sync import sync_to_async
import torch
from django.conf import settings
import PyPDF2
from time import sleep
import io
from .llm_service import LLMService
from transformers import AutoTokenizer, AutoModelForCausalLM
from google.generativeai import GenerativeModel
from google.api_core import retry
import google.generativeai as genai


from django.core.cache import cache
logger = logging.getLogger(__name__)
def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)

        if user_form.is_valid() and profile_form.is_valid():
            try:

                user = user_form.save()


                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()


                profile.update_score()
                print(f"Profile score after update: {profile.score}")  # Debug print


                login(request, user)
                messages.success(request, 'Registration successful!')
                return redirect('dashboard')
            except Exception as e:
                print(f"Error during registration: {e}")
                messages.error(request, 'An error occurred during registration.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserRegistrationForm()
        profile_form = UserProfileForm()

    return render(request, 'members/register.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


@login_required

def profile(request):
    user_profile = request.user.userprofile
    return render(request, 'members/profile_detail.html', {'profile': user_profile})

def home(request):
    return render(request, 'members/home.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'members/login.html')
@login_required
def dashboard(request):
    user_profile = request.user.userprofile
    top_profiles = UserProfile.objects.all().order_by('-score')[:10]
    context ={
        'user_profile': user_profile,
        'top_profiles': top_profiles,
    }
    return render(request, 'members/dashboard.html', context)
@login_required
def profile_detail(request, user_id):
    profile = get_object_or_404(UserProfile, user_id= user_id)
    return render(request, 'members/profile_detail.html', {'profile':profile})
@login_required
def resume_optimizer_page(request):
    """Render the resume optimizer tool page"""
    user_profile = UserProfile.objects.get(user=request.user)
    context = {
        'has_current_resume': bool(user_profile.resume)
    }
    return render(request, 'members/resume_optimizer.html')
@login_required
@csrf_exempt
async def optimize_resume(request):
    """Handle resume optimization and update"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:

        user_profile = await sync_to_async(UserProfile.objects.get)(user=request.user)


        if 'resume' in request.FILES:
            resume_file = request.FILES['resume']
        elif user_profile.resume:
            resume_file = user_profile.resume.file
        else:
            return JsonResponse({'success': False, 'error': 'No resume found'})


        optimizer = ResumeOptimizer()
        results = await optimizer.process_resume(resume_file)


        request.session['optimization_results'] = {
            'text': results['optimized_text'],
            'score': results['optimized_score'],
        }

        return JsonResponse({
            'success': True,
            'current_score': results['current_score'],
            'optimized_score': results['optimized_score'],
            'suggestions': results['suggestions'],
            'optimized_text': results['optimized_text'],
            'requires_confirmation': True
        })

    except Exception as e:
        logger.error(f"Error in resume optimization: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def apply_optimization(request):

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:

        optimization_results = request.session.get('optimization_results')
        if not optimization_results:
            return JsonResponse({'success': False, 'error': 'No optimization results found'})

        user_profile = UserProfile.objects.get(user=request.user)


        filename = f"optimized_resume_{request.user.username}.pdf"
        user_profile.resume.save(
            filename,
            ContentFile(optimization_results['pdf_content']),
            save=True
        )


        del request.session['optimization_results']

        return JsonResponse({
            'success': True,
            'message': 'Resume successfully updated',
            'new_score': optimization_results['score']
        })

    except Exception as e:
        logger.error(f"Error applying optimization: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


def extract_text_from_pdf(pdf_file):

    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text.strip()
    except Exception as e:
        print(f"PDF extraction error: {str(e)}")
        raise Exception("Could not read PDF file. Please ensure it's a valid PDF document.")


@login_required
def career_roadmap(request):
    if request.method == 'POST' and request.FILES.get('resume'):
        try:
            resume_file = request.FILES['resume']
            career_path = request.POST.get('career_path')


            try:
                resume_text = extract_text_from_pdf(resume_file)
                if not resume_text:
                    raise Exception("No text could be extracted from the PDF")
            except Exception as e:
                return render(request, 'members/career_roadmap.html', {
                    'error': f"PDF Error: {str(e)}"
                })


            try:
                llm_service = LLMService.get_instance()
                roadmap = llm_service.generate_roadmap(resume_text, career_path)

                # Get career path display name
                career_path_display = llm_service.CAREER_CONTEXTS[career_path]['title']

                return render(request, 'members/career_roadmap.html', {
                    'roadmap': roadmap,
                    'career_path': career_path_display
                })
            except Exception as e:
                return render(request, 'members/career_roadmap.html', {
                    'error': f"Roadmap Generation Error: {str(e)}"
                })

        except Exception as e:
            return render(request, 'members/career_roadmap.html', {
                'error': f"An error occurred: {str(e)}"
            })

    return render(request, 'members/career_roadmap.html')
@login_required
def skills_gap_analyzer(request, profile_id):
    # Your view logic here
    return render(request, 'your_template.html')


@login_required
def profile_view(request, profile_id):


    profile = get_object_or_404(UserProfile, id=profile_id)


    skills_list = profile.skills if isinstance(profile.skills, list) else []


    context = {
        'profile': {
            'user': profile.user,
            'full_name': profile.full_name,
            'department': profile.get_department_display(),
            'college_email': profile.college_email,
            'phone_number': profile.phone_number,
            'profile_photo': profile.profile_photo,
            'score': profile.score,
            'skills': skills_list,
            'resume': profile.resume,
            'date_joined': profile.date_joined,
        }
    }

    return render(request, 'members/profile_detail.html', context)


@login_required
def update_score(request):

    if request.method == 'POST':
        try:
            profile = get_object_or_404(UserProfile, user=request.user)
            profile.update_score()
            return redirect('profile', profile_id=profile.id)
        except Exception as e:

            print(f"Error updating score: {e}")

            return redirect('profile', profile_id=profile.id)

    return redirect('profile', profile_id=request.user.userprofile.id)


genai.configure(api_key=settings.GEMINI_API_KEY)
model = GenerativeModel('gemini-pro')

@login_required
def chat_response(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'error': 'Empty message'}, status=400)

        system_prompt = """You are a professional career advisor specializing in technology careers. 
        Provide specific, actionable advice focused on:
        - Career planning and development
        - Job search strategies
        - Technical skills needed
        - Learning resources
        - Industry trends
        -Engineeringt skills specially AI/ML, Web Dev, Android Development
        Be concise but informative in your responses."""


        full_prompt = f"{system_prompt}\n\nUser: {user_message}"


        @retry.Retry(predicate=retry.if_exception_type(Exception))
        def generate_response():
            chat = model.start_chat(history=[])
            response = chat.send_message(full_prompt)
            return response.text

        max_retries = 3
        retry_count = 0
        retry_delay = 1

        while retry_count < max_retries:
            try:
                bot_response = generate_response()
                break
            except Exception as e:
                if retry_count == max_retries - 1:
                    if "quota" in str(e).lower():
                        return JsonResponse({
                            'error': 'API quota exceeded. Please try again later.'
                        }, status=429)
                    return JsonResponse({
                        'error': 'Service temporarily unavailable.'
                    }, status=503)
                retry_count += 1
                time.sleep(retry_delay)
                retry_delay *= 2


        chat_history = request.session.get('chat_history', [])
        chat_history.extend([
            {'content': user_message, 'is_user': True},
            {'content': bot_response, 'is_user': False}
        ])
        request.session['chat_history'] = chat_history[-10:]
        request.session.modified = True

        return JsonResponse({'response': bot_response})

    except Exception as e:
        print(f"Error in chat_response: {str(e)}")
        return JsonResponse({
            'error': 'An unexpected error occurred. Please try again later.'
        }, status=500)

@login_required
def chatbot_view(request):
    if 'chat_history' not in request.session:
        request.session['chat_history'] = [{
            'content': """Hello! I'm your Career AI Assistant. I can help you with:
- Career planning and guidance
- Job search strategies
- Resume and interview preparation
- Skill development advice
- Industry insights
- Professional growth

What would you like to discuss?""",
            'is_user': False
        }]

    return render(request, 'members/chatbot.html', {
        'chat_history': request.session['chat_history']
    })