from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('', views.home, name='home'),
    path('classification/',views.classification,name='classification'),
    path('document-Q-and-A/',views.doc_qna,name='doc_qna'),
    path('update_knowledge/',views.update_knowledge,name='update_knowledge'),
    path('summary/',views.summary,name='summary'),
    path('download_excel/', views.download_excel, name='download_excel'),
]