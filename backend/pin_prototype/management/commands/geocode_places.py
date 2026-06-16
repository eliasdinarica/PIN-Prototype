from django.core.management.base import BaseCommand
from pin_prototype.models import ResourcePlace, geocode_ch


class Command(BaseCommand):
    help = 'Fill latitude/longitude for places that have an address but no coordinates.'

    def handle(self, *args, **options):
        qs = ResourcePlace.objects.filter(latitude__isnull=True).exclude(address='')
        total = qs.count()
        ok = 0
        for p in qs:
            coords = geocode_ch(p.address)
            if coords:
                p.latitude, p.longitude = coords
                p.save(geocode=False)
                ok += 1
                self.stdout.write(f'  OK  {p.name} — {p.address}')
            else:
                self.stdout.write(f'  --  {p.name} — {p.address}')
        self.stdout.write(self.style.SUCCESS(f'\nGeocoded {ok}/{total} places.'))
