from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from .models import *
from .forms import *
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView, View
from django.urls import reverse, reverse_lazy

from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.views import LoginView, LogoutView

from django.db.models import Avg, Count, Q, Case, When, IntegerField, Value
from django.utils import timezone
from datetime import timedelta
from django.db import transaction



class RegisterView(CreateView):
    model = User
    form_class = RegisterForm
    template_name = 'register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        activation_link = self.request.build_absolute_uri(
            reverse(
                'activate',
                kwargs={
                    'uidb64': uid,
                    'token': token
                }
            )
        )
        send_mail(
            subject='Activate your account',
            message=(
                f'Hello {user.username}\n\n'
                f'Click here {activation_link} to activate your account!'
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False
        )

        return render(self.request, 'email_sent.html', {'email': user.email})


class ActivateView(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save(update_fields=['is_active'])
            return redirect('login')
        return HttpResponse('<h1>Token is not valid!</h1>')


class LoginView(LoginView):
    template_name = 'login.html'
    next_page = reverse_lazy('category_list')


class LogoutView(LoginRequiredMixin, LogoutView):
    next_page = reverse_lazy('login')


class ProfileCreateView(LoginRequiredMixin, CreateView):
    model = UstoProfile
    form_class = ProfileForm
    template_name = 'create_profile.html'
    success_url = reverse_lazy('home')

    # def dispatch(self, request, *args, **kwargs):
    #     if hasattr(request.user, 'usto_profile'):
    #         return redirect('home')
    #     return super().dispatch(request, *args, **kwargs)

    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ProfileDetailView(DetailView):
    model = UstoProfile
    template_name = 'profile_detail.html'
    context_object_name = 'usto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['advertisements'] = self.object.advertisements.filter(
            status='active'
        )
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UstoProfile
    form_class = ProfileForm
    template_name = 'update_usto.html'
    success_url = reverse_lazy('profile_detail')

    def get_queryset(self):
        return UstoProfile.objects.filter(user=self.request.user)


class ProfileDeleteView(LoginRequiredMixin, DeleteView):
    model = UstoProfile
    success_url = reverse_lazy('home')

    def get_queryset(self):
        return UstoProfile.objects.filter(user=self.request.user)


class CategoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'create_category.html'
    success_url = reverse_lazy('category_list')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff


class CategoryListView(ListView):
    model = Category
    template_name = 'category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.all().order_by('-created_at')


class CategoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'update_category.html'
    success_url = reverse_lazy('category_list')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff


class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('category_list')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff


class AdvertisementCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Advertisement
    form_class = AdvertisementForm
    template_name = 'create_advertisement.html'
    success_url = reverse_lazy('my_advertisements')

    def test_func(self):
        return hasattr(self.request.user, 'usto_profile')

    def handle_no_permission(self):
        return redirect('create_profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['promotion_prices'] = AdvertisementPromotion.PRICES
        context['duration_choices'] = AdvertisementPromotion.DURATION_CHOICES
        return context

    def form_valid(self, form):
        images = self.request.FILES.getlist('images')
        video = self.request.FILES.get('video')

        if not 1 <= len(images) <= 10:
            form.add_error('images', 'От 1 до 10 фотографий.')
            return self.form_invalid(form)

        with transaction.atomic():
            form.instance.usto = self.request.user.usto_profile
            form.instance.expires_at = timezone.now() + timedelta(days=14)

            response = super().form_valid(form)

            for image in images:
                AdvertisementImage.objects.create(
                    advertisement=self.object, 
                    image=image)

            if video:
                AdvertisementVideo.objects.create(
                    advertisement=self.object,
                    video=video)
        return response
 

class AdvertisementListView(ListView):
    model = Advertisement
    template_name = 'advertisement_list.html'
    context_object_name = 'advertisements'

    def get_queryset(self):
        now = timezone.now()

        return (Advertisement.objects.filter(status='active').annotate(
            views_count=Count('views', distinct=True),
            rating=Avg('reviews__rating')).annotate(promotion_priority=Case(
                When(
                    promotions__status='active',
                    promotions__promotion_type='top',
                    promotions__start_date__lte=now,
                    promotions__end_date__gte=now,
                    then=2
                ),
                When(
                    promotions__status='active',
                    promotions__promotion_type='premium',
                    promotions__start_date__lte=now,
                    promotions__end_date__gte=now,
                    then=1
                ),
                default=0,
                output_field=IntegerField()
            )).prefetch_related('images', 'promotions').order_by(
                '-promotion_priority', '-created_at').distinct())


class AdvertisementDetailView(DetailView):
    model = Advertisement
    template_name = 'advertisement_detail.html'
    context_object_name = 'advertisement'

    def get_queryset(self):
        return Advertisement.objects.filter(
            status='active',).select_related('usto', 'usto__user', 'category'
                    ).prefetch_related('images', 'video', 'reviews__user', 'promotions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        advertisement = self.object
        now = timezone.now()

        context['views_count'] = advertisement.views_count()
        context['active_promotion'] = advertisement.promotions.filter(
            status='active', start_date__lte=now, end_date__gte=now
        ).order_by('-end_date').first()

        if self.request.user.is_authenticated:
            context['is_favorite'] = Favorite.objects.filter(
                user=self.request.user, advertisement=advertisement).exists()
        else:
            context['is_favorite'] = False

        return context


class MyAdvertisementListView(LoginRequiredMixin, ListView):
    model = Advertisement
    template_name = 'my_advertisements.html'
    context_object_name = 'advertisements'

    def get_queryset(self):
        return Advertisement.objects.filter(usto=self.request.user.usto_profile
        ).annotate(views_count=Count('views', distinct=True),
            rating=Avg('reviews__rating'),
            promotion_order=Case(
                When(
                    promotions__promotion_type='top',
                    promotions__status='active',
                    then=2
                ),
                When(
                    promotions__promotion_type='premium',
                    promotions__status='active',
                    then=1
                ),
                default=0,
                output_field=IntegerField())
            ).prefetch_related('images', 'video', 'promotions').order_by(
                'promotion_order', '-created_at').distinct()


class AdvertisementUpdateView(LoginRequiredMixin, UpdateView):
    model = Advertisement
    form_class = AdvertisementForm
    template_name = 'update_advertisement.html'

    def get_queryset(self):
        return Advertisement.objects.filter(
            usto=self.request.user.usto_profile).prefetch_related('images', 'video', 'promotions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['promotion_prices'] = AdvertisementPromotion.PRICES
        context['duration_choices'] = AdvertisementPromotion.DURATION_CHOICES
        context['active_promotion'] = self.object.promotions.filter(
            status='active',
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()).first()

        return context

    def get_success_url(self):
        return reverse('advertisement_detail', kwargs={'pk': self.object.pk})


class AdvertisementDeleteView(LoginRequiredMixin, DeleteView):
    model = Advertisement
    success_url = reverse_lazy('my_advertisements')

    def get_queryset(self):
        return Advertisement.objects.filter(
            usto=self.request.user.usto_profile)


class ReviewCreateView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'create_review.html'

    def dispatch(self, request, *args, **kwargs):
        self.advertisement = get_object_or_404(Advertisement, 
                    pk=self.kwargs['pk'], status='active')

        if Review.objects.filter(advertisement=self.advertisement, user=request.user).exists():
            return redirect('advertisement_detail', pk=self.advertisement.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.advertisement = self.advertisement
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('advertisement_detail', kwargs={'pk': self.advertisement.pk})


class MyReviewListView(LoginRequiredMixin, ListView):
    model = Review
    template_name = 'my_reviews.html'
    context_object_name = 'reviews'

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user
                ).select_related('advertisement').order_by('-created_at')


class ReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = Review
    form_class = ReviewForm
    template_name = 'update_review.html'

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse('advertisement_detail', kwargs={'pk': self.object.advertisement.pk})


class ReviewDeleteView(LoginRequiredMixin, DeleteView):
    model = Review

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse('advertisement_detail', kwargs={'pk': self.object.advertisement.pk})






