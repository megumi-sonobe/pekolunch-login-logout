from django.urls import path
from.views import(
    RegistUserView,HomeView,UserLoginView,UserLogoutView,
    UserUpdateView,MyPageView
)
from meal_planner.views import create_meal_plans
from django.conf import settings
from django.conf.urls.static import static

app_name = 'accounts'
urlpatterns = [
    path('home/',HomeView.as_view(),name='home'),
    path('regist/',RegistUserView.as_view(),name='regist'),
    path('user_login/',UserLoginView.as_view(),name='user_login'),
    path('user_logout/',UserLogoutView.as_view(),name='user_logout'),
    path('user_update/',UserUpdateView.as_view(),name='user_update'),
    path('my_page/',MyPageView.as_view(),name='my_page'),
    path('create_meal_plans/',create_meal_plans,name='create_meal_plans'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
