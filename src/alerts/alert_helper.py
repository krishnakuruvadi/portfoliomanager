from .models import Alert
import datetime
import enum

class Severity(enum.Enum):
    critical = 0
    error = 1
    warning = 2
    unknown = 3
    info = 4

def create_alert(summary, content, severity, seen=False, action_url=None, json_data=None):
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

def is_alert_raised(summary, start_time, end_time):
    #print(f'searching {summary} between {start_time} and {end_time}')
    for alert in Alert.objects.filter(time__gte=start_time, time__lte=end_time):
        #print(f'checking if {summary} is a substring in {alert.summary}')
        if summary in alert.summary:
            return True
    return False

def create_alert_today_if_not_exist(search_str, summary, content, severity, start_time, end_time, seen=False, action_url=None, json_data=None):
    if not is_alert_raised(search_str, start_time, end_time):
        create_alert(summary, content, severity,seen, action_url, json_data)
