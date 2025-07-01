from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.product.models import Product as Item
from apps.chest.models import Chest
from apps.promotion.models import Promotion

from .scoreboard_client import send_chest_promo_purchase_event  # новый http клиент


class TransactionStatus(models.TextChoices):
    PENDING = "pending", "Ожидание"
    RESERVED = "reserved", "Баланс зарезервирован"
    DECLINED = "declined", "Отклонено"
    COMPLETED = "completed", "Завершено"
    FAILED = "failed", "Ошибка"


class Purchase(models.Model):
    """
    Покупка: сундука, предмета или акции.
    """
    owner = models.IntegerField()  # UID пользователя

    item = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL)
    chest = models.ForeignKey(Chest, null=True, blank=True, on_delete=models.SET_NULL)
    promotion = models.ForeignKey(Promotion, null=True, blank=True, on_delete=models.SET_NULL)

    quantity = models.PositiveIntegerField(default=1)  # кол-во купленных сундуков/предметов/акций

    transaction_status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING
    )

    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        if self.item:
            return f"Purchase #{self.id} by UID {self.owner}: item #{self.item_id}, qty {self.quantity}"
        elif self.chest:
            return f"Purchase #{self.id} by UID {self.owner}: chest #{self.chest_id}, qty {self.quantity}"
        elif self.promotion:
            return f"Purchase #{self.id} by UID {self.owner}: promotion #{self.promotion_id}, qty {self.quantity}"
        return f"Purchase #{self.id} by UID {self.owner}: unknown"

    def clean(self):
        filled = [self.item, self.chest, self.promotion]
        if sum(x is not None for x in filled) != 1:
            raise ValidationError("Ровно одно из полей item, chest или promotion должно быть заполнено.")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # При новой покупке сундука по акции отправляем событие в промо-сервис
        if is_new and self.chest and self.promotion:
            send_chest_promo_purchase_event(self.owner, self.quantity)