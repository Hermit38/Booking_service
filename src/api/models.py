"""Модели только описывают схему для ORM: managed = False, миграций нет.

Владелец DDL — schema.sql (таблицы, индексы, CHECK/UNIQUE/exclusion constraints).
"""

from django.db import models


class User(models.Model):
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "users"


class Hotel(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=500)
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "hotels"


class Room(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="rooms")
    room_number = models.CharField(max_length=20)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "rooms"


class Booking(models.Model):
    # Пользователя с бронями удалять нельзя; при удалении номера его брони сносятся
    user = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="bookings")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bookings")
    date_start = models.DateField()
    date_end = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "bookings"
