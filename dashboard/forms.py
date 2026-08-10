from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from ads.models import Banner
from coupons.models import Coupon
from orders.models import Order, ReturnRequest
from products.models import Category, Product, ProductImage, Review, Variant

from .models import SiteSettings

User = get_user_model()


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'category', 'description', 'price', 'condition', 'warranty_days', 'is_active', 'is_featured')
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}

    def clean_name(self):
        name = self.cleaned_data['name']
        qs = Product.objects.filter(slug=slugify(name))
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('يوجد منتج بهذا الاسم مسبقًا.')
        return name


class BaseProductImageFormSet(forms.BaseInlineFormSet):
    """Only one image can be primary — if more than one is checked
    (e.g. JS was bypassed), keep the first and unset the rest."""

    def clean(self):
        super().clean()
        primary_forms = [
            form for form in self.forms
            if getattr(form, 'cleaned_data', None)
            and not form.cleaned_data.get('DELETE')
            and form.cleaned_data.get('is_primary')
        ]
        for form in primary_forms[1:]:
            form.cleaned_data['is_primary'] = False
            form.instance.is_primary = False


ProductImageFormSet = forms.inlineformset_factory(
    Product, ProductImage,
    fields=('image', 'alt_text', 'is_primary'),
    formset=BaseProductImageFormSet,
    extra=0, can_delete=True,
)

VariantFormSet = forms.inlineformset_factory(
    Product, Variant,
    fields=('size', 'color', 'sku', 'stock', 'price_override'),
    extra=1, can_delete=True,
)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name', 'description', 'icon')
        widgets = {
            'icon': forms.TextInput(attrs={'placeholder': 'مثال: shopping-bag'}),
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        qs = Category.objects.filter(slug=slugify(name))
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('يوجد قسم بهذا الاسم مسبقًا.')
        return name


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('status', 'tracking_carrier', 'tracking_number')
        widgets = {
            'tracking_carrier': forms.TextInput(attrs={'placeholder': 'مثال: أرامكس، بريد السودان'}),
            'tracking_number': forms.TextInput(attrs={'placeholder': 'رقم التتبع'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self._previous_status = self.instance.status
        if not (user and user.is_superuser):
            self.fields['status'].choices = [
                choice for choice in self.fields['status'].choices
                if choice[0] != Order.Status.CANCELLED
            ]

    def clean_status(self):
        status = self.cleaned_data['status']
        if status == Order.Status.CANCELLED and not (self.user and self.user.is_superuser):
            raise forms.ValidationError('يمكن للمشرف العام فقط إلغاء الطلب.')
        return status

    def save(self, commit=True):
        order = super().save(commit=False)

        if order.status == Order.Status.DELIVERED and not order.delivered_at:
            order.delivered_at = timezone.now()

        if commit:
            with transaction.atomic():
                if order.status == Order.Status.CANCELLED and self._previous_status != Order.Status.CANCELLED:
                    for item in order.items.select_related('variant'):
                        variant = Variant.objects.select_for_update().get(pk=item.variant_id)
                        variant.stock += item.quantity
                        variant.save(update_fields=['stock'])
                order.save()
        return order


class EmployeeCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True
        if commit:
            user.save()
        return user


class EmployeeUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = (
            'maintenance_mode', 'coming_soon_message', 'ads_enabled',
            'bank_name', 'bank_account_name', 'bank_account_number', 'bank_transfer_note',
            'delivery_estimate',
        )
        widgets = {
            'coming_soon_message': forms.Textarea(attrs={'rows': 4}),
            'bank_transfer_note': forms.Textarea(attrs={'rows': 2}),
        }


class BannerForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = ('name', 'placement', 'image', 'target_url', 'alt_text', 'order', 'is_active')


class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = (
            'code', 'amount', 'is_active', 'valid_from', 'valid_until',
            'minimum_order_amount', 'max_redemptions', 'max_redemptions_per_customer',
        )
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'valid_until': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class MarketingEmailForm(forms.Form):
    subject = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'placeholder': 'مثال: خصم 20% على كل شيء هذا الأسبوع'}))
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 10,
        'placeholder': 'اكتب رسالتك… افصل بين الفقرات بسطر فارغ.',
    }))


class ReturnRequestStatusForm(forms.ModelForm):
    class Meta:
        model = ReturnRequest
        fields = ('status', 'staff_notes')
        widgets = {'staff_notes': forms.Textarea(attrs={'rows': 3})}


class ReviewModerationForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('status', 'staff_notes')
        widgets = {'staff_notes': forms.Textarea(attrs={'rows': 3})}


class DashboardReturnRequestForm(forms.ModelForm):
    """Lets staff log a return on a customer's behalf (phone/email requests,
    or guest-checkout orders that have no account to self-serve from).
    Unlike the customer-facing form, this skips the eligibility-window
    check — staff are trusted to use judgment."""

    class Meta:
        model = ReturnRequest
        fields = ('reason', 'resolution_requested', 'description', 'status', 'staff_notes')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'staff_notes': forms.Textarea(attrs={'rows': 3}),
        }
