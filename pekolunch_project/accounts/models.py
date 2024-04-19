from django.db import models
from django.contrib.auth.models import(
    BaseUserManager,AbstractBaseUser,PermissionsMixin
)
from django.urls import reverse_lazy
from django.utils import timezone
from choices import COOKING_TIME_CHOICES


class UserManager(BaseUserManager):
    def create_user(self,username,email,password=None):
        if not email:
            raise ValueError('Enter Email')
        if not password:
            raise ValueError('Enter Password')
        user = self.model(
            username=username,
            email=email
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self,username,email,password=None):
        user = self.create_user(
            username = username,
            email=email,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
    
    
class Users(AbstractBaseUser,PermissionsMixin):
    username = models.CharField(max_length=32)
    email = models.EmailField(max_length=64,unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    image_url = models.ImageField(upload_to='images/',null=True,blank=True)
    adult_count = models.IntegerField(default=2)
    children_count = models.IntegerField(default=0)
    
    cooking_time_min = models.IntegerField(choices=COOKING_TIME_CHOICES,null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    objects = UserManager()
    
    def get_absolute_url(self):
        return reverse_lazy('accounts:home')
    
    def save(self,*args,**kwargs):
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super(Users,self).save(*args,**kwargs)