from django.db import models
from django.contrib.auth.models import User

class TextAudio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    audio_file = models.FileField(upload_to='audio_files/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return self.text if self.text else self.audio_file.name