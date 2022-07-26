from django.conf import settings
from django.db import models
from django.contrib.auth.models import (BaseUserManager,PermissionsMixin,AbstractBaseUser)

class UserManager(BaseUserManager): #manager to be used by the user model

    def create_user(self,email,password=None,**extra_fields):
        if not email:
            raise ValueError('Email is required')
        user = self.model(email=self.normalize_email(email),**extra_fields) #associating with the user model provided below
        user.set_password(password)
        user.save(using=self._db)

        return user
    
    def create_superuser(self,email,password,**extra_fields):
        user = self.create_user(email,password)
        user.is_superuser = True
        user.is_staff =True
        user.save(using=self._db)

        return user

class Custom_User(AbstractBaseUser,PermissionsMixin):
    email = models.EmailField(max_length=250,unique=True)
    name = models.CharField(max_length=250)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = UserManager()
    USERNAME_FIELD ='email'

class Recipe(models.Model):
    user  = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,)
    title =models.CharField(max_length=250)
    description = models.TextField(blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5,decimal_places=2)
    link = models.CharField(max_length=250 ,blank=True)
    tags = models.ManyToManyField('Tag')
    ingredients =models.ManyToManyField('Ingredient')

    def __str__(self):
        return self.title
        
class Tag(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,)
    name = models.CharField(max_length=300)
    
    def __str__(self):
        return self.name

class Ingredient(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,)
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name