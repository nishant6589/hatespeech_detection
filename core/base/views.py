from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import os
import speech_recognition as sr
from pydub import AudioSegment
from .models import TextAudio
from django.conf import settings

@login_required(login_url='/login/')
def home(request):
    return render(request, 'base/home.html')

# Allowed audio file extensions
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".aac", ".m4a"}

def convert_audio_to_text(audio_path):
    """Convert an audio file to text using SpeechRecognition."""
    recognizer = sr.Recognizer()

    # Convert to .wav format if needed
    audio_extension = os.path.splitext(audio_path)[1].lower()
    if audio_extension != ".wav":
        converted_path = audio_path.replace(audio_extension, ".wav")
        audio = AudioSegment.from_file(audio_path, format=audio_extension[1:])
        audio.export(converted_path, format="wav")
        audio_path = converted_path

    # Recognize speech
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data)  # Convert speech to text
        except sr.UnknownValueError:
            return "Could not understand the audio"
        except sr.RequestError:
            return "Error connecting to speech recognition service"

@login_required(login_url='/login/')
def take_input(request):
    if request.method == 'POST':
        user = request.user
        text = request.POST.get('input_text')
        audio = request.FILES.get('input_voice')

        # Ensure at least one input is provided
        if not (text or audio):
            messages.warning(request, 'Please provide either text or audio')
            return render(request, 'base/home.html')

        # Process audio if provided
        transcribed_text = ""
        if audio:
            file_ext = os.path.splitext(audio.name)[1].lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                messages.error(request, 'Invalid audio format. Allowed formats: .mp3, .wav, .aac, .m4a')
                return render(request, 'base/home.html')

            # Ensure the temp_audio directory exists
            temp_audio_dir = os.path.join(settings.MEDIA_ROOT, 'temp_audio')
            os.makedirs(temp_audio_dir, exist_ok=True)

            # Save the audio file temporarily
            audio_path = os.path.join(temp_audio_dir, audio.name)
            with open(audio_path, 'wb+') as destination:
                for chunk in audio.chunks():
                    destination.write(chunk)

            # Convert audio to text
            transcribed_text = convert_audio_to_text(audio_path)

            # Clean up temporary file
            os.remove(audio_path)

        # Combine user text input (if any) with transcribed text
        final_text = text if text else transcribed_text
        print(final_text)   
        messages.success(request, 'Input received successfully!')
        TextAudio.objects.create(user=user, text=final_text, audio_file=audio)

        return render(request, 'base/home.html', {'text': final_text, 'audio': audio})

    return render(request, 'base/home.html')
