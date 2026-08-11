from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, UserCreationForm
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.text import slugify

from .emails import send_password_reset
from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label='البريد الإلكتروني')
    privacy_consent = forms.BooleanField(
        required=True,
        label='أوافق على سياسة الخصوصية وأوافق على تخزين بياناتي واستخدامها على النحو الموضّح فيها.',
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self._generate_username(user.email)
        if commit:
            user.save()
        return user

    @staticmethod
    def _generate_username(email):
        base = slugify(email.split('@')[0])[:25] or 'user'
        username = base
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f'{base}{suffix}'
        return username


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'phone', 'address', 'city')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'اسم المستخدم أو البريد الإلكتروني'
        self.fields['username'].widget.attrs['placeholder'] = 'اسم المستخدم أو البريد الإلكتروني'


class AccountPasswordResetForm(PasswordResetForm):
    def save(self, request, **kwargs):
        for user in self.get_users(self.cleaned_data['email']):
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = request.build_absolute_uri(
                reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token}),
            )
            send_password_reset(user, reset_url)
