from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import TextAudio
import speech_recognition as sr

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
            return render(request, 'base/home.html')

        if audio:
            recognizer = sr.Recognizer()
            audio_file = sr.AudioFile(audio)
            with audio_file as source:
                audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                print(text)
            except sr.UnknownValueError:
                messages.warning(request, 'Could not understand the audio')
                return render(request, 'base/home.html')
            except sr.RequestError:
                messages.warning(request, 'Could not request results from Google Speech Recognition service')
                return render(request, 'base/home.html')

        TextAudio.objects.create(user=user, text=text, audio_file=audio)
        messages.success(request, 'Input successfully saved')
        return redirect('home') 

    return render(request, 'base/home.html')