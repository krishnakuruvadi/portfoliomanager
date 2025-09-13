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

def update_tasks():
    available_tasks = {
        'get_mf_navs': {
            'description':'Get Mutual Fund latest NAV'
        },
        'update_mf': {
            'description':'Update Mutual Fund investment with latest value'
        },
        'update_espp': {
            'description':'Update ESPP investment with latest value'
        },
        'update_mf_schemes': {
            'description':'Check and update latest mutual schemes from fund houses from AMFII'
        },
        'update_bse_star_schemes': {
            'description':'Check and update latest mutual schemes from fund houses from BSE STaR' 
        },
        'update_investment_data':{
            'description':'Update investment data for home view chart'
        },
        'update_mf_mapping': {
            'description': 'Update any missing mapping info between AMFII, BSE STaR and KUVERA'
        },
        'update_goal_contrib': {
            'description': 'Update different investment data for each goal'
        },
        'analyse_mf': {
            'description': 'Analyse different Mutual Funds where users have active investment'
        },
        'update_shares_latest_vals': {
            'description': 'Reconcile and get latest vals of shares'
        },
        'mf_update_blend': {
            'description': 'Update latest blend of Mutual Funds'
        },
        'pull_mf_transactions': {
            'description': 'Pulls mutual fund transactions from supported broker if passwords are stored'
        },
        'update_latest_vals_epf_ssy_ppf': {
            'description': 'Update latest values in PPF, EPF, SSY'
        },
        'update_rsu': {
            'description':'Update RSU investment with latest value'
        },
        'pull_corporate_actions_shares': {
            'description':'Pull corporate actions of shares'
        },
        'initial_setup': {
            'description':'Pull information needed for initial setup'
        },
        'fetch_data': {
            'description':'Pull all information needed from external sources'
        },
        'update_all_investments': {
            'description':'Update all investments with data fetched from external sources'
        },
        'pull_store_and_update_gold_vals': {
            'description':'pull, store and update gold vals for everyone'
        },
    }
    new_tasks = 0
    existing = 0
    for task in available_tasks.keys():
        found = False
        for task_obj in Task.objects.all():
            if task_obj.task_name == task:
                found = True
                existing += 1
                break
        if not found:
            Task.objects.create(
                task_name = task,
                description = available_tasks[task]['description']
            )
            new_tasks += 1
    print(f"INFO: Created {new_tasks} tasks on startup. {existing} tasks already exist.")
