from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import os
import speech_recognition as sr
from pydub import AudioSegment
from .models import TextAudio
from django.conf import settings
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np
import re
import string
import time  # Add this import

# Load the model
model_path = os.path.join(settings.BASE_DIR, 'models', 'v1.keras')
model = tf.keras.models.load_model(model_path)

# Constants for text preprocessing
MAX_SEQUENCE_LENGTH = 50  # Adjust this based on your model's requirements
VOCAB_SIZE = 50000  # Adjust this based on your model's requirements

# Load the tokenizer
tokenizer_path = os.path.join(settings.BASE_DIR, 'models', 'tokenizer.json')
with open(tokenizer_path, 'r') as f:
    tokenizer_data = f.read()
tokenizer = tf.keras.preprocessing.text.tokenizer_from_json(tokenizer_data)

def remove_emoji(text):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def clean_text(text):
    delete_dict = {sp_character: '' for sp_character in string.punctuation}
    delete_dict[' '] = ' '
    table = str.maketrans(delete_dict)
    text1 = text.translate(table)
    textArr = text1.split()
    text2 = ' '.join([w for w in textArr if (not w.isdigit() and len(w) > 3)])
    return text2.lower()

def preprocess_text(text):
    """Preprocess text to match the model's expected input format"""
    # Remove emojis and clean text
    text = remove_emoji(text)
    text = clean_text(text)
    
    # Convert to list if single string
    if isinstance(text, str):
        text = [text]
    
    # Tokenize and pad sequences
    sequences = tokenizer.texts_to_sequences(text)
    padded_sequences = pad_sequences(sequences, padding='post', maxlen=MAX_SEQUENCE_LENGTH)
    return np.array(padded_sequences)

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
    if (audio_extension != ".wav"):
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
                messages.warning(request, 'Unsupported audio format')
                return render(request, 'base/home.html')

            # Ensure the temp_audio directory exists
            temp_audio_dir = os.path.join(settings.MEDIA_ROOT, 'temp_audio')
            os.makedirs(temp_audio_dir, exist_ok=True)

            # Save the audio file temporarily
            temp_audio_path = os.path.join(temp_audio_dir, audio.name)
            with open(temp_audio_path, 'wb+') as destination:
                for chunk in audio.chunks():
                    destination.write(chunk)

            # Convert audio to text
            transcribed_text = convert_audio_to_text(temp_audio_path)

        # Combine user text input (if any) with transcribed text
        final_text = text if text else transcribed_text
        print(final_text)

        # Preprocess text and make predictions
        processed_text = preprocess_text(final_text)
        
        # Measure the time taken for prediction
        start_time = time.time()
        prediction = model.predict(processed_text)
        end_time = time.time()
        time_taken = round(end_time - start_time, 2)
        
        print(prediction)
        # Convert prediction to human-readable format
        prediction_label = "Hate Speech" if prediction[0][0] > 0.5 else "Not Hate Speech"
        prediction_probability = round(float(prediction[0][0]) * 100, 2)

        messages.success(request, 'Input received successfully!')
        TextAudio.objects.create(user=user, text=final_text, audio_file=audio)

        return render(request, 'base/results.html', {
            'input_text': final_text, 
            'result': prediction_label,
            'probability': f"{prediction_probability}%",
            'model': 'v1.keras',
            'time_taken': f"{time_taken} seconds"  
        })

    return render(request, 'base/home.html')

