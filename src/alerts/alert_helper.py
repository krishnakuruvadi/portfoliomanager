from .models import Alert
import datetime
import enum
from dateutil.relativedelta import relativedelta

class Severity(enum.Enum):
    critical = 0
    error = 1
    warning = 2
    unknown = 3
    info = 4

def create_alert(summary, content, severity, alert_type, seen=False, action_url=None, json_data=None):
    print('creating alert')
    alert = Alert.objects.create(
        summary=summary,
        content=content,
        severity=severity.value,
        seen=seen,
        time=datetime.datetime.now(),
        action_url=action_url,
        alert_type=alert_type,
        json_data=json_data
    )
    # not hitting the save function model if using just create
    alert.seen=seen
    alert.save()
    return alert.id

def is_alert_raised(summary, start_time, end_time):
    #print(f'searching {summary} between {start_time} and {end_time}')
    for alert in Alert.objects.filter(time__gte=start_time, time__lte=end_time).order_by("-time"):
        #print(f'checking if {summary} is a substring in {alert.summary}')
        if summary in alert.summary:
            return True
    return False

def create_alert_today_if_not_exist(search_str, summary, content, severity, alert_type, start_time, end_time, seen=False, action_url=None, json_data=None):
    if not is_alert_raised(search_str, start_time, end_time):
        create_alert(summary, content, severity, alert_type, seen, action_url, json_data)
    else:
        print(f'alert already present {search_str}')

def create_alert_month_if_not_exist(search_str, summary, content, severity, alert_type, seen=False, action_url=None, json_data=None):
    end_time = datetime.datetime.now()
    start_time = end_time+relativedelta(months=-1) 
    if not is_alert_raised(search_str, start_time, end_time):
        create_alert(summary, content, severity, alert_type, seen, action_url, json_data)
    else:
        print(f'alert already present {search_str}')

def clean_alerts():
    today= datetime.date.today()
    Alert.objects.filter(alert_type='Notification', time__lte=today+relativedelta(days=-5)).delete()
    Alert.objects.filter(alert_type='Action', time__lte=today+relativedelta(months=-1)).delete()
    Alert.objects.filter(alert_type='Application', time__lte=today+relativedelta(days=-10)).delete()
    Alert.objects.filter(alert_type='Marketing', time__lte=today+relativedelta(days=-15)).delete()