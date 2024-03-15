from django.contrib import admin

from theatre.models import TheatreHall, Actor, Genre, Ticket, Order, Performance, Play

admin.site.register(TheatreHall)
admin.site.register(Genre)
admin.site.register(Actor)
admin.site.register(Play)
admin.site.register(Performance)
admin.site.register(Order)
admin.site.register(Ticket)
