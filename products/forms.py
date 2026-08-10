from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('rating', 'title', 'body')
        widgets = {
            'rating': forms.RadioSelect(),
            'title': forms.TextInput(attrs={'placeholder': 'لخّص تجربتك (اختياري)'}),
            'body': forms.Textarea(attrs={'rows': 4, 'placeholder': 'ما الذي أعجبك أو لم يعجبك؟'}),
        }
