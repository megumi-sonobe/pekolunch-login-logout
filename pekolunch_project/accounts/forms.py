from django import forms
from accounts.models import Users
from django.contrib.auth.password_validation import validate_password,ValidationError


class RegistForm(forms.ModelForm):
    username = forms.CharField(label='名前/ニックネーム：',min_length=8,max_length=32)
    email = forms.EmailField(label='メールアドレス')
    password = forms.CharField(label='パスワード',widget=forms.PasswordInput())
    confirm_password = forms.CharField(label='パスワード再入力',widget=forms.PasswordInput())
    
    class Meta:
        model = Users
        fields = ['username','email','password']
    
    def clean(self):
        cleaned_data = super().clean()
        # print(cleaned_data)
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
        
        
            # for message in e.messages:
            #     self.add_error('password',message)
        
    def save(self,commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
    
class UserLoginForm(forms.Form):
    email = forms.EmailField(label='メールアドレス')
    password = forms.CharField(label='パスワード',widget=forms.PasswordInput())
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        
        if len(password) < 8 or len(password) > 32 or not password.isalnum():
            raise forms.ValidationError('半角英数字を含み、8文字以上32文字以内で入力してください')
        
        return password