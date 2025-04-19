from django.core.management.base import BaseCommand
from django.utils.timezone import now
from api.models import AdoptedArea

class Command(BaseCommand):
    help = 'Deactivates adopted areas with expired temporary adoption periods.'

    def handle(self, *args, **kwargs):
        today = now().date()
        expired = AdoptedArea.objects.filter(
            adoption_type="temporary",
            end_date__lt=today,
            is_active=True
        )
        count = expired.update(is_active=False)
        self.stdout.write(self.style.SUCCESS(f'Deactivated {count} expired adopted areas.'))
