from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
import uuid
from tickets.models import Venue, Event, Tickettype, Order, Ticket

class VenueModelTest(TestCase):
    def test_venue_creation(self):
        """Test 1: Test Venue creation and string representation."""
        venue = Venue(
            id=uuid.uuid4(),
            name="Equinoccio",
            city="La Paz"
        )
        self.assertEqual(str(venue), "Equinoccio (La Paz)")
        self.assertEqual(venue.name, "Equinoccio")
        self.assertEqual(venue.city, "La Paz")


class EventModelTest(TestCase):
    def test_event_creation(self):
        """Test 2: Test Event creation and relation to Venue."""
        venue = Venue(id=uuid.uuid4(), name="Equinoccio", city="La Paz")
        event_time = timezone.now() + timedelta(days=5)
        event = Event(
            id=uuid.uuid4(),
            title="Rock Night",
            description="Classic Bolivian rock bands",
            starts_at=event_time,
            total_capacity=150,
            venue=venue
        )
        self.assertEqual(str(event), "Rock Night")
        self.assertEqual(event.title, "Rock Night")
        self.assertEqual(event.total_capacity, 150)
        self.assertEqual(event.venue.name, "Equinoccio")


class TickettypeModelTest(TestCase):
    def test_tickettype_creation_with_validity_dates(self):
        """Test 3: Test Tickettype creation with active start/end validity dates."""
        venue = Venue(id=uuid.uuid4(), name="Arena Sonilum", city="Santa Cruz")
        event = Event(id=uuid.uuid4(), title="Indie Fest", starts_at=timezone.now(), total_capacity=500, venue=venue)
        
        start_date = timezone.now() - timedelta(days=5)
        end_date = timezone.now() + timedelta(days=2)
        
        tt = Tickettype(
            id=uuid.uuid4(),
            name="Early Bird",
            price=45.00,
            total_quantity=75,
            event=event,
            start_date=start_date,
            end_date=end_date
        )
        self.assertEqual(str(tt), f"Early Bird - Indie Fest ($45.0)")
        self.assertEqual(tt.name, "Early Bird")
        self.assertEqual(float(tt.price), 45.00)
        self.assertEqual(tt.total_quantity, 75)
        self.assertEqual(tt.start_date, start_date)
        self.assertEqual(tt.end_date, end_date)


class OrderModelTest(TestCase):
    def test_order_creation(self):
        """Test 4: Test Order creation and customer email."""
        order = Order(
            id=uuid.uuid4(),
            customer_email="fer@example.com"
        )
        self.assertIn("fer@example.com", str(order))
        self.assertEqual(order.customer_email, "fer@example.com")


class TicketModelTest(TestCase):
    def test_ticket_creation(self):
        """Test 5: Test Ticket creation and relationships to Order & Tickettype."""
        venue = Venue(id=uuid.uuid4(), name="Equinoccio", city="La Paz")
        event = Event(id=uuid.uuid4(), title="Lounge Session", starts_at=timezone.now(), total_capacity=100, venue=venue)
        tt = Tickettype(id=uuid.uuid4(), name="VIP", price=120.00, total_quantity=20, event=event)
        order = Order(id=uuid.uuid4(), customer_email="customer@example.com")
        
        ticket = Ticket(
            id=uuid.uuid4(),
            order=order,
            ticket_type=tt
        )
        self.assertIn("Ticket", str(ticket))
        self.assertEqual(ticket.ticket_type.name, "VIP")
        self.assertEqual(ticket.order.customer_email, "customer@example.com")
