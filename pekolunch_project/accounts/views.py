from django.shortcuts import render,redirect
from django.views.generic.edit import CreateView,FormView
from django.views.generic.base import TemplateView,View
from .forms import RegistForm,UserLoginForm
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin


class HomeView(LoginRequiredMixin,TemplateView):
    template_name = 'home.html'
    
class RegistUserView(CreateView):
    template_name = 'regist.html'
    form_class = RegistForm
    success_url = '/accounts/user_login/'
    
class UserLoginView(FormView):
    template_name = 'user_login.html'
    form_class = UserLoginForm
    
    def post(self,request,*args,**kwargs):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(email=email,password=password)
            
            if user is not None and user.is_active:
                login(request,user)
                return redirect('accounts:home')
            else:
                messages.warning(request,'メールアドレスかパスワードが間違っています')
        else:
            messages.warning(request,'入力された情報に問題があります。正しいメールアドレスとパスワードを入力してください。')
                
        return render(
            request,self.template_name,{'form':form})
            


class UserLogoutView(View):
    def get(self,request,*args,**kwargs):
        logout(request)
        messages.success(request,'ログアウトしました')
        return redirect('accounts:user_login')
    
