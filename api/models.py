from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.contrib.gis.db import models as gis_models


class CustomUserManager(UserManager):
    def get_by_natural_key(self, email):
        return self.get(email__iexact=email)


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()  # Use the custom manager

    def __str__(self):
        return self.email.lower()  # Store and return email in lowercase

    def save(self, *args, **kwargs):
        self.email = self.email.lower()  # Ensure email is always stored in lowercase
        super().save(*args, **kwargs)


class AdoptedArea(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="adopted_areas"
    )
    area_name = models.CharField(max_length=100)
    adoptee_name = models.CharField(max_length=100)
    email = models.EmailField()
    adoption_type = models.CharField(
        max_length=20,
        choices=[("indefinite", "Indefinite"), ("temporary", "Temporary")],
        default="indefinite"
    )
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    note = models.TextField(blank=True)
    location = gis_models.PointField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.area_name} in {self.city}, {self.state}"


class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    headquarters = gis_models.PointField()
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    leaders = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="led_teams", blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="teams", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def add_leader(self, user):
        if self.leaders.count() >= 5:
            raise ValueError("Maximum of 5 leaders allowed.")
        self.leaders.add(user)

    def __str__(self):
        return self.name
