from django.shortcuts import render,redirect
from django.views.generic.edit import CreateView,FormView,UpdateView
from django.views.generic.base import TemplateView,View
from .forms import RegistForm,UserLoginForm,UserUpdateForm
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

class HomeView(LoginRequiredMixin,TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs): 
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['my_page_url'] = reverse_lazy('accounts:my_page')
        return context
    
        
class RegistUserView(CreateView):
    template_name = 'accounts/regist.html'
    form_class = RegistForm
    success_url = '/accounts/user_login/'
    
    def form_valid(self,form):
        user = form.save(commit=False)
        password = form.cleaned_data.get('password')
        user.set_password(password)
        user.save()
        print("ユーザーが保存されました",user)
        
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        print("フォームのデータが無効:", form.errors)
        messages.error(self.request, "入力された情報に問題があります。正しい情報を入力してください。")
        return super().form_invalid(form)
    
class UserLoginView(FormView):
    template_name = 'accounts/user_login.html'
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
    
class UserUpdateView(LoginRequiredMixin,UpdateView):
    template_name = 'accounts/user_update.html'
    form_class = UserUpdateForm
    success_url = reverse_lazy('accounts:home')
   
    
    def get_object(self,queryset=None):
        return self.request.user
    
    
    def form_valid(self,form):
        # user = self.request.user
        # form.save()
        
        new_password = form.cleaned_data.get('new_password')
        if new_password:
            self.request.user.set_password(new_password)
            self.request.user.save()
        
        return super().form_valid(form)
    
    
    
class MyPageView(LoginRequiredMixin,TemplateView):
    template_name = 'accounts/my_page.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['user_update_url'] = reverse_lazy('accounts:user_update')
        return context