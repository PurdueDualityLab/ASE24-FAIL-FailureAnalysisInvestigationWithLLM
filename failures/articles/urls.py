from django.urls import path
from .views import public_page, index
from .views import incident_detail_view

app_name = "articles"

urlpatterns = [
    path('admin/', index, name="index"),  # Admin view
    path('public/', public_page, name='public_page'),  # Public page URL
    path('incident/<int:pk>/', incident_detail_view, name='incident-detail'),  # Route for detail view
]
