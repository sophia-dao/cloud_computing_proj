
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .filters import (
    apply_user_defaults,
    filter_recipes,
    get_request_application_user,
    parse_recipe_filters,
)
from .models import Recipe, Tag
from .permissions import IsOwnerOrAdminOrReadOnly
from .serializers import RecipeDetailSerializer, RecipeListSerializer, RecipeWriteSerializer, TagSerializer


class RecipePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class RecipeViewSet(viewsets.ModelViewSet):
    """
    GET    /api/recipes/        public, paginated, searchable, filterable
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
            queryset = Recipe.objects.with_list_relations()

            criteria = parse_recipe_filters(self.request.query_params)
            application_user = get_request_application_user(self.request)
            criteria = apply_user_defaults(criteria, application_user)

            return filter_recipes(queryset, criteria)

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

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/tags/       List all available tags.
    GET /api/tags/{id}/  Retrieve a tag.
    """

    queryset = Tag.objects.all().order_by("type", "name")
    serializer_class = TagSerializer
    permission_classes = []
    pagination_class = None