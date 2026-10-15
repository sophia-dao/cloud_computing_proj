from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .models import Recipe
from .permissions import IsOwnerOrAdminOrReadOnly
from .serializers import RecipeDetailSerializer, RecipeListSerializer, RecipeWriteSerializer


class RecipePagination(PageNumberPagination):
    page_size = 20


class RecipeViewSet(viewsets.ModelViewSet):
    """
    GET    /api/recipes/        public, paginated
    GET    /api/recipes/{id}/   public
    POST   /api/recipes/        logged-in users; owner is the requester
    PATCH  /api/recipes/{id}/   owner or admin
    DELETE /api/recipes/{id}/   owner or admin
    """

    permission_classes = [IsOwnerOrAdminOrReadOnly]
    pagination_class = RecipePagination
    # api-design.md defines PATCH for updates, not PUT.
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        if self.action == "list":
            return Recipe.objects.with_list_relations()
        if self.action == "retrieve":
            return Recipe.objects.with_detail_relations()
        return Recipe.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return RecipeListSerializer
        if self.action == "retrieve":
            return RecipeDetailSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
