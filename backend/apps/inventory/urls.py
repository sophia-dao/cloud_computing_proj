from rest_framework.routers import SimpleRouter

from .views import InventoryItemViewSet

router = SimpleRouter()
router.register("inventory", InventoryItemViewSet, basename="inventory")

urlpatterns = router.urls
