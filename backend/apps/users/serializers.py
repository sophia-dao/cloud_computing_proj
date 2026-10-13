
from rest_framework import serializers

from .models import User, UserProfile, Tag, Allergen


class UserProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.URLField(
        source="profile_image_reference",
        allow_null=True,
        required=False,
    )

    class Meta:
        model = UserProfile
        fields = ["display_name", "profile_image"]


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        source="auth_user.email",
        read_only=True,
    )
    display_name = serializers.CharField(
        source="profile.display_name",
        read_only=True,
    )
    profile_image = serializers.URLField(
        source="profile.profile_image_reference",
        read_only=True,
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "display_name",
            "profile_image",
            "is_admin",
        ]
        read_only_fields = fields


class UserUpdateSerializer(serializers.Serializer):
    display_name = serializers.CharField(
        max_length=150,
        allow_blank=True,
        required=False,
    )
    profile_image = serializers.URLField(
        allow_blank=True,
        allow_null=True,
        required=False,
    )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "type"]


class AllergenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergen
        fields = ["id", "name"]


class UserPreferencesSerializer(serializers.Serializer):
    preferences = TagSerializer(many=True, read_only=True)


class UserPreferencesUpdateSerializer(serializers.Serializer):
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
    )

    def validate_tag_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                "Duplicate tag IDs are not allowed."
            )

        existing_ids = set(
            Tag.objects.filter(id__in=value)
            .values_list("id", flat=True)
        )

        if existing_ids != set(value):
            raise serializers.ValidationError(
                "One or more tag IDs do not exist."
            )

        return value


class UserAllergiesUpdateSerializer(serializers.Serializer):
    allergen_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True,
    )

    def validate_allergen_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError(
                "Duplicate allergen IDs are not allowed."
            )

        existing_ids = set(
            Allergen.objects.filter(id__in=value)
            .values_list("id", flat=True)
        )

        if existing_ids != set(value):
            raise serializers.ValidationError(
                "One or more allergen IDs do not exist."
            )

        return value
