from django.contrib import admin
from django.urls import path , include

handler404 = 'crud.errors.page_not_found'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('api.urls'))
]
