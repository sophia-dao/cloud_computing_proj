
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .filters import (
    apply_user_defaults,
    filter_recipes,
    get_request_application_user,
    parse_recipe_filters,
)
from .models import Recipe, Tag
from .permissions import IsOwnerOrAdminOrReadOnly
from .serializers import (
    RecipeDetailSerializer,
    RecipeImageSerializer,
    RecipeListSerializer,
    RecipeMatchSerializer,
    RecipeNameCheckSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)
from .services import find_recipes_with_same_name, normalize_recipe_name


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

    Recipe submission (Issue #67):
    GET    /api/recipes/duplicates/?name=...  public; same-name recipes to warn about
    POST   /api/recipes/{id}/image/           owner or admin; multipart "image" file
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

    @action(detail=False, methods=["get"], url_path="duplicates")
    def duplicates(self, request):
        """Recipes with the same name as ?name=, ignoring case and extra spaces.

        Only a warning for the Add Recipe form: creating a recipe with a
        duplicate name is still allowed.
        """
        query = RecipeNameCheckSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        name = normalize_recipe_name(query.validated_data["name"])
        matches = find_recipes_with_same_name(name)
        return Response({"name": name, "matches": RecipeMatchSerializer(matches, many=True).data})

    @action(
        detail=True,
        methods=["post"],
        url_path="image",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_image(self, request, pk=None):
        """Add or replace a recipe's image. Same owner/admin rule as editing."""
        recipe = self.get_object()
        upload = RecipeImageSerializer(data=request.data)
        upload.is_valid(raise_exception=True)
        recipe.image = upload.validated_data["image"]
        recipe.save(update_fields=["image", "updated_at"])
        recipe = Recipe.objects.with_detail_relations().get(pk=recipe.pk)
        return Response(RecipeDetailSerializer(recipe, context=self.get_serializer_context()).data)

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/tags/       List all available tags.
    GET /api/tags/{id}/  Retrieve a tag.
    """

    queryset = Tag.objects.all().order_by("type", "name")
    serializer_class = TagSerializer
    permission_classes = []
    pagination_class = None