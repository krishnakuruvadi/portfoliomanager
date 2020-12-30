from .models import Alert
import datetime
import enum

class Severity(enum.Enum):
    critical = 0
    error = 1
    warning = 2
    unknown = 3
    info = 4

def create_alert(summary, content, severity,seen=False, action_url=None, json_data=None):
    print('creating alert')
    alert = Alert.objects.create(
        summary=summary,
        content=content,
        severity=severity.value,
        seen=seen,
        time=datetime.datetime.now(),
        action_url=action_url,
        json_data=json_data
    )
    # not hitting the save function model if using just create
    alert.seen=seen
    alert.save()
    return alert.id