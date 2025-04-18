from django.db import models
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group, Permission
import random
import string
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager  # Add this import
from django.utils import timezone
from django.db.models import Sum, Avg, F, Q


class UserManager(models.Manager):
    def get_by_natural_key(self, email):
        return self.get(email=email)

    def create_user(self, username, email, password=None, phone=None, confirmation_code=None, **extra_fields):
        if confirmation_code is None:
            confirmation_code = ''.join(random.choices(string.digits, k=6))
        user = self.model(username=username, email=email, phone=phone, confirmation_code=confirmation_code,
                          **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, phone=None, confirmation_code=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)

        return self.create_user(username, email, password, phone, confirmation_code, **extra_fields)

class User(models.Model):
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)
    password = models.CharField(max_length=128)
    is_superuser = models.BooleanField(default=False)
    reset_code = models.CharField(max_length=6, blank=True, null=True)  # Ensure this field exists
    email_confirmed = models.BooleanField(default=False)
    confirmation_code = models.CharField(max_length=6, blank=True, null=True)  # Ensure this field exists
    objects = UserManager()

    def generate_confirmation_code(self):
        self.confirmation_code = ''.join(random.choices(string.digits, k=6))
        self.save()
    groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name='user_set',
        related_query_name='user'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name='user_set',
        related_query_name='user'
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'phone']

    class Meta:
        db_table = 'users'

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def save(self, *args, **kwargs):
        if not self.password.startswith(('pbkdf2_sha256$', 'bcrypt$', 'argon2')):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

    @property
    def is_anonymous(self):
        return False

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_staff(self):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return True

    def has_perm(self, perm, obj=None):
        return True

    def get_username(self):
        return self.username

    def check_password(self, raw_password):
        return make_password(raw_password) == self.password

class Currency(models.Model):
    name = models.CharField(max_length=10)
    rate_to_som = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # цена от юзера

    def __str__(self):
        return self.name

class UserCurrency(models.Model):
    user = models.ForeignKey(User, related_name='currencies', on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, related_name='user_rates', on_delete=models.CASCADE)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Значение по умолчанию
    event_date = models.DateField(null=True, blank=True, default=timezone.now)  # Разрешаем null и устанавливаем значение по умолчанию
    event_type = models.CharField(max_length=10, default='purchase')  # Значение по умолчанию
    purchase_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    purchase_count = models.IntegerField(null=True, blank=True)
    sale_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sale_count = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Вычисление покупки и продажи в зависимости от типа события
        if self.event_type == 'purchase':
            self.purchase_total = self.amount * self.rate
            self.purchase_count = self.amount
            self.sale_total = 0
            self.sale_count = 0
        elif self.event_type == 'sale':
            self.sale_total = self.amount * self.rate
            self.sale_count = self.amount
            self.purchase_total = 0
            self.purchase_count = 0
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'user_currencies'
        verbose_name = 'User Currency'
        verbose_name_plural = 'User Currencies'
        unique_together = ('user', 'currency')

class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    type = models.CharField(max_length=255)
    currency = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    time = models.TimeField(default=timezone.now)  # ⬅ автоматически текущее время
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total = self.amount * self.rate  # автоматический расчет total
        if not self.time:
            self.time = timezone.now().time()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.type} - {self.currency} ({self.date} {self.time})"

    class Meta:
        db_table = 'events'
        verbose_name = 'Event'
        verbose_name_plural = 'Events'
        ordering = ['-date']

class UserCurrencySummary:
    def __init__(self, user, currency_name):
        self.user = user
        self.currency_name = currency_name
        self._calculate_summary()

    def _calculate_summary(self):
        # Получаем все события, связанные с этим пользователем и валютой
        events = Event.objects.filter(currency=self.currency_name)

        # Покупки
        purchases = events.filter(type='purchase')
        self.purchase_total = purchases.aggregate(total=Sum(F('amount') * F('rate')))['total'] or 0
        self.purchase_count = purchases.aggregate(total=Sum('amount'))['total'] or 0
        self.purchase_average = self.purchase_total / self.purchase_count if self.purchase_count else 0

        # Продажи
        sales = events.filter(type='sale')
        self.sale_total = sales.aggregate(total=Sum(F('amount') * F('rate')))['total'] or 0
        self.sale_count = sales.aggregate(total=Sum('amount'))['total'] or 0
        self.sale_average = self.sale_total / self.sale_count if self.sale_count else 0

        # Профит
        self.profit = self.sale_total - self.purchase_total

    def as_dict(self):
        return {
            'currency': self.currency_name,
            'purchase_total': self.purchase_total,
            'purchase_count': self.purchase_count,
            'purchase_average': round(self.purchase_average, 2),
            'sale_total': self.sale_total,
            'sale_count': self.sale_count,
            'sale_average': round(self.sale_average, 2),
            'profit': round(self.profit, 2),
        }

