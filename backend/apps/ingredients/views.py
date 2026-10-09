
from rest_framework import generics, permissions, serializers
from rest_framework.pagination import PageNumberPagination

from .serializers import IngredientSerializer

from .models import Ingredient


class IngredientPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class IngredientListView(generics.ListAPIView):
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = IngredientPagination

    def get_queryset(self):
        queryset = Ingredient.objects.all()

        search = self.request.query_params.get("search", "")

        if len(search) > 255:
            raise serializers.ValidationError({
                "search": "Search must be 255 characters or fewer."
            })

        search = search.strip()

        if search:
            queryset = queryset.filter(name__icontains=search)

        return queryset


class IngredientDetailView(generics.RetrieveAPIView):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [permissions.AllowAny]
