from rest_framework import mixins, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import InventoryItem
from .serializers import InventoryItemSerializer


class InventoryItemViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET    /api/inventory/       the logged-in user's inventory
    POST   /api/inventory/       add {"ingredient_id": N}; 201 if new, 200 if already there
    DELETE /api/inventory/{id}/  remove one of the user's own items

    All endpoints require login. There is no PATCH: per database-design.md an
    inventory item has no editable fields. To swap an ingredient, delete the
    item and add the new one.
    """

    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Every lookup, including DELETE by ID, only ever sees the requester's
        # own rows. Another user's item ID is simply not found (404).
        if not self.request.user.is_authenticated:
            return InventoryItem.objects.none()
        return InventoryItem.objects.for_user(self.request.user)

    def list(self, request, *args, **kwargs):
        # Not paginated: the unique (user, ingredient) constraint caps a user's
        # inventory at one row per canonical ingredient.
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response({"results": serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item, created = InventoryItem.objects.add(
            user=request.user,
            ingredient=serializer.validated_data["ingredient"],
        )
        return Response(
            self.get_serializer(item).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
