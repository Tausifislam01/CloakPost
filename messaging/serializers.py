from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class ThreadCreateSerializer(serializers.Serializer):
    participants = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False
    )

    def validate_participants(self, value):
        users = list(User.objects.filter(id__in=value).values_list("id", flat=True))
        missing = set(value) - set(users)
        if missing:
            raise serializers.ValidationError(f"Unknown user IDs: {sorted(missing)}")
        return value

class MessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=1, max_length=5000)
