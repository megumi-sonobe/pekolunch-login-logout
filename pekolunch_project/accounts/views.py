from django.db.models.base import Model as Model
from django.db.models.query import QuerySet
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.views.generic.edit import CreateView,FormView,UpdateView
from django.views.generic.base import TemplateView,View
from .forms import RegistForm,UserLoginForm,UserUpdateForm,MyPageForm
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib.messages import get_messages
from recipes.models import Recipe

class AccountsHomeView(LoginRequiredMixin,TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs): 
        print("AccountsHomeView accessed") 
        context = super().get_context_data(**kwargs)
        context['username'] = self.request.user.username
        context['my_page_url'] = reverse_lazy('accounts:my_page')
        context['messages'] = list(get_messages(self.request))
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
        messages.success(self.request,'アカウントを登録しました。ログインしてください。')
        
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        self.request.session['django.contrib.messeges.error'] = []
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
        
        messages.success(self.request,'アカウント情報を更新しました。もう一度ログインしてください。')
        return redirect('accounts:home')
    
    
    
class MyPageView(LoginRequiredMixin, UpdateView):
    template_name = 'accounts/my_page.html'
    form_class = MyPageForm
    success_url = reverse_lazy('accounts:home')
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        user = form.save(commit=False)
        image_url = self.request.FILES.get('image_url')  # ファイルを取得する
        
        # デバッグメッセージを追加
        print("image_url-clear in POST:", 'image_url-clear' in self.request.POST)

        
        if 'image_url-clear' in self.request.POST:
            user.image_url = None  # 画像をクリアする
        elif image_url:
            user.image_url = image_url
            
        user.save()
        
        self.request.session['adult_count'] = form.cleaned_data['adult_count']
        self.request.session['children_count'] = form.cleaned_data['children_count']

        messages.success(self.request, 'マイページを更新しました。')
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        three_star_recipes = Recipe.objects.filter(user_evaluations__user=user, user_evaluations__evaluation=3)
        context['three_star_recipes'] = three_star_recipes
        return context

    