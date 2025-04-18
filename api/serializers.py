from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Event, Currency, User, UserCurrency
from django.utils import timezone

from rest_framework import serializers

class UserCurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCurrency
        fields = ['user', 'currency', 'rate', 'amount', 'event_date', 'event_type',
                  'purchase_total', 'purchase_count', 'sale_total', 'sale_count']

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']  # Include 'phone' field
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):

        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ['total']  # total будет вычисляться автоматически

    def create(self, validated_data):
        amount = validated_data.get('amount')
        rate = validated_data.get('rate')
        validated_data['total'] = amount * rate

        # если время не передано — берем текущее
        if not validated_data.get('time'):
            validated_data['time'] = timezone.now().time()

        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Обновляем amount/rate => пересчитываем total
        instance.type = validated_data.get('type', instance.type)
        instance.currency = validated_data.get('currency', instance.currency)
        instance.amount = validated_data.get('amount', instance.amount)
        instance.date = validated_data.get('date', instance.date)
        instance.time = validated_data.get('time', instance.time)
        instance.rate = validated_data.get('rate', instance.rate)
        instance.total = instance.amount * instance.rate
        instance.save()
        return instance

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ['id', 'name', 'rate_to_som']

    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class CustomTokenObtainPairSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        try:
            user = User.objects.get(username=username)
            if check_password(password, user.password):
                refresh = RefreshToken()
                
                # Add custom claims
                refresh['user_id'] = user.id
                refresh['username'] = user.username
                refresh['email'] = user.email
                refresh['is_superuser'] = user.is_superuser

                return {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            else:
                raise serializers.ValidationError('Неверный пароль')
        except User.DoesNotExist:
            print('Пользователь не найден')
            raise serializers.ValidationError('Пользователь не найден')