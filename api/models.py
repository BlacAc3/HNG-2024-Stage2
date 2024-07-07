from typing import Any
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

#Custom user manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user



#User Autentication Model
class CustomUser(AbstractBaseUser):
    userId = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firstName = models.CharField(max_length=30, blank=False)
    lastName = models.CharField(max_length=30, blank=False)
    email = models.EmailField(unique=True, blank=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    objects = CustomUserManager()

    USERNAME_FIELD = 'userId'
    REQUIRED_FIELDS = []

    #Setup initialization for default organisation creation during user registration
    # def save(self, *args, **kwargs):
    #     if not self.pk:  # Check if instance is being created
    #         # Perform initialization actions here
    #         org = Organisation.objects.create(name = f"{self.firstName}'s Organisation")
    #         org.save()
    #         self.organisationByUser = org
    #     super().save(*args, **kwargs)

    def __str__(self):
        return self.email
    

#Organisation Models
class Organisation(models.Model):
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="my_organisations")
    orgId = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    members= models.ManyToManyField(CustomUser, related_name="organisation_following")
