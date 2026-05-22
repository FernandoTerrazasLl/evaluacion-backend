from django.contrib import admin
from .models import Venue, Event, Tickettype, Ticket, Order

class BaseAdminMixin:
    readonly_fields = ('created', 'modified')
    exclude = ('id', 'created', 'modified')


class BaseTabularInline(BaseAdminMixin, admin.TabularInline):
    extra = 0


class BaseModelAdmin(BaseAdminMixin, admin.ModelAdmin):
    list_per_page = 20



class TickettypeInline(BaseTabularInline):
    model = Tickettype


class TicketInline(BaseTabularInline):
    model = Ticket


@admin.register(Venue)
class VenueAdmin(BaseModelAdmin):
    list_display = ('name', 'city', 'created', 'modified')
    search_fields = ('name', 'city')
    list_filter = ('city',)
    ordering = ('name',)


@admin.register(Event)
class EventAdmin(BaseModelAdmin):
    list_display = ('title', 'venue', 'starts_at', 'total_capacity', 'created', 'modified')
    search_fields = ('title', 'description', 'venue__name')
    list_filter = ('venue', 'starts_at')
    inlines = (TickettypeInline,)
    ordering = ('starts_at',)


@admin.register(Tickettype)
class TickettypeAdmin(BaseModelAdmin):
    list_display = ('name', 'event', 'price', 'total_quantity', 'created', 'modified')
    search_fields = ('name', 'event__title')
    list_filter = ('event',)
    ordering = ('name',)


@admin.register(Order)
class OrderAdmin(BaseModelAdmin):
    list_display = ('customer_email', 'created', 'modified')
    search_fields = ('customer_email',)
    inlines = (TicketInline,)
    ordering = ('-created',)


@admin.register(Ticket)
class TicketAdmin(BaseModelAdmin):
    list_display = ('ticket_type', 'order', 'created', 'modified')
    search_fields = ('order__customer_email', 'ticket_type__name')
    list_filter = ('ticket_type', 'created')
    ordering = ('-created',)