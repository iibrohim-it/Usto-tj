from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class ProfileForm(forms.ModelForm):

    class Meta:
        model = UstoProfile
        fields = ['phone', 'city', 'experience', 'description', 'avatar']


class CategoryForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = ['name', 'is_active']


class AdvertisementForm(forms.ModelForm):
    class MultipleFileInput(forms.ClearableFileInput):
        allow_multiple_selected = True

    images = forms.FileField(
        required=True,
        widget=MultipleFileInput(attrs={'multiple': True})
    )   

    video = forms.FileField(required=False)

    class Meta:
        model = Advertisement
        fields = ['category', 'title', 'description', 'price', 'city']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)

    def clean_images(self):
        images = self.files.getlist('images')

        if not 1 <= len(images) <= 10:
            raise forms.ValidationError('Нужно загрузить от 1 до 10 фотографий.')
        return images


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']