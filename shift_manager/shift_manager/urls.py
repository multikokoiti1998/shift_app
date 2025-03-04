"""
URL configuration for shift_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from shift_app import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('assign/', views.assign_teams, name='assign_teams'),
    path('schedule/', views.create_shift_schedule, name='create_shift_schedule'),
    path("add_tech/", views.add_tech, name="add_tech"),
    path("delete_tech/<str:tech_name>/", views.delete_tech, name="delete_tech"),
    path("assign_ab_team/", views.assign_ab_team, name="assign_ab_team"),
    path('generate_attendance_report/', views.generate_attendance_report, name='generate_attendance_report'),
]

