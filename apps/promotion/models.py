from django.db import models


# Create your models here.
class Promotion(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField()
    products = models.ManyToManyField("Item", blank=True)
    chests = models.ManyToManyField("Chest", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        end_time = self.start_time + self.duration
        total_products = self.products.count()
        total_chests = self.chests.count()
        
        return (
            f"{self.name} | {self.start_time.date()} → {end_time.date()} | "
            f"Price: {self.price} | Items: {total_products} | Chests: {total_chests}"
        )
        
    
