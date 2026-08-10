from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STAFF = 'staff', 'موظف'
        MANAGER = 'manager', 'مدير'

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=32, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)

    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_seen_ip = models.GenericIPAddressField(null=True, blank=True)
    last_seen_location = models.CharField(max_length=150, blank=True)

    email_verified_at = models.DateTimeField(null=True, blank=True)

    totp_secret = models.CharField(max_length=32, blank=True)
    totp_enabled = models.BooleanField(default=False)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_manager(self):
        return self.is_superuser or self.role == self.Role.MANAGER

    @property
    def is_email_verified(self):
        return self.email_verified_at is not None
