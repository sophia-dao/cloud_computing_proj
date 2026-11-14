from rest_framework.routers import SimpleRouter

from .views import RecipeViewSet, SavedRecipeViewSet, TagViewSet

router = SimpleRouter()
router.register("recipes", RecipeViewSet, basename="recipe")
router.register("tags", TagViewSet, basename="tag")
router.register("saved-recipes", SavedRecipeViewSet, basename="saved-recipe")

urlpatterns = router.urls
