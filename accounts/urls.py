from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('a-propos/', views.about, name='a_propos'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    # Phone verification
    path('phone/send/', views.send_phone_otp, name='phone_send'),
    path('phone/verify/', views.verify_phone_otp, name='phone_verify'),
]
