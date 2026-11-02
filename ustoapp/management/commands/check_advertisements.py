from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from ustoapp.models import Advertisement, Notification


class Command(BaseCommand):
    help = 'Check expired advertisements'

    def handle(self, *args, **options):
        now = timezone.now()

        soon_expiring = Advertisement.objects.filter(
            status='active',
            expires_at__gt=now,
            expires_at__lte=now + timedelta(days=1)
        ).select_related('usto__user')

        for ad in soon_expiring:
            title = f'Срок объявления «{ad.title}» скоро истечёт'

            if not Notification.objects.filter(
                user=ad.usto.user, title=title).exists():

                Notification.objects.create(user=ad.usto.user,
                    title=title,
                    message=f'Ваше объявление «{ad.title}» скоро истечёт. Продлите его.')

        expired_ads = Advertisement.objects.filter(
            status='active',
            expires_at__lte=now).select_related('usto__user')

        for ad in expired_ads:
            ad.status = 'expired'
            ad.save(update_fields=['status'])

            Notification.objects.create(
                user=ad.usto.user,
                title=f'Объявление «{ad.title}» истекло',
                message=f'Срок объявления «{ad.title}» закончился. Вы можете продлить его на 14 дней.'
            )

        self.stdout.write(self.style.SUCCESS('Advertisements checked successfully!'))
