from rest_framework.exceptions import NotAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.recipes.filters import get_request_application_user

from .serializers import RecommendationRequestSerializer, RecommendationResultSerializer
from .services import RecommendationService, saved_inventory_ingredient_ids, saved_settings


class RecommendationPagination(PageNumberPagination):
    # Same paging as the recipes and ingredients lists.
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class RecommendationView(APIView):
    """
    POST /api/recommendations/   public; ?page=N and ?page_size=N for paging

    Guests send ingredient IDs. Logged-in users may instead send
    "use_saved_inventory": true, which reads only their own inventory.

    For logged-in users, everything else comes from their own account only:
    - saved allergies are always excluded, on top of any filters.allergen_ids
      (same rule as recipe search: they can't be switched off per request)
    - saved DIET/CUISINE preferences move matching recipes up the list
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        filters = data["filters"]

        if data["use_saved_inventory"]:
            if not request.user.is_authenticated:
                raise NotAuthenticated("Log in to use your saved inventory.")
            ingredient_ids = saved_inventory_ingredient_ids(request.user)
        else:
            ingredient_ids = data["ingredients"]

        saved = saved_settings(get_request_application_user(request))

        service = RecommendationService()
        recipes = service.matching_recipes(
            ingredient_ids,
            data["match_mode"],
            tag_ids=filters["tag_ids"],
            allergen_ids=set(filters["allergen_ids"]) | saved.allergen_ids,
            preferred_tag_ids=saved.preference_tag_ids,
        )

        paginator = RecommendationPagination()
        page = paginator.paginate_queryset(recipes, request, view=self)
        results = service.build_results(page, ingredient_ids)

        return Response(
            {
                "match_mode": data["match_mode"],
                "count": paginator.page.paginator.count,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
                "results": RecommendationResultSerializer(
                    results, many=True, context={"request": request}
                ).data,
            }
        )
