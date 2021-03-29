from django.db import models
from django.urls import reverse

import enum
# Create your models here.

class TaskState(enum.Enum):
    Unknown = 0
    Scheduled = 1
    Running = 2
    Failed = 3
    Successful = 4

class Task(models.Model):
    TASK_STATE_CHOICES = [
        (0, 'Unknown'),
        (1, 'Scheduled'),
        (2, 'Running'),
        (3, 'Failed'),
        (4, 'Successful')
    ]
    description = models.CharField(max_length=600)
    last_run = models.DateTimeField(null=True, blank=True)
    last_run_status = models.IntegerField(choices=TASK_STATE_CHOICES, default=0)
    notes = models.TextField(blank=True, null=True, max_length=600)
    task_name = models.CharField(max_length=60)
    current_state = models.IntegerField(choices=TASK_STATE_CHOICES, default=0)

    def get_absolute_url(self):
        return reverse("tasks:task-detail", kwargs={'id': self.id})
    
    def __str__(self):
        return str(self.id) + ': ' + self.task_name + ' Last Run:' + str(self.last_run) + ' Last Run Status:' + self.TASK_STATE_CHOICES[self.last_run_status][1]