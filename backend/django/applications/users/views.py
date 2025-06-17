# applications\users\views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from applications.users.services.identify_accounts import identify_user_accounts
from services.profile import get_user_profile

from users.services.login import login_user
from users.services.logout import logout_user
from users.services.refresh_token import refresh_user_token
from users.services.register import register_user
from users.utils.authentication import AppTokenAuthentication
from users.services.register_scan import handle_invoice_scan


class RegisterUserView(APIView):
    permission_classes = []

    def post(self, request):
        success, response_data, http_status = register_user(request.data)
        return Response(response_data, status=http_status)


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        account_id = request.data.get("account_id")

        success, response_data, http_status = login_user(
            email=email, password=password, account_id=account_id
        )
        return Response(response_data, status=http_status)


class RefreshTokenView(APIView):
    permission_classes = []

    def post(self, request):
        refresh_token_str = request.data.get("refresh_token")
        account_id = request.data.get("account_id")

        success, response_data, http_status = refresh_user_token(
            refresh_token_str=refresh_token_str,
            account_id=account_id,
        )
        return Response(response_data, status=http_status)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token_str = getattr(request.auth, "token", None)

        success, response_data, http_status = logout_user(token_str)
        return Response(response_data, status=http_status)


class MeView(APIView):
    # authentication_classes = [AppTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        account_info = getattr(request, "jwt_payload", {}).get("account_info", {})
        data = get_user_profile(
            user=request.user, context={"account_info": account_info}
        )
        return Response(data)


class IdentifyUserAccountsView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        success, response_data, http_status = identify_user_accounts(email, password)
        return Response(response_data, status=http_status)


class RegisterInvoiceScanView(APIView):
    authentication_classes = [AppTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        success, response_data, http_status = handle_invoice_scan(
            user=request.user,
            user_id=user_id,
            jwt_data=request.jwt_payload,
        )
        return Response(response_data, status=http_status)
