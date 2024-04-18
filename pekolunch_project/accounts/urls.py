from django.urls import path
from.views import(
    RegistUserView,HomeView,UserLoginView,UserLogoutView,
    UserUpdateView,MyPageView
)

app_name = 'accounts'
urlpatterns = [
    path('home/',HomeView.as_view(),name='home'),
    path('regist/',RegistUserView.as_view(),name='regist'),
    path('user_login/',UserLoginView.as_view(),name='user_login'),
    path('user_logout/',UserLogoutView.as_view(),name='user_logout'),
    path('user_update/',UserUpdateView.as_view(),name='user_update'),
    path('my_page/',MyPageView.as_view(),name='my_page'),
]