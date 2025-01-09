
from django.contrib import admin
from django.urls import path, include
from quotes import urls
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('quotes.urls')),
]