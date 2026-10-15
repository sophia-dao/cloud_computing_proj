from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .filters import (
    apply_user_defaults,
    filter_recipes,
    get_request_application_user,
    parse_recipe_filters,
)
from .models import Recipe
from .permissions import IsOwnerOrAdminOrReadOnly
from .serializers import RecipeDetailSerializer, RecipeListSerializer, RecipeWriteSerializer


class RecipePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class RecipeViewSet(viewsets.ModelViewSet):
    """
    GET    /api/recipes/        public, paginated, searchable/filterable
                                (api-design.md section 19.1, filters.py)
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
            criteria = apply_user_defaults(
                parse_recipe_filters(self.request.query_params),
                get_request_application_user(self.request),
            )
            return filter_recipes(Recipe.objects.with_list_relations(), criteria)
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
