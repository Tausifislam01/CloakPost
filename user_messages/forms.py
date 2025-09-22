from django import forms
from django.contrib.auth import get_user_model
from .models import Message

class MessageForm(forms.ModelForm):
    """
    Recipient list is limited to the current user's friends.
    Pass the current user via `user=` kwarg.
    Includes a password field to unlock the sender's private key for signing.
    """
    recipient = forms.ModelChoiceField(queryset=get_user_model().objects.none())
    content = forms.CharField(widget=forms.Textarea, label="Message")
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
        label="Password (to sign your message)",
        strip=False,
        help_text="Used to unlock your private key; never stored."
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user is not None and user.is_authenticated:
            self.fields["recipient"].queryset = user.friends.all()
        else:
            self.fields["recipient"].queryset = get_user_model().objects.none()

    class Meta:
        model = Message
        fields = ['recipient', 'content', 'password']


class MessageUnlockForm(forms.Form):
    """
    Require the user to re-enter their account password to unlock messages.
    The password is used to derive the AES key transiently (not stored).
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
        label="Password to unlock inbox",
        strip=False,
    )