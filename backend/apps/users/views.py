
from django.db import transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from .models import (
    User,
    UserProfile,
    UserPreference,
    UserAllergy,
    Tag,
    Allergen,
)
from .serializers import (
    UserSerializer,
    UserUpdateSerializer,
    TagSerializer,
    AllergenSerializer,
    UserPreferencesUpdateSerializer,
    UserAllergiesUpdateSerializer,
)



def get_application_user(request):
    """
    Resolve the authenticated Django user to an active
    application User.
    """
    user = get_object_or_404(
        User.objects.select_related("auth_user"),
        auth_user=request.user,
    )

    if user.account_status != User.AccountStatus.ACTIVE:
        raise PermissionDenied(
            "This account is suspended or disabled."
        )

    return user

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_application_user(request)

        UserProfile.objects.get_or_create(user=user)

        serializer = UserSerializer(user)
        return Response(serializer.data)

    def patch(self, request):
        user = get_application_user(request)

        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            profile, _ = UserProfile.objects.get_or_create(
                user=user
            )

            for field, value in serializer.validated_data.items():
                if field == "profile_image":
                    profile.profile_image_reference = value
                else:
                    setattr(profile, field, value)

            profile.save()

        return Response(UserSerializer(user).data)


class CurrentUserPreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_application_user(request)

        tags = Tag.objects.filter(
            user_preferences__user=user
        ).order_by("type", "name")

        return Response({
            "preferences": TagSerializer(tags, many=True).data
        })

    def put(self, request):
        user = get_application_user(request)

        serializer = UserPreferencesUpdateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        tag_ids = serializer.validated_data["tag_ids"]

        with transaction.atomic():
            UserPreference.objects.filter(user=user).delete()

            UserPreference.objects.bulk_create([
                UserPreference(user=user, tag_id=tag_id)
                for tag_id in tag_ids
            ])

        tags = Tag.objects.filter(
            user_preferences__user=user
        ).order_by("type", "name")

        return Response({
            "preferences": TagSerializer(tags, many=True).data
        })


class CurrentUserAllergiesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_application_user(request)

        allergens = Allergen.objects.filter(
            user_allergies__user=user
        ).order_by("name")

        return Response({
            "allergies": AllergenSerializer(
                allergens,
                many=True,
            ).data
        })

    def put(self, request):
        user = get_application_user(request)

        serializer = UserAllergiesUpdateSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        allergen_ids = serializer.validated_data["allergen_ids"]

        with transaction.atomic():
            UserAllergy.objects.filter(user=user).delete()

            UserAllergy.objects.bulk_create([
                UserAllergy(
                    user=user,
                    allergen_id=allergen_id,
                )
                for allergen_id in allergen_ids
            ])

        allergens = Allergen.objects.filter(
            user_allergies__user=user
        ).order_by("name")

        return Response({
            "allergies": AllergenSerializer(
                allergens,
                many=True,
            ).data
        })
