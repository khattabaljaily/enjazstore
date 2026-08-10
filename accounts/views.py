from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import CreateView

from orders.models import Order
from products.models import Wishlist

from .emails import send_email_verification
from .forms import AccountPasswordResetForm, EmailOrUsernameAuthenticationForm, ProfileForm, RegisterForm
from .models import User
from .tokens import email_verification_token
from .twofactor import provisioning_uri, qr_data_uri, random_secret, verify_totp

PENDING_2FA_SESSION_KEY = 'pending_2fa_user_id'
PENDING_2FA_ATTEMPTS_KEY = 'pending_2fa_attempts'
PENDING_TOTP_SECRET_SESSION_KEY = 'pending_totp_secret'
MAX_2FA_ATTEMPTS = 5


class AccountLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = EmailOrUsernameAuthenticationForm
    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        if self.request.user.is_staff:
            return reverse_lazy('dashboard:home')
        return super().get_default_redirect_url()

    def form_valid(self, form):
        user = form.get_user()
        if user.is_staff and user.totp_enabled:
            self.request.session[PENDING_2FA_SESSION_KEY] = user.pk
            return redirect('accounts:two_factor_verify')
        return super().form_valid(form)


def two_factor_verify(request):
    user_id = request.session.get(PENDING_2FA_SESSION_KEY)
    if not user_id:
        return redirect('accounts:login')

    try:
        user = User.objects.get(pk=user_id, is_staff=True, totp_enabled=True)
    except User.DoesNotExist:
        request.session.pop(PENDING_2FA_SESSION_KEY, None)
        return redirect('accounts:login')

    if request.method == 'POST':
        if verify_totp(user.totp_secret, request.POST.get('code', '')):
            request.session.pop(PENDING_2FA_SESSION_KEY, None)
            request.session.pop(PENDING_2FA_ATTEMPTS_KEY, None)
            login(request, user, backend='accounts.backends.EmailOrUsernameBackend')
            return redirect('dashboard:home')

        attempts = request.session.get(PENDING_2FA_ATTEMPTS_KEY, 0) + 1
        if attempts >= MAX_2FA_ATTEMPTS:
            request.session.pop(PENDING_2FA_SESSION_KEY, None)
            request.session.pop(PENDING_2FA_ATTEMPTS_KEY, None)
            messages.error(request, 'محاولات فاشلة كثيرة جدًا. يرجى تسجيل الدخول مرة أخرى.')
            return redirect('accounts:login')
        request.session[PENDING_2FA_ATTEMPTS_KEY] = attempts
        messages.error(request, 'رمز غير صحيح. يرجى المحاولة مرة أخرى.')

    return render(request, 'accounts/two_factor_verify.html', {})


class AccountLogoutView(LogoutView):
    next_page = 'products:list'


def _send_verification_email(request, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    verify_url = request.build_absolute_uri(
        reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': token}),
    )
    send_email_verification(user, verify_url)


class RegisterView(CreateView):
    template_name = 'accounts/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('products:list')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object, backend='accounts.backends.EmailOrUsernameBackend')
        _send_verification_email(self.request, self.object)
        messages.info(self.request, 'أرسلنا رابط تحقق إلى بريدك الإلكتروني.')
        return response


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and email_verification_token.check_token(user, token):
        if not user.is_email_verified:
            user.email_verified_at = timezone.now()
            user.save(update_fields=['email_verified_at'])
        messages.success(request, 'تم التحقق من بريدك الإلكتروني.')
    else:
        messages.error(request, 'رابط التحقق هذا غير صالح أو انتهت صلاحيته.')

    return redirect('accounts:profile' if request.user.is_authenticated else 'accounts:login')


@login_required
def resend_verification(request):
    if request.method == 'POST' and not request.user.is_email_verified:
        _send_verification_email(request, request.user)
        messages.success(request, 'تم إرسال بريد التحقق.')
    return redirect('accounts:profile')


class AccountPasswordChangeView(PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم تحديث كلمة المرور الخاصة بك.')
        return response


class AccountPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    form_class = AccountPasswordResetForm
    success_url = reverse_lazy('accounts:password_reset_done')

    def form_valid(self, form):
        form.save(request=self.request)
        return super(PasswordResetView, self).form_valid(form)


class AccountPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class AccountPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class AccountPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث ملفك الشخصي.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def two_factor_setup(request):
    if not request.user.is_staff:
        raise Http404

    if request.user.totp_enabled:
        return redirect('accounts:profile')

    secret = request.session.get(PENDING_TOTP_SECRET_SESSION_KEY)
    if not secret:
        secret = random_secret()
        request.session[PENDING_TOTP_SECRET_SESSION_KEY] = secret

    if request.method == 'POST':
        if verify_totp(secret, request.POST.get('code', '')):
            request.user.totp_secret = secret
            request.user.totp_enabled = True
            request.user.save(update_fields=['totp_secret', 'totp_enabled'])
            request.session.pop(PENDING_TOTP_SECRET_SESSION_KEY, None)
            messages.success(request, 'تم تفعيل المصادقة الثنائية الآن.')
            return redirect('accounts:profile')
        messages.error(request, 'رمز غير صحيح. يرجى المحاولة مرة أخرى.')

    return render(request, 'accounts/two_factor_setup.html', {
        'qr_data_uri': qr_data_uri(provisioning_uri(request.user, secret)),
        'secret': secret,
    })


@login_required
def two_factor_disable(request):
    if request.method == 'POST' and request.user.totp_enabled:
        if verify_totp(request.user.totp_secret, request.POST.get('code', '')):
            request.user.totp_secret = ''
            request.user.totp_enabled = False
            request.user.save(update_fields=['totp_secret', 'totp_enabled'])
            messages.success(request, 'تم تعطيل المصادقة الثنائية.')
        else:
            messages.error(request, 'رمز غير صحيح.')
    return redirect('accounts:profile')


@login_required
def my_wishlist(request):
    items = list(
        Wishlist.objects.filter(user=request.user).select_related('product').prefetch_related(
            'product__images', 'product__variants',
        ),
    )
    return render(request, 'accounts/wishlist.html', {
        'wishlist_items': items,
        'wishlist_product_ids': {item.product_id for item in items},
    })


@login_required
def my_orders(request):
    orders = list(
        Order.objects.filter(user=request.user)
        .prefetch_related('return_requests')
        .order_by('-created_at')
    )
    for order in orders:
        order.open_return = next(
            (r for r in order.return_requests.all() if r.status in ('pending', 'approved')), None,
        )
    return render(request, 'accounts/orders.html', {'orders': orders})
