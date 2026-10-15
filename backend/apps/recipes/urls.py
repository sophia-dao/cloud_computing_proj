from rest_framework.routers import SimpleRouter

from .views import RecipeViewSet

router = SimpleRouter()
router.register("recipes", RecipeViewSet, basename="recipe")

urlpatterns = router.urls
