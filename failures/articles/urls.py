from django.urls import path
from .views import public_page, index

app_name = "articles"

urlpatterns = [
    path('admin/', index, name="index"),  # Admin view
    path('public/', public_page, name='public_page'),  # Public page URL
]
