import random
import uuid
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from tickets.models import Venue, Event, Tickettype, Order, Ticket

class Command(BaseCommand):
    help = "Seeds the database with required venues, events, ticket types, orders, and tickets"

    def handle(self, *args, **options):
        if Event.objects.exists():
            self.stdout.write(self.style.SUCCESS("Database already contains event data. Skipping seeding."))
            return

        self.stdout.write("Starting database seeding...")

        venue_data = [
            {"name": "The Garage", "city": "Santiago"},
            {"name": "Subterranean", "city": "Buenos Aires"},
            {"name": "Lincoln Hall", "city": "Bogota"},
            {"name": "Metro Concert Hall", "city": "Lima"},
            {"name": "Thalia Theatre", "city": "Mexico City"},
            {"name": "Schubas Tavern", "city": "Chicago"},
            {"name": "Empty Bottle Lounge", "city": "New York"},
            {"name": "Beat Kitchen", "city": "London"},
            {"name": "Reggie's Rock Club", "city": "Santiago"},
            {"name": "Cobra Lounge", "city": "Mexico City"},
        ]

        venues = []
        for vd in venue_data:
            v = Venue(name=vd["name"], city=vd["city"])
            venues.append(v)
        
        Venue.objects.bulk_create(venues)
        db_venues = list(Venue.objects.all())
        self.stdout.write(f"Created {len(db_venues)} venues.")

        band_names = [
            "The Pixies", "Daft Punk", "Radiohead", "Arctic Monkeys", "The Strokes",
            "Tame Impala", "Interpol", "Phoenix", "LCD Soundsystem", "Gorillaz",
            "Queens of the Stone Age", "The National", "Foals", "Franz Ferdinand",
            "Modest Mouse", "Arcade Fire", "Vampire Weekend", "Yeah Yeah Yeahs",
            "Bloc Party", "Hot Chip", "The Killers", "Muse", "Nine Inch Nails",
            "Depeche Mode", "The Cure", "New Order", "The Smiths Tribute",
            "Salsa Brava Allstars", "Bogota Techno Collective", "Santiago Jazz Quartet"
        ]
        
        event_types = ["Live", "Experience", "Rave", "Tribute", "Session", "Unplugged", "Festival", "Club Night"]

        events = []
        now = timezone.now()
        
        for i in range(300):
            band = band_names[i % len(band_names)]
            etype = event_types[i % len(event_types)]
            title = f"{band} - {etype} {i + 1}"
            description = f"Don't miss the spectacular performance of {band} for an exclusive {etype} night at one of the finest venues."
            
            days_offset = random.randint(-10, 120)
            hours_offset = random.randint(18, 22)
            starts_at = (now + timedelta(days=days_offset)).replace(hour=hours_offset, minute=0, second=0, microsecond=0)
            
            total_capacity = 600 + random.randint(50, 400)
            venue = random.choice(db_venues)
            
            e = Event(
                title=title,
                description=description,
                starts_at=starts_at,
                total_capacity=total_capacity,
                venue=venue
            )
            events.append(e)

        Event.objects.bulk_create(events)
        db_events = list(Event.objects.all())
        self.stdout.write(f"Created {len(db_events)} events.")

        ticket_types_to_create = []
        for ev in db_events:
            cap = ev.total_capacity
            eb_qty = int(cap * 0.15)
            vip_qty = int(cap * 0.15)
            ga_qty = cap - eb_qty - vip_qty 
            
            eb_price = random.randint(15, 30)
            ga_price = random.randint(35, 75)
            vip_price = random.randint(90, 180)

            eb_start = ev.starts_at - timedelta(days=30)
            eb_end = ev.starts_at - timedelta(days=10)

            ga_start = ev.starts_at - timedelta(days=10)
            ga_end = ev.starts_at + timedelta(days=1)

            vip_start = ev.starts_at - timedelta(days=30)
            vip_end = ev.starts_at + timedelta(days=1)

            tt_eb = Tickettype(
                name="Early Bird", 
                price=eb_price, 
                total_quantity=eb_qty, 
                event=ev,
                start_date=eb_start,
                end_date=eb_end
            )
            tt_ga = Tickettype(
                name="General Admission", 
                price=ga_price, 
                total_quantity=ga_qty, 
                event=ev,
                start_date=ga_start,
                end_date=ga_end
            )
            tt_vip = Tickettype(
                name="VIP", 
                price=vip_price, 
                total_quantity=vip_qty, 
                event=ev,
                start_date=vip_start,
                end_date=vip_end
            )
            
            ticket_types_to_create.extend([tt_eb, tt_ga, tt_vip])

        Tickettype.objects.bulk_create(ticket_types_to_create)
        db_ticket_types = list(Tickettype.objects.all())
        self.stdout.write(f"Created {len(db_ticket_types)} ticket types.")

        orders = []
        for i in range(1500):
            email = f"customer_{i}@example.com"
            o = Order(customer_email=email)
            orders.append(o)
        
        Order.objects.bulk_create(orders)
        db_orders = list(Order.objects.all())
        self.stdout.write(f"Created {len(db_orders)} orders.")

        tt_by_event = {}
        for tt in db_ticket_types:
            tt_by_event.setdefault(tt.event_id, []).append(tt)

        tickets_to_create = []
        for ev in db_events:
            event_tts = tt_by_event.get(ev.id, [])
            if len(event_tts) < 3:
                continue
            
            # Sort by name/price so we know which is which: VIP, General, Early Bird
            eb_tt = next(t for t in event_tts if t.name == "Early Bird")
            ga_tt = next(t for t in event_tts if t.name == "General Admission")
            vip_tt = next(t for t in event_tts if t.name == "VIP")
            
            
            sales_plan = [
                (eb_tt, 100),
                (ga_tt, 350),
                (vip_tt, 50),
            ]
            
            for tt, count in sales_plan:
                for _ in range(count):
                    t = Ticket(
                        order=random.choice(db_orders),
                        ticket_type=tt
                    )
                    tickets_to_create.append(t)

        batch_size = 10000
        for i in range(0, len(tickets_to_create), batch_size):
            batch = tickets_to_create[i:i+batch_size]
            Ticket.objects.bulk_create(batch)
            self.stdout.write(f"Created tickets batch {i // batch_size + 1}...")

        self.stdout.write(self.style.SUCCESS(f"Database successfully seeded with {len(db_events)} events and {len(tickets_to_create)} tickets!"))
