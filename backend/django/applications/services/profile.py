from users.serializers import UserWithAccountSerializer


def get_user_profile(user, context: dict = None) -> dict:
    serializer = UserWithAccountSerializer(user, context=context or {})
    return serializer.data
