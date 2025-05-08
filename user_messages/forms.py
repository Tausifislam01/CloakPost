from django import forms
from .models import Message
from django.contrib.auth import get_user_model

class MessageForm(forms.ModelForm):
    recipient = forms.ModelChoiceField(queryset=get_user_model().objects.all())
    content = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Message
        fields = ['recipient', 'content']