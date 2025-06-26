from django.db import models

class Purchase(models.Model):
    """
    Покупка: сундука, предмета или акции.
    """
    owner = models.IntegerField()  # UID пользователя
    item = models.ForeignKey('apps.product.Item', null=True, blank=True, on_delete=models.SET_NULL)
    chest = models.ForeignKey('apps.chest.Chest', null=True, blank=True, on_delete=models.SET_NULL)
    promotion = models.ForeignKey('apps.promotion.Promotion', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        target = self.item or self.chest or self.promotion
        return f"{self.owner} bought {target} at {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
