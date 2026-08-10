from datetime import timedelta

from django import forms
from django.utils import timezone

from .models import Order, ReturnRequest


class CheckoutForm(forms.ModelForm):
    receipt_image = forms.ImageField(label='صورة إيصال التحويل البنكي')

    class Meta:
        model = Order
        fields = ('full_name', 'email', 'phone', 'address', 'city')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }


class ReturnRequestForm(forms.ModelForm):
    class Meta:
        model = ReturnRequest
        fields = ('reason', 'resolution_requested', 'description')
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'أضف أي تفاصيل تساعدنا على معالجة الطلب بسرعة.',
            }),
        }

    def __init__(self, *args, order=None, **kwargs):
        self.order = order
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        reason = cleaned_data.get('reason')
        resolution = cleaned_data.get('resolution_requested')

        if self.order is not None and reason and resolution:
            if not self.order.delivered_at:
                raise forms.ValidationError(
                    'لم يتم تسليم هذا الطلب بعد، لذا لا يمكن طلب إرجاعه.'
                )

            elapsed = timezone.now() - self.order.delivered_at
            if reason in (ReturnRequest.Reason.DAMAGED, ReturnRequest.Reason.DEFECTIVE):
                window, window_label = timedelta(hours=24), '24 ساعة'
            elif resolution == ReturnRequest.Resolution.REFUND:
                window, window_label = timedelta(days=3), '3 أيام'
            else:
                window, window_label = timedelta(days=7), '7 أيام'

            if elapsed > window:
                raise forms.ValidationError(
                    f'انتهت مهلة طلب هذا الإجراء ({window_label} بعد التسليم). '
                    'يرجى التواصل مع الدعم مباشرة للمساعدة.'
                )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.order = self.order
        if commit:
            instance.save()
        return instance
