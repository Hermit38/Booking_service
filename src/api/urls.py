from django.urls import path

from . import views

urlpatterns = [
    # users
    path("users", views.UserListCreateView.as_view()),
    path("users/<int:user_id>", views.UserDetailView.as_view()),
    # hotels
    path("hotels", views.HotelListCreateView.as_view()),
    path("hotels/<int:hotel_id>", views.HotelDetailView.as_view()),
    # rooms
    path("rooms", views.RoomListCreateView.as_view()),
    path("rooms/<int:room_id>", views.RoomDetailView.as_view()),
    # bookings
    path("bookings", views.BookingListCreateView.as_view()),
    path("bookings/<int:booking_id>", views.BookingDetailView.as_view()),
]
