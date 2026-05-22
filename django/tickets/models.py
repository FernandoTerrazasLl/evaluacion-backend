import uuid
from django.db import models

class TimeStampedUUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        managed = False


class Venue(TimeStampedUUIDModel):
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'venue'

    def __str__(self):
        return f"{self.name} ({self.city})"


class Event(TimeStampedUUIDModel):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    starts_at = models.DateTimeField()
    total_capacity = models.IntegerField()
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='events')

    class Meta:
        managed = False
        db_table = 'event'

    def __str__(self):
        return self.title


class Tickettype(TimeStampedUUIDModel):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total_quantity = models.IntegerField()
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_types')
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tickettype'

    def __str__(self):
        return f"{self.name} - {self.event.title} (${self.price})"


class Order(TimeStampedUUIDModel):
    customer_email = models.CharField(max_length=150)

    class Meta:
        managed = False
        db_table = 'order'

    def __str__(self):
        return f"Order {self.id} ({self.customer_email})"


class Ticket(TimeStampedUUIDModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tickets')
    ticket_type = models.ForeignKey(Tickettype, on_delete=models.RESTRICT, related_name='tickets')

    class Meta:
        managed = False
        db_table = 'ticket'

    def __str__(self):
        return f"Ticket {self.id} for {self.ticket_type.name}"
