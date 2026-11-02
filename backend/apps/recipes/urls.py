from rest_framework.routers import SimpleRouter

from .views import RecipeViewSet, TagViewSet

router = SimpleRouter()
router.register("recipes", RecipeViewSet, basename="recipe")
router.register("tags", TagViewSet, basename="tag")

urlpatterns = router.urls
