from django.contrib import admin
from django.urls import path
from api.views import (
    EventList, CurrencyList,
    UsersList, ClearAll, isSuperAdmin, testRenderResetTemplateUi, UserCurrencyList, UserCurrencyDetail,
    ExportUserCurrenciesView,EventListCreateAPIView, EventDetailAPIView, ExportEventsView,
UserOwnedCurrenciesView, UserCurrencySummaryView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from api.auth import (RegisterView, confirm_email_view, ConfirmEmailAPI,
                      ForgotPasswordAPI, ResetPasswordAPI,
                      UserAuthentication, UserLogOut, VerifyCodeAPI, ResendCode)

from api.serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/events', EventList.as_view()),
    path('api/v1/register', RegisterView.as_view(), name='register'),
    path('api/v1/resend', ResendCode.as_view(), name='resend'),
    path('api/v1/events/<int:pk>', EventList.as_view(), name='event-detail'),
    path('api/v1/currencies', CurrencyList.as_view(), name='currency'),
    path('api/v1/currencies/<str:currency_name>', CurrencyList.as_view(), name='currency-detail'),
    path('api/v1/authenticate', UserAuthentication.as_view()),
    path('api/v1/confirm-email', ConfirmEmailAPI.as_view(), name='confirm_email'),
    path('api/v1/users', UsersList.as_view(), name='users'),
    path('api/v1/users/<str:username>', UsersList.as_view(), name='user-detail'),
    path('api/v1/forgot-password', ForgotPasswordAPI.as_view(), name='forgot_password'),
    path('api/v1/verify-code', VerifyCodeAPI.as_view(), name='verify_code'),
    path('api/v1/reset-password', ResetPasswordAPI.as_view(), name='reset_password'),
    path('api/v1/logout', UserLogOut.as_view(), name='logout' ),
    path('api/v1/clear-all', ClearAll.as_view(), name='clearr-all'),
    path('api/v1/super-user-check/<str:username>', isSuperAdmin.as_view(), name='is-super-admin'),
    path('api/v1/test-reset-template', testRenderResetTemplateUi.as_view(), name='test-reset-template'),
    path('api/v1/token', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/user-currencies', UserCurrencyList.as_view(), name='user-currency-list'),
    path('api/v1/all-currencies', UserOwnedCurrenciesView.as_view(), name='all-currency-list'),
    path('api/v1/user-currencies/<int:pk>', UserCurrencyDetail.as_view(), name='user-currency-detail'),
    path('api/v1/export_user_currencies', ExportUserCurrenciesView.as_view(), name='export_user_currencies'),
    path('api/v1/events', EventListCreateAPIView.as_view(), name='event-list'),
    path('api/v1/events/<int:pk>', EventDetailAPIView.as_view(), name='event-detail'),
    path('api/v1/events/export', ExportEventsView.as_view(), name='export-events'),
    path('api/v1/cash', UserCurrencySummaryView.as_view(), name='cash' ),

]
