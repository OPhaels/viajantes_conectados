from django.http import JsonResponse


def set_cookie_view(request):
    response = JsonResponse({"message": "Cookie set successfully!"})
    response.set_cookie(
        key="user_preferences",
        value='{"theme": "dark", "language": "pt-br"}',
        max_age=3600,  # 1 hora
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    return response


def get_cookie_view(request):
    user_preferences = request.COOKIES.get("user_preferences")
    return JsonResponse({"user_preferences": user_preferences})
