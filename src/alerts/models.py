from django.db import models
from django.urls import reverse
from django.core.validators import MaxValueValidator, MinValueValidator 
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

ALERT_TYPE_CHOICES = [
    ('Application', 'Application'),
    ('Action', 'Action'),
    ('Notification', 'Notification'),
    ('Marketing', 'Marketing')
]

# Create your models here.
class Alert(models.Model):
    seen = models.BooleanField(default=False)
    json_data = models.CharField(max_length=1000, null=True, blank=True)
    action_url = models.CharField(max_length=500, null=True, blank=True)
    time = models.DateTimeField(null=False)
    content = models.CharField(max_length=500, null=True)
    summary = models.CharField(max_length=100, null=False)
    severity = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(4)],default=4)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES, default='Notification')

    def get_absolute_url(self):
        return reverse("alerts:alert-detail", kwargs={'id': self.id})
    
    def save(self, *args, **kw):
        super(Alert, self).save(*args, **kw)
        print('Change in alerts table detected')
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "gossip", {
                "type": "alert.gossip",
                "event": "Alert Change",
                "count": len(Alert.objects.filter(seen=False))
            }
        )
