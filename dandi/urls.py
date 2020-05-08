from django.contrib import admin
from django.urls import include, path

from publish.api import DandisetViewSet

from rest_framework import routers


router = routers.DefaultRouter()
router.register('dandisets', DandisetViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('admin/', admin.site.urls),
]
