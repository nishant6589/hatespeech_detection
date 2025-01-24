from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from .models import TextAudio 
# Create your views here.

@login_required(login_url='/login/')
def home(request):
    return render(request, 'base/home.html')

@login_required(login_url='/login/')
def take_input(request):
    if request.method == 'POST':
        user = request.user
        text = request.POST.get('input_text')
        audio = request.FILES.get('input_voice')
        if not (text or audio):
            messages.warning(request, 'Please provide either text or audio')
            return render('base/home.html')
    return render(request, 'base/home.html')