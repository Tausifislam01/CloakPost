from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea)
    visibility = forms.ChoiceField(choices=[('global', 'Global'), ('friends', 'Friends Only')], widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Post
        fields = ['title', 'content', 'visibility']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        }