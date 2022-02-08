from .models import Task, TaskState
import datetime
from ppf.ppf_helper import insert_ppf_trans_entry
from shared.utils import get_date_or_none_from_string
from ppf.models import PpfEntry
from ssy.models import SsyEntry
from ssy.ssy_helper import insert_ssy_trans_entry


def is_task_run_today(task_name):
    task_found = False
    for task in Task.objects.all():
        if task.task_name == task_name:
            task_found = True
            if task.last_run and task.last_run.date() == datetime.date.today() and task.current_state == TaskState.Unknown.value and task.last_run_status == TaskState.Successful.value:
                print(f'task was last run on {task.last_run.date() } with status {task.last_run_status}')
                return True
            else:
                if not task.last_run:
                    print(f'task {task_name} was never run')
                else:
                    print(f'task {task_name} was last run on {task.last_run.date()} and status was {Task.TASK_STATE_CHOICES[task.last_run_status][1]}')
    if not task_found:
        print(f'task {task_name} not found')
    return False

def add_transactions_sbi_ppf(ppf_acc_num, transactions):
    for trans in transactions:
        date_obj = get_date_or_none_from_string(trans['date'], '%d-%b-%Y')
        if trans['debit'] > 0:
            entry = PpfEntry.DEBIT
            amount = trans['debit']
        else:
            entry = PpfEntry.CREDIT
            amount = trans['credit']
        if 'CREDIT INTEREST' in trans['description']:
            interest_comp = True
        else:
            interest_comp = False
        insert_ppf_trans_entry(ppf_acc_num, date_obj, entry, amount,trans['description'], '', interest_comp)

def add_transactions_sbi_ssy(ssy_acc_num, transactions):
    for trans in transactions:
        date_obj = get_date_or_none_from_string(trans['date'], '%d-%b-%Y')
        if trans['debit'] > 0:
            entry = SsyEntry.DEBIT
            amount = trans['debit']
        else:
            entry = SsyEntry.CREDIT
            amount = trans['credit']
        if 'CREDIT INTEREST' in trans['description']:
            interest_comp = True
        else:
            interest_comp = False
        insert_ssy_trans_entry(ssy_acc_num, date_obj, entry, amount,trans['description'], '', interest_comp)
