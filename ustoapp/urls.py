from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<uidb64>/<token>/', ActivateView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    # profile==========================
    path('create/profile/', ProfileCreateView.as_view(), name='create_profile'),
    path('profile/detail/', ProfileDetailView.as_view(), name='profile_detail'),
    path('update/profile/<int:pk>/', ProfileUpdateView.as_view(), name='update_profile'),
    path('delete/profile/<int:pk>/', ProfileDeleteView.as_view(), name='delete_profile'),
    # category=======================
    path('create/category/', CategoryCreateView.as_view(), name='create_category'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('update/category/<int:pk>/', CategoryUpdateView.as_view(), name='update_category'),
    path('delete/category/<int:pk>/', CategoryDeleteView.as_view(), name='delete_category'),
    # advertisement=============
    path('create/advertisement/', AdvertisementCreateView.as_view(), name='create_advertisement'),
    path('advertisements/', AdvertisementListView.as_view(), name='advertisement_list'),
    path('advertisement/<int:pk>/', AdvertisementDetailView.as_view(), name='advertisement_detail'),
    path('my/advertisements/', MyAdvertisementListView.as_view(), name='my_advertisements'),
    path('update/advertisement/<int:pk>/', AdvertisementUpdateView.as_view(), name='update_advertisement'),
    path('delete/advertisement/<int:pk>/', AdvertisementDeleteView.as_view(), name='delete_advertisement'),
    # review==============
    path('create/review/<int:pk>/', ReviewCreateView.as_view(), name='create_review'),
    path('my/reviews/', MyReviewListView.as_view(), name='my_reviews'),
    path('update/review/<int:pk>/', ReviewUpdateView.as_view(), name='update_review'),
    path('delete/review/<int:pk/', ReviewDeleteView.as_view(), name='delete_review'),
    
    


]   