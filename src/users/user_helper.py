from shared.handle_chart_data import get_user_contributions
from .models import User, AssetClassDistribution
import datetime
from django.utils import timezone


def update_user_networth(user_id):
    if user_id:
        try:
            u = User.objects.get(id=user_id)
            c = get_user_contributions(u.id)
            u.total_networth = c['total']
            u.as_on = datetime.datetime.now()
            u.save()
        except User.DoesNotExist:
            print(f'no user with id {user_id}')
    else:
        for u in User.objects.all():
            c = get_user_contributions(u.id)
            u.total_networth = c['total']
            u.as_on = datetime.datetime.now()
            u.save()

def get_or_create_asset_allocation_for_user(user_obj):
    try:
        aobj = AssetClassDistribution.objects.get(user=user_obj)
    except AssetClassDistribution.DoesNotExist:
        aobj = AssetClassDistribution.objects.create(
                user=user_obj,
                as_on_date=datetime.datetime.now(),
            )
    return aobj

def get_asset_allocation_details_for_user(user_obj):
    data = dict()
    try:
        aobj = get_or_create_asset_allocation_for_user(user_obj)
        data['suggested_equity_percentage'] = aobj.suggested_equity_percentage
        data['preferred_equity_percentage'] = aobj.preferred_equity_percentage
        data['current_equity_percentage'] = aobj.current_equity_percentage
        data['suggested_debt_percentage'] = aobj.suggested_debt_percentage
        data['preferred_debt_percentage'] = aobj.preferred_debt_percentage
        data['current_debt_percentage'] = aobj.current_debt_percentage
        data['suggested_gold_percentage'] = aobj.suggested_gold_percentage
        data['preferred_gold_percentage'] = aobj.preferred_gold_percentage
        data['current_gold_percentage'] = aobj.current_gold_percentage
        data['suggested_crypto_percentage'] = aobj.suggested_crypto_percentage
        data['preferred_crypto_percentage'] = aobj.preferred_crypto_percentage
        data['current_crypto_percentage'] = aobj.current_crypto_percentage
        data['suggested_cash_percentage'] = aobj.suggested_cash_percentage
        data['preferred_cash_percentage'] = aobj.preferred_cash_percentage
        data['current_cash_percentage'] = aobj.current_cash_percentage
        data['as_on'] = aobj.as_on_date
    except Exception as ex:
        print(f"ERROR: Exception {ex} when getting asset allocation details for user with id {user_obj.id}.")
    return data

def update_current_asset_allocation_for_user(user_id):
    if not user_id:
        users = User.objects.all()
    else:
        try:
            users = [User.objects.get(id=user_id)]
        except User.DoesNotExist:
            print(f"WARNING: No user with id {user_id}")
    for user_obj in users:
        try:
            aobj = get_or_create_asset_allocation_for_user(user_obj)
            contrib = get_user_contributions(user_obj.id)
            total = contrib['total']
            aobj.as_on_date = timezone.now()
            if total > 0:
                aobj.current_equity_percentage = round(contrib['equity']*100/total,2)
                aobj.current_debt_percentage = round(contrib['debt']*100/total,2)
                aobj.current_gold_percentage = round(contrib['Gold']*100/total,2)
                aobj.current_crypto_percentage = round(contrib['Crypto']*100/total,2)
                aobj.current_cash_percentage = round(contrib['Cash']*100/total,2)
            else:
                aobj.current_equity_percentage = 0
                aobj.current_debt_percentage = 0
                aobj.current_gold_percentage = 0
                aobj.current_crypto_percentage = 0
                aobj.current_cash_percentage = 0
            aobj.save()
        except Exception as ex:
            print(f"ERROR: Exception {ex} when setting current asset allocation for user with id {user_obj.id}.")

def update_suggested_asset_allocation_for_user(user_id):
    if not user_id:
        users = User.objects.all()
    else:
        try:
            users = [User.objects.get(id=user_id)]
        except User.DoesNotExist:
            print(f"WARNING: No user with id {user_id}")
    for user_obj in users:
        if not user_obj.dob:
            continue
        risk_profile = user_obj.risk_profile
        age = (datetime.date.today() - user_obj.dob).days // 365
        # Base allocation based on the "Rule of 100" for a moderate profile
        base_equity = max(100 - age, 10)
        
        # Adjustments based on risk profile
        if risk_profile == 'aggressive':
            # Increase equity, decrease debt/cash/gold
            equity_percentage = min(base_equity + 15, 95)
            remaining_percentage = 100 - equity_percentage
            debt_percentage = remaining_percentage * 0.60
            gold_percentage = remaining_percentage * 0.15
            crypto_percentage = remaining_percentage * 0.15
            cash_percentage = remaining_percentage * 0.10
        elif risk_profile == 'conservative':
            # Decrease equity, increase debt/cash/gold
            equity_percentage = max(base_equity - 15, 5)
            remaining_percentage = 100 - equity_percentage
            debt_percentage = remaining_percentage * 0.80
            gold_percentage = remaining_percentage * 0.10
            crypto_percentage = 0
            cash_percentage = remaining_percentage * 0.10
        else:
            # Use the base allocation
            equity_percentage = base_equity
            remaining_percentage = 100 - equity_percentage
            debt_percentage = remaining_percentage * 0.70
            gold_percentage = remaining_percentage * 0.15
            crypto_percentage = remaining_percentage * 0.05
            cash_percentage = remaining_percentage * 0.10


        # Ensure allocations sum to 100% due to floating point arithmetic
        total = sum([equity_percentage, debt_percentage, gold_percentage, crypto_percentage, cash_percentage])
        if total != 100:
            diff = 100 - total
            # Adjust debt to make it 100%
            debt_percentage += diff

        equity_perc = round(equity_percentage, 2)
        debt_perc = round(debt_percentage, 2)
        gold_perc = round(gold_percentage, 2)
        crypto_perc = round(crypto_percentage, 2)
        cash_perc = round(cash_percentage, 2)
        try:
            aobj = get_or_create_asset_allocation_for_user(user_obj)
            aobj.suggested_equity_percentage = equity_perc
            aobj.suggested_debt_percentage = debt_perc
            aobj.suggested_gold_percentage = gold_perc
            aobj.suggested_crypto_percentage = crypto_perc
            aobj.suggested_cash_percentage = cash_perc
            aobj.save()
        except User.DoesNotExist:
            print(f"WARNING: No user with id {user_id}")
        except Exception as ex:
            print(f"ERROR: Exception {ex} when setting suggested asset allocation for user with id {user_id}.")
        