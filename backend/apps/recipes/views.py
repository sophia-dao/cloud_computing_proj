
from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import (
    apply_user_defaults,
    filter_recipes,
    get_request_application_user,
    parse_recipe_filters,
)
from .models import Recipe, SavedRecipe, Tag
from .permissions import IsOwnerOrAdminOrReadOnly
from .serializers import (
    RecipeDetailSerializer,
    RecipeImageSerializer,
    RecipeListSerializer,
    RecipeMatchSerializer,
    RecipeNameCheckSerializer,
    RecipeWriteSerializer,
    SavedRecipeSerializer,
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


class SavedRecipeViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Saved recipes (Issue #14). Signed-in users only, each sees only their own.

    GET    /api/saved-recipes/                your saved recipes, newest first (paginated)
    GET    /api/saved-recipes/?recipe_id=42   is recipe 42 saved? (0 or 1 result)
    POST   /api/saved-recipes/                {"recipe_id": 42}; 201, or 200 if already saved
    DELETE /api/saved-recipes/{id}/           unsave; someone else's bookmark is a 404
    """

    serializer_class = SavedRecipeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = RecipePagination

    def get_queryset(self):
        # Always scoped to the requester, so other users' bookmarks can't be
        # listed or deleted. They simply don't exist from this user's view.
        saved = SavedRecipe.objects.filter(user=self.request.user)
        if self.action == "list":
            saved = saved.select_related("recipe").prefetch_related("recipe__tags")
            recipe_id = self.request.query_params.get("recipe_id")
            if recipe_id is not None:
                if not recipe_id.isdigit():
                    raise ValidationError({"recipe_id": ["Must be a recipe ID."]})
                saved = saved.filter(recipe_id=int(recipe_id))
        return saved

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # get_or_create also copes with two saves arriving at once: the unique
        # constraint stops the second insert and the existing row is returned.
        saved, created = SavedRecipe.objects.get_or_create(
            user=request.user, recipe=serializer.validated_data["recipe"]
        )
        return Response(
            self.get_serializer(saved).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
