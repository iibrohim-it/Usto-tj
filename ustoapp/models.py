from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from django.core.validators import MinValueValidator, MaxValueValidator


class UstoProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='usto_profile')
    phone = models.CharField(max_length=17, blank=True, null=True)
    avatar = models.ImageField(upload_to='masters/', blank=True, null=True)
    city = models.CharField(max_length=150, blank=True)
    experience = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Category(models.Model):
    name = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Advertisement(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает проверки'),
        ('active', 'Активно'),
        ('expired', 'Истекло'),
        ('rejected', 'Отклонено'),
    ]
    
    usto = models.ForeignKey(UstoProfile, on_delete=models.CASCADE, related_name='advertisements')
    category = models.ForeignKey(Category, on_delete=models.PROTECT,
                        blank=True, null=True, related_name='advertisements')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    expires_at = models.DateTimeField(blank=True, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    city = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def average_rating(self):
        return self.reviews.aggregate(average=Avg('rating'))['average'] or 0

    def __str__(self):
        return self.title


class AdvertisementImage(models.Model):
    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='advertisement/images/')

    def __str__(self):
        return self.advertisement.title


class AdvertisementVideo(models.Model):
    advertisement = models.OneToOneField(Advertisement, on_delete=models.CASCADE, related_name='video')
    video = models.FileField(upload_to='advertisement/videos/')

    def __str__(self):
        return self.advertisement.title


class Review(models.Model):
    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('advertisement', 'user')

    def __str__(self):
        return self.user.username


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'advertisement')

    def __str__(self):
        return f'{self.user.username} - {self.advertisement.title}'


class AdvertisementView(models.Model):
    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='advertisement_views')
    session_key = models.CharField(max_length=50, blank=True, null=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.advertisement.title


class ServiceRequest(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('accepted', 'Принят'),
        ('rejected', 'Отклонён'),
        ('completed', 'Завершён'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_requests')
    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name='service_requests')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.advertisement.title}'


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class AdvertisementPromotion(models.Model):
    PRICES = {
        'premium': {
            3: 15,
            5: 23,
            7: 30,
            10: 40,
            14: 52,
        },
        'top': {
            3: 30,
            5: 45,
            7: 60,
            10: 80,
            14: 100,
        }
    }   
    
    PROMOTION_CHOICES = [
        ('premium', 'Premium'),
        ('top', 'Top'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('active', 'Активно'),
        ('expired', 'Истекло'),
        ('rejected', 'Отклонено'),
    ]

    DURATION_CHOICES = [
        (3, '3 дня'),
        (5, '5 дней'),
        (7, '7 дней'),
        (10, '10 дней'),
        (14, '14 дней'),
    ]

    advertisement = models.ForeignKey(Advertisement, on_delete=models.CASCADE, related_name='promotions')
    promotion_type = models.CharField(max_length=20, choices=PROMOTION_CHOICES)
    duration_days = models.PositiveSmallIntegerField(choices=DURATION_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        return self.PRICES[self.promotion_type][self.duration_days]

    def __str__(self):
        return f'{self.advertisement.title} - {self.promotion_type}'