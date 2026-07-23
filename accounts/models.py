import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model using email as the login identifier.
    `username` is retained (unused for login) purely because several
    Django admin/auth internals expect it; it is auto-populated from
    the email address.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("email address", unique=True)
    job_title = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=32, blank=True)
    is_platform_admin_contact = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["first_name", "last_name"]

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        full_name = self.get_full_name()
        return f"{full_name} <{self.email}>" if full_name else self.email

    @property
    def display_name(self):
        return self.get_full_name() or self.email

    @property
    def initials(self):
        first = self.first_name[:1] if self.first_name else ""
        last = self.last_name[:1] if self.last_name else ""
        initials = (first + last).upper()
        return initials or self.email[:2].upper()
