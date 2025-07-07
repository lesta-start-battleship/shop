from django.db import models
import django.utils.timezone as timezone

# Create your models here.
class Promotion(models.Model):
	name = models.CharField(max_length=255)
	description = models.TextField(null=True, blank=True)
	start_date = models.DateTimeField(default=timezone.now)
	duration = models.DurationField()
	manually_disabled = models.BooleanField(default=False)
	compensation_done = models.BooleanField(default=False)

	@property 
	def end_date(self):
		return self.start_date + self.duration

	def is_active(self):
		now = timezone.now()
		return self.start_date <= now <= self.end_date and not self.manually_disabled

	def __str__(self):
			return f"{self.name} (Active: {self.is_active()})"
		
	def has_ended(self):
		return timezone.now() > self.end_date
