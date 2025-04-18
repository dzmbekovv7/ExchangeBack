from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import ObjectDoesNotExist
from twilio.base.obsolete import ObsoleteException

from .serializers import RegisterSerializer
import logging
from django.views.decorators.csrf import csrf_exempt
logger = logging.getLogger(__name__)
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
import logging
from django.contrib.auth.hashers import check_password
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.core.mail import send_mail
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
import random
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
logger = logging.getLogger(__name__)

def generate_confirmation_code():
    return ''.join(random.choices('0123456789', k=6))

def send_confirmation_email(user, confirmation_code):
    subject = 'Подтверждение регистрации'
    message = f'Здравствуйте, {user.username}! Подтвердите вашу почту с помощью следующего кода: {confirmation_code}'
    from_email = 'ExchangeWork <aziretdzumabekov19@gmail.com>'
    recipient_list = [user.email]

    html_message = f'''
    <html>
        <head>
            <style>
                body {{
                    background-color: #f2f4f6;
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background-color: #ffffff;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .header h2 {{
                    color: #333333;
                }}
                .content p {{
                    font-size: 16px;
                    color: #555555;
                    line-height: 1.6;
                }}
                .code {{
                    margin: 20px auto;
                    font-size: 28px;
                    font-weight: bold;
                    background-color: #e0f7e9;
                    color: #2e7d32;
                    padding: 15px;
                    text-align: center;
                    border-radius: 5px;
                    width: 200px;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #999999;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Подтверждение регистрации</h2>
                </div>
                <div class="content">
                    <p>Здравствуйте, <strong>{user.username}</strong>!</p>
                    <p>Спасибо за регистрацию на ExchangeWork.</p>
                    <p>Пожалуйста, используйте следующий код для подтверждения вашей почты:</p>
                    <div class="code">{confirmation_code}</div>
                    <p>Если вы не регистрировались, просто проигнорируйте это письмо.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2025 ExchangeWork. Все права защищены.</p>
                </div>
            </div>
        </body>
    </html>
    '''

    try:
        print(user.email)
        send_mail(subject, message, from_email, recipient_list, html_message=html_message)
    except Exception as e:
        logger.error(f"Ошибка отправки письма подтверждения: {str(e)}")

def send_password_reset_email(user, reset_code):
    subject = 'Сброс пароля'
    message = f'Здравствуйте, {user.username}! Ваш код для сброса пароля: {reset_code}'
    from_email = 'ExchangeWork <aziretdzumabekov19@gmail.com>'
    recipient_list = [user.email]

    html_message = f'''
    <html>
        <head>
            <style>
                body {{
                    background-color: #f2f4f6;
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background-color: #ffffff;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .header h2 {{
                    color: #333333;
                }}
                .content p {{
                    font-size: 16px;
                    color: #555555;
                    line-height: 1.6;
                }}
                .code {{
                    margin: 20px auto;
                    font-size: 28px;
                    font-weight: bold;
                    background-color: #fff3cd;
                    color: #856404;
                    padding: 15px;
                    text-align: center;
                    border-radius: 5px;
                    width: 200px;
                }}
                .footer {{
                    text-align: center;
                    font-size: 12px;
                    color: #999999;
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Сброс пароля</h2>
                </div>
                <div class="content">
                    <p>Здравствуйте, <strong>{user.username}</strong>!</p>
                    <p>Мы получили запрос на сброс вашего пароля.</p>
                    <p>Пожалуйста, введите следующий код для создания нового пароля:</p>
                    <div class="code">{reset_code}</div>
                    <p>Если вы не запрашивали сброс пароля, проигнорируйте это письмо.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2025 ExchangeWork. Все права защищены.</p>
                </div>
            </div>
        </body>
    </html>
    '''


    send_mail(subject, message, from_email, recipient_list, html_message=html_message)

@csrf_exempt
def confirm_email_view(request):
    if request.method == 'POST':
        confirmation_code = request.POST.get('confirmation_code')
        try:
            user = User.objects.get(confirmation_code=confirmation_code)
            if user:
                user.email_confirmed = True
                user.confirmation_code = None  # Clear the confirmation code
                user.save()
                messages.success(request, 'Your account has been activated! You can now log in.')
                return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'Invalid confirmation code. Please try again.')

    return render(request, 'users/waiting_for_confirmation.html')

class ForgotPasswordAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            reset_code = generate_confirmation_code()  # Генерируем код сброса
            user.reset_code = reset_code
            user.save()

            send_password_reset_email(user, reset_code)  # Отправляем код на почту

            return Response({"message": "Password reset code sent to your email."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"message": "User with this email not found."}, status=status.HTTP_400_BAD_REQUEST)

class VerifyCodeAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        reset_code = request.data.get('reset_code')

        if not reset_code:
            return Response({"message": "Reset code is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(reset_code=reset_code)

            return Response({"message": "Code is valid, you can now reset your password."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"message": "Invalid reset code."}, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Получаем новый пароль и его подтверждение
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        # Проверяем, что оба пароля введены
        if not new_password or not confirm_password:
            return Response({"message": "New password and confirmation are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, что пароли совпадают
        if new_password != confirm_password:
            return Response({"message": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем код сброса из запроса
        reset_code = request.data.get('reset_code')

        if not reset_code:
            return Response({"message": "Reset code is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Ищем пользователя с этим кодом сброса
            user = User.objects.get(reset_code=reset_code)

            # Обновляем пароль
            user.set_password(new_password)
            user.reset_code = None  # Очищаем код сброса после использования
            user.save()  # Сохраняем изменения в базе данных

            return Response({"message": "Password has been successfully reset."}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({"message": "Invalid reset code."}, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            confirmation_code = generate_confirmation_code()
            user.confirmation_code = confirmation_code
            user.save()

            send_confirmation_email(user, confirmation_code)

            return Response({'message': 'User registered, please confirm your email'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendCode(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({"message": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except ObjectDoesNotExist:
            return Response({"message": "User with this email not found."}, status=status.HTTP_400_BAD_REQUEST)

        confirmation_code = generate_confirmation_code()
        user.confirmation_code = confirmation_code
        user.save()

        send_confirmation_email(user, confirmation_code)

        return Response({"message": "The code has been sent."}, status=status.HTTP_200_OK)


class UserAuthentication(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        try:
            user = User.objects.get(username=username)
            if check_password(password, user.password):
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)

                return Response({
                    "message": "Authentication successful",
                    "tokens": {
                        "refresh": str(refresh),
                        "access": access_token,
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

class UserLogOut(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({"message": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
            except TokenError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

class ConfirmEmailAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        confirmation_code = request.data.get('confirmation_code')

        if not email or not confirmation_code:
            return Response({"message": "Email and confirmation code are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            # Ищем пользователя по email
            user = User.objects.get(email=email)

            if str(user.confirmation_code).strip() == str(confirmation_code).strip():
                user.email_confirmed = True
                user.confirmation_code = None
                user.save()
                return Response({"message": "Your email has been confirmed! You can now log in."},
                                status=status.HTTP_200_OK)
            else:
                return Response({"message": "Invalid confirmation code."}, status=status.HTTP_400_BAD_REQUEST)


        except User.DoesNotExist:
            return Response({"message": "User with this email not found."}, status=status.HTTP_400_BAD_REQUEST)

class CustomBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        if check_password(password, user.password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None