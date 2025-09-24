from django import forms
from users.models import CustomUser

class MessageForm(forms.Form):
    recipient = forms.ModelChoiceField(queryset=CustomUser.objects.none())
    content = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        # Only friends can be recipients
        self.fields["recipient"].queryset = user.friends.all()