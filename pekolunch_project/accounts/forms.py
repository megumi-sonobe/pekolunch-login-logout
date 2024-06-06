from typing import Any
from django import forms
from accounts.models import Users
from django.contrib.auth.password_validation import validate_password,ValidationError
from django.contrib.auth.forms import PasswordChangeForm
from choices import COOKING_TIME_CHOICES


class RegistForm(forms.ModelForm):
    username = forms.CharField(label='名前/ニックネーム：',max_length=32)
    email = forms.EmailField(label='メールアドレス')
    password = forms.CharField(label='パスワード',widget=forms.PasswordInput())
    confirm_password = forms.CharField(label='パスワード再入力',widget=forms.PasswordInput())
    
    class Meta:
        model = Users
        fields = ['username','email','password']
        
    def clean_email(self):
        email = self.cleaned_data['email']
        if Users.objects.filter(email=email).exists():
            raise forms.ValidationError('このメールアドレスは既に使用されています。')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password != confirm_password:
            self.add_error('confirm_password','パスワードが一致しません。')
            return
        
        try:
            validate_password(password)
        except ValidationError as e:
            self.add_error('password',e.messages[0])
            
        
        if not (8 <= len(password) <= 32 and any(c.isalpha() for c in password) and any(c.isdigit() for c in password)) :
            self.add_error('password','パスワードは半角英文字と数字を含んでください。')
        
        
        
    def save(self,commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save(using=self._db)
        return user
    
class UserLoginForm(forms.Form):
    email = forms.EmailField(label='メールアドレス')
    password = forms.CharField(label='パスワード',widget=forms.PasswordInput())
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        if len(password) < 8 or len(password) > 32 or not password.isalnum():
            raise forms.ValidationError('半角英数字を含み、8文字以上32文字以内で入力してください')
        
        return password
    
    
class UserUpdateForm(forms.ModelForm):
    username = forms.CharField(label='名前/ニックネーム：',max_length=32)
    email = forms.EmailField(label='メールアドレス')
    current_password = forms.CharField(label='現在のパスワード',widget=forms.PasswordInput(),required=False)
    new_password = forms.CharField(label='新しいパスワード',widget=forms.PasswordInput(),required=False)
    confirm_password = forms.CharField(label='新しいパスワード再入力',widget=forms.PasswordInput(),required=False)
    

    class Meta:
        model = Users
        fields = ['username','email']
        
        
    def clean_email(self):
        email = self.cleaned_data['email']
        if Users.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError('このメールアドレスは既に使用されています')
        return email
    
    
    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if current_password:
            user = self.instance
            if not user.check_password(current_password):
                self.add_error('current_password','現在のパスワードが間違っています')
        
        if new_password or confirm_password:
            if new_password != confirm_password:
                self.add_error('confirm_password','新しいパスワードが一致しません')
                
                
            else:
                try:
                    validate_password(new_password)
                except ValidationError as e:
                    self.add_error('new_password',e.messages[0])
            
            if not (8 <= len(new_password) <= 32 and any(c.isalpha() for c in new_password) and any(c.isdigit() for c in new_password)) :
                self.add_error('new_password','パスワードは半角英文字と数字を含んでください。')
                    
        

        return cleaned_data
                    
    
    def save(self,commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        
        if new_password:
            user.set_password(new_password)
            
            
        if commit:
            user.save()
            
        return user
    

class MyPageForm(forms.ModelForm):
    image_url = forms.ImageField(label='画像',required=False)
    adult_count = forms.IntegerField(label='大人')
    children_count = forms.IntegerField(label='子ども')
    cooking_time_min = forms.ChoiceField(label='一品あたりの調理時間',choices=COOKING_TIME_CHOICES) 
    
    class Meta:
        model = Users
        fields = ['image_url','adult_count','children_count','cooking_time_min']
        
