from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import (
    ListView,
    DetailView,
    DeleteView
)
from django.template import Context
from django.http import HttpResponseRedirect
from decimal import Decimal
from .models import Goal
from .goal_helper import one_time_pay_final_val, add_goal_entry, get_corpus_to_be_saved, get_depletion_vals, get_unallocated_amount
from dateutil.relativedelta import relativedelta
from ppf.models import Ppf, PpfEntry

from rest_framework.views import APIView
from rest_framework.response import Response
import json
from shared.handle_delete import delete_goal
from shared.handle_get import *
from shared.handle_chart_data import get_goal_contributions, get_goal_yearly_contrib
from shared.financial import *
import colorsys
from shared.utils import get_int_or_none_from_string

from bankaccounts.bank_account_interface import BankAccountInterface
from crypto.crypto_interface import CryptoInterface
from users.user_interface import get_ext_user, get_users
from django.conf import settings

# Create your views here.

def goal_list(request):
    template = 'goals/goal_list.html'
    queryset = Goal.objects.all()
    data = dict()
    data['user_name_mapping'] = get_all_users()
    data['total_goals'] = len(queryset)
    data['target'] = 0
    data['achieved'] = 0
    data['object_list'] = list()
    for g in queryset:
        data['target'] += g.final_val
        data['achieved'] += g.achieved_amt
        data['object_list'].append(
            {
                'name': g.name,
                'start_date':g.start_date,
                'end_date':g.start_date+relativedelta(months=g.time_period),
                'time_period':g.time_period,
                'final_val':g.final_val,
                'achieved_amt':g.achieved_amt,
                'achieved_percent':g.achieved_percent,
                'user':g.user,
                'notes':g.notes,
                'id':g.id
            }
        )
    if data['target'] > 0:
        data['ach_per'] = round(data['achieved']*100/data['target'],2)
    else:
        data['ach_per'] = 0
    data['unalloc'] = get_unallocated_amount()
    data['curr_module_id'] = 'id_goal_module'
    print(data)
    return render(request, template, context=data)

def goals_insight(request):
    template = "goals/goals_insight.html"
    context = dict()
    goal_objs = Goal.objects.all()
    target_val = 0
    remaining_val = 0
    yrly_invest_12 = dict()
    yrly_invest_8 = dict()
    target_dates_and_amts= list()
    today = datetime.date.today()
    exp_growth = 8
    if request.method == 'POST':
        exp_growth = get_int_or_none_from_string(request.POST.get('exp_ret'))
        if not exp_growth or exp_growth <= 0:
            exp_growth = 8
    
    for goal_obj in goal_objs:
        target = float(goal_obj.final_val)
        if target < 1:
            target = 1
        target_val += target
        remaining = target - float(goal_obj.achieved_amt)
        if remaining < 0:
            remaining = 0
        remaining_val += remaining
        target_date = goal_obj.start_date+relativedelta(months=goal_obj.time_period)
        months_to_goal = relativedelta(target_date, today)
        mtg = months_to_goal.months + months_to_goal.years*12
        projected = get_fd_final_val(float(goal_obj.achieved_amt), 'fd_compound_yearly', mtg, exp_growth)

        target_dates_and_amts.append({'id':goal_obj.id, 'user':goal_obj.user, 'name':goal_obj.name, 'date':target_date, 'achieved':int(goal_obj.achieved_amt), 'target':int(remaining-projected+float(goal_obj.achieved_amt)), 'id':goal_obj.id, 'remaining':int(remaining), 'projected':int(projected)})
        '''
        yrly_investment_reqd_12 = int(get_required_yrly_investment(float(goal_obj.achieved_amt), 12, target_date, target))
        yrly_investment_reqd_8 = int(get_required_yrly_investment(float(goal_obj.achieved_amt), 8, target_date, target))

        for yr in range(today.year, target_date.year):
            if not yr in yrly_invest_12:
                yrly_invest_12[yr] = 0
            if not yr in yrly_invest_8:
                yrly_invest_8[yr] = 0
            yrly_invest_12[yr] += yrly_investment_reqd_12
            yrly_invest_8[yr] += yrly_investment_reqd_8
        '''
    context['remaining_per'] = round(remaining_val*100/target_val, 2)
    context['achieve_per'] = round(100 - context['remaining_per'], 2)
    context['target'] = target_val
    context['remaining'] = remaining_val
    context['achieved'] = target_val - remaining_val
    #context['yrly_invest_12'] = yrly_invest_12
    #context['yrly_invest_8'] = yrly_invest_8
    context['exp_ret'] = exp_growth

    for i in range(0,len(target_dates_and_amts)):
        if i != len(target_dates_and_amts)-1:
            for j in range(i, len(target_dates_and_amts)):
                if target_dates_and_amts[i]['date'] > target_dates_and_amts[j]['date']:
                    temp = target_dates_and_amts[j]
                    target_dates_and_amts[j] = target_dates_and_amts[i]
                    target_dates_and_amts[i] = temp
    print(f'sorted {target_dates_and_amts}')
    goal_yrly_inv, goal_monthly_inv, yrly_total = alternate_investment_strategy(target_dates_and_amts, exp_growth)

    last_date = target_dates_and_amts[len(target_dates_and_amts)-1]['date']
    j = 0 
    cash_flows = list()
    cash_flows.append((today, -1*context['achieved']))
    for yr, amt in yrly_total.items():
        if yr == today.year:
            for m in range(today.month, 13):
                cash_flows.append((datetime.date(year=yr, month=m, day=1), -1*int(amt/(13-today.month))))
                for k in range (j, len(target_dates_and_amts)):
                    if target_dates_and_amts[k]['date'].year == yr and target_dates_and_amts[k]['date'].month == m:
                        g = Goal.objects.get(id=target_dates_and_amts[k]['id'])
                        cash_flows.append((target_dates_and_amts[k]['date'], float(g.final_val)))
                        j += 1
        elif yr == last_date.year:
            for m in range(1, last_date.month+1):
                cash_flows.append((datetime.date(year=yr, month=m, day=1), -1*int(amt/last_date.month)))
                for k in range (j, len(target_dates_and_amts)):
                    if target_dates_and_amts[k]['date'].year == yr and target_dates_and_amts[k]['date'].month == m:
                        g = Goal.objects.get(id=target_dates_and_amts[k]['id'])
                        cash_flows.append((target_dates_and_amts[k]['date'], float(g.final_val)))
                        j += 1
        else:
            for m in range(1, 13):
                cash_flows.append((datetime.date(year=yr, month=m, day=1), -1*int(amt/12)))
                for k in range (j, len(target_dates_and_amts)):
                    if target_dates_and_amts[k]['date'].year == yr and target_dates_and_amts[k]['date'].month == m:
                        g = Goal.objects.get(id=target_dates_and_amts[k]['id'])
                        cash_flows.append((target_dates_and_amts[k]['date'], float(g.final_val)))
                        j += 1

    colors = get_N_HexCol(len(goal_objs)+2)
    print(f'****** Getting fv for total ***********')
    print(f'cash_flows: {cash_flows}')
    fv, fvs = get_fv_from_cashflows(cash_flows=cash_flows, roi=exp_growth)
    print(f'****** Done fv for total ***********')

    table_goal_yrly_inv = '<thead><tr><th>Investment Required</th><th>Total</th>'
    for goal_obj in goal_objs:
        table_goal_yrly_inv += '<th>' + get_user_short_name_or_name_from_id(goal_obj.user) + '/' + goal_obj.name 
        #target_dates_and_amts.append({'id':goal_obj.id, 'user':goal_obj.user, 'name':goal_obj.name, 'date':target_date, 'achieved':int(goal_obj.achieved_amt), 'target':int(remaining-projected), 'id':goal_obj.id, 'remaining':int(remaining), 'projected':int(projected)})
        for t in target_dates_and_amts:
            if t['id'] == goal_obj.id:
                tip = f"Achieved {t['achieved']}. Projected to grow to {t['projected']} at {exp_growth}%. Target {goal_obj.final_val}"
                break
        table_goal_yrly_inv += f' <i class="far fa-question-circle" data-toggle="tooltip" style="font-size:0.8em;" data-placement="top" title="{tip}"></i></th>'
    table_goal_yrly_inv += '</tr></thead><tbody>' 
    for yr in range(today.year, last_date.year+1):
        yr_total = 0
        table_goal_yrly_inv += '<tr><th>' + str(yr) + '</th>'
        yr_ind = ''
        for goal_obj in goal_objs:
            if yr in goal_yrly_inv[goal_obj.id]:
                yr_ind += '<td>' + str(goal_yrly_inv[goal_obj.id][yr]) + '</td>'
                yr_total += goal_yrly_inv[goal_obj.id][yr]
            else:
                yr_ind += '<td>0</td>'
        table_goal_yrly_inv += '<td>' + str(round(yr_total,2)) + '</td>' + yr_ind
        table_goal_yrly_inv += '</tr>'
    context['table_goal_yrly_inv'] = table_goal_yrly_inv+'</tbody>'

    #print(f'fv: {fv}')
    #print(f'fvs: {fvs}')
    context['chart_data'] = list()
    context['chart_data'].append({'label':'Total', 'data':fvs, 'borderColor':colors[0], 'fill':'false'})
    i = 1
    for g in goal_objs:
        print(f'************ Getting chart fv data for {g.name}**************')
        cash_flows = list()
        if float(g.achieved_amt) > 0:
            print(f'achieved amount for goal {g.name}: {g.achieved_amt}')
            cash_flows.append((today, -1*float(g.achieved_amt)))
        else:
            print(f'no achieved amount for goal {g.name}')
        cash_flows.extend(goal_monthly_inv[g.id])
        cash_flows.append((g.start_date+relativedelta(months=g.time_period), float(g.final_val)))
        #if g.id == 2:
        #    print(f'cash_flows {cash_flows}')
        fv, fvs = get_fv_from_cashflows(cash_flows=cash_flows, roi=exp_growth, debug=g.id==2)
        #if g.id == 2:
        #    print(f'goal2 fvs {fvs}')
        context['chart_data'].append({'label':g.name, 'data':fvs, 'borderColor':colors[i], 'fill':'false'})
        i += 1
    context['curr_module_id'] = 'id_goal_module'
    print(context)
    return render(request, template, context)

def get_N_HexCol(N=5):
    HSV_tuples = [(x * 1.0 / N, 0.5, 0.5) for x in range(N)]
    hex_out = []
    for rgb in HSV_tuples:
        rgb = map(lambda x: int(x * 255), colorsys.hsv_to_rgb(*rgb))
        hex_out.append('#%02x%02x%02x' % tuple(rgb))
    return hex_out

def goal_monthly_data(start_date, end_date, monthly_amt):
    ret = list()
    while start_date <= end_date:
        ret.append((start_date, -1*float(monthly_amt)))
        start_date = start_date+relativedelta(months=1)
    return ret

def alternate_investment_strategy(target_dates_and_amts, roi):
    print('*************************************************************************************')
    print(target_dates_and_amts)
    total_target = 0
    today = datetime.date.today()
    #print(f'before sorting: {sorted_dates}')

    last_date = target_dates_and_amts[len(target_dates_and_amts)-1]['date']
    print(f'by {last_date} we should have reached {total_target}')
    goal_yrly_inv = dict()
    goal_monthly_inv = dict()
    max_yrs_investment = 0
    for i in range(len(target_dates_and_amts)):
        curr_goal = target_dates_and_amts[i]
        last_goal = target_dates_and_amts[i-1]
        goal_yrly_inv[curr_goal['id']] = dict()
        goal_monthly_inv[curr_goal['id']] = dict()
        print(f'Goal {curr_goal}')
        yrly_investment_reqd = 0
        start_yr = 0
        end_yr = 0

        months_to_goal = relativedelta(curr_goal['date'], today)
        months_to_goal = months_to_goal.months + 12*months_to_goal.years if months_to_goal.years > 0 else 0

        if months_to_goal < 12:
            yrly_investment_reqd = int(get_required_yrly_investment(0, roi, curr_goal['date'], curr_goal['target']))
            monthly = round(yrly_investment_reqd/12, 2)
            curr_yr_months = 12 - today.month
            goal_yrly_inv[curr_goal['id']][today.year] = round(goal_yrly_inv[curr_goal['id']].get(today.year, 0) + curr_yr_months * monthly, 2)
            if curr_goal['date'].year != today.year:
                goal_yrly_inv[curr_goal['id']][curr_goal['date'].year] = round(goal_yrly_inv[curr_goal['id']].get(curr_goal['date'].year, 0) + (curr_goal['date'].month+1)*monthly, 2)
            goal_monthly_inv[curr_goal['id']] = goal_monthly_data(today, curr_goal['date'], monthly)
        elif i == 0:
            yrly_investment_reqd = int(get_required_yrly_investment(0,roi, curr_goal['date'], curr_goal['target']))
            monthly = round(yrly_investment_reqd/12, 2)
            for yr in range(today.year, curr_goal['date'].year+1):
                months = 12
                if yr == today.year:
                    months = 12 - today.month
                elif yr == curr_goal['date'].year:
                    months = curr_goal['date'].month+1
                goal_yrly_inv[curr_goal['id']][yr] = round(goal_yrly_inv[curr_goal['id']].get(yr, 0) + months*monthly, 2)
            goal_monthly_inv[curr_goal['id']] = goal_monthly_data(today, curr_goal['date'], monthly)
        else:
            diff = relativedelta(curr_goal['date'], last_goal['date'])
            print(f"diff between {last_goal['date']} and {curr_goal['date']} is {diff}")
            if diff.years > 0:
                print('have more than a year for next goal')
                m = diff.months + 1 + diff.years*12
                yrly_investment_reqd = int(get_required_yrly_investment(0,roi, today+relativedelta(months=m), curr_goal['target']))
                if yrly_investment_reqd > max_yrs_investment:
                    print(f' {yrly_investment_reqd} > highest yearly investment of  {max_yrs_investment}')
                    temp1 = rd_calc_final_val(max_yrs_investment/12, m, roi, None)
                    temp2 = curr_goal['target'] - temp1
                    print(f'temp1 {temp1} temp2 {temp2}')
                    add_each_year = get_required_yrly_investment(0,roi, curr_goal["date"], temp2)
                    print(f'Add {max_yrs_investment} to each year from {last_goal["date"].year} to {curr_goal["date"].year+1}.')
                    print(f'Add additional {add_each_year} to each year from {today.year} to {curr_goal["date"].year} to reach goal')
                    monthly1 = round(add_each_year/12, 2)
                    for j in range(today.year, curr_goal["date"].year+1):
                        months = 12
                        if j == today.year:
                            months = 12 - today.month
                        elif j == curr_goal['date'].year:
                            months = curr_goal['date'].month+1
                        goal_yrly_inv[curr_goal['id']][j] = round(goal_yrly_inv[curr_goal['id']].get(j, 0) + months*monthly1, 2)
                    
                    goal_monthly_inv[curr_goal['id']] = goal_monthly_data(today, last_goal["date"], monthly1)

                    monthly2 = round(max_yrs_investment/12, 2)
                    for j in range(last_goal['date'].year, curr_goal["date"].year+1):
                        months = 12
                        if j == today.year:
                            months = 12 - today.month
                        elif j == curr_goal['date'].year:
                            months = curr_goal['date'].month+1
                        goal_yrly_inv[curr_goal['id']][j] = round(goal_yrly_inv[curr_goal['id']].get(j, 0) + months*monthly2, 2)
                    goal_monthly_inv[curr_goal['id']].extend(goal_monthly_data(last_goal["date"], curr_goal["date"], monthly1+monthly2))
                else:
                    print(f'{yrly_investment_reqd} < highest yearly investment of {max_yrs_investment}')
                    start_yr = last_goal["date"].year
                    end_yr = curr_goal["date"].year
                    monthly = round(yrly_investment_reqd/12, 2)
                    for j in range(start_yr, end_yr+1):
                        months = 12
                        if j == today.year:
                            months = 12 - today.month
                        elif j == curr_goal['date'].year:
                            months = curr_goal['date'].month+1
                        goal_yrly_inv[curr_goal['id']][j] = round(goal_yrly_inv[curr_goal['id']].get(j, 0) + months*monthly, 2)
                    goal_monthly_inv[curr_goal['id']] = goal_monthly_data(last_goal["date"], curr_goal['date'], monthly)
            else:
                print('have less than a year for next goal')
                yrly_investment_reqd = int(get_required_yrly_investment(0,roi, curr_goal["date"], curr_goal["target"]))
                monthly = round(yrly_investment_reqd/12, 2)
                for yr in range(today.year, curr_goal['date'].year+1):
                    months = 12
                    if yr == today.year:
                        months = 12 - today.month
                    elif yr == curr_goal['date'].year:
                        months = curr_goal['date'].month+1
                    goal_yrly_inv[curr_goal['id']][yr] = round(goal_yrly_inv[curr_goal['id']].get(yr, 0) + months*monthly, 2)
                goal_monthly_inv[curr_goal['id']] = goal_monthly_data(today, curr_goal['date'], monthly)

        yrly_total = dict()
        for _,v in goal_yrly_inv.items():
            for yr,amt in v.items():
                yrly_total[yr] = yrly_total.get(yr, 0) + amt
        max_yr = None
        for yr,v in yrly_total.items():
            if v > max_yrs_investment:
                max_yrs_investment = v
                max_yr = yr
        print(f"Goal {curr_goal['id']} {goal_yrly_inv[curr_goal['id']]}")
        print(f'after {i} goals max_yrs_investment: {max_yrs_investment} for year {max_yr}')

    for k,v in goal_yrly_inv.items():
        print(f'Goal {k}, {v}')
    yrly_total = dict()
    for _,v in goal_yrly_inv.items():
        for yr,amt in v.items():
            yrly_total[yr] = yrly_total.get(yr, 0) + amt
    total = 0
    for yr,v in yrly_total.items():
        print(f'{yr}: {v}')
        total += v
    print(f'total: {total}')
    return goal_yrly_inv, goal_monthly_inv, yrly_total

class GoalDetailView(DetailView):
    template_name = 'goals/goal_detail.html'
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Goal, id=id_)
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        print(data['object'])
        data['distribution'] = {'labels':list(), 'vals':list(), 'colors':list()}
        has_data = False
        if data['object'].epf_conitrib > 0:
            data['distribution']['labels'].append('EPF')
            data['distribution']['vals'].append(float(data['object'].epf_conitrib))
            data['distribution']['colors'].append("#f15664")
            has_data = True
        if data['object'].espp_conitrib > 0:
            data['distribution']['labels'].append('ESPP')
            data['distribution']['vals'].append(float(data['object'].espp_conitrib))
            data['distribution']['colors'].append("#DC7633")
            has_data = True
        if data['object'].fd_conitrib > 0:
            data['distribution']['labels'].append('FD')
            data['distribution']['vals'].append(float(data['object'].fd_conitrib))
            data['distribution']['colors'].append("#006f75")
            has_data = True
        if data['object'].ppf_conitrib > 0:
            data['distribution']['labels'].append('PPF')
            data['distribution']['vals'].append(float(data['object'].ppf_conitrib))
            data['distribution']['colors'].append("#92993c")
            has_data = True
        if data['object'].ssy_conitrib > 0:
            data['distribution']['labels'].append('SSY')
            data['distribution']['vals'].append(float(data['object'].ssy_conitrib))
            data['distribution']['colors'].append("#f9c5c6")
            has_data = True
        if data['object'].rsu_conitrib > 0:
            data['distribution']['labels'].append('RSU')
            data['distribution']['vals'].append(float(data['object'].rsu_conitrib))
            data['distribution']['colors'].append("#AA12E8")
            has_data = True
        if data['object'].mf_conitrib > 0:
            data['distribution']['labels'].append('MutualFunds')
            data['distribution']['vals'].append(float(data['object'].mf_conitrib))
            data['distribution']['colors'].append("#bfff00")
            has_data = True
        if data['object'].shares_conitrib > 0:
            data['distribution']['labels'].append('Shares')
            data['distribution']['vals'].append(float(data['object'].shares_conitrib))
            data['distribution']['colors'].append("#e31219")
            has_data = True
        if data['object'].r_401k_contribution > 0:
            data['distribution']['labels'].append('401K')
            data['distribution']['vals'].append(float(data['object'].r_401k_contribution))
            data['distribution']['colors'].append("#617688")
            has_data = True
        if data['object'].insurance_contribution > 0:
            data['distribution']['labels'].append('Insurance')
            data['distribution']['vals'].append(float(data['object'].insurance_contribution))
            data['distribution']['colors'].append("#ede76d")
            has_data = True
        if data['object'].gold_contribution > 0:
            data['distribution']['labels'].append('Gold')
            data['distribution']['vals'].append(float(data['object'].gold_contribution))
            data['distribution']['colors'].append("#ffd700")
            has_data = True
        if data['object'].cash_contribution > 0:
            data['distribution']['labels'].append('Cash')
            data['distribution']['vals'].append(float(data['object'].cash_contribution))
            data['distribution']['colors'].append(BankAccountInterface.get_chart_color())
            has_data = True
        if data['object'].crypto_contribution > 0:
            data['distribution']['labels'].append('Crypto')
            data['distribution']['vals'].append(float(data['object'].crypto_contribution))
            data['distribution']['colors'].append(CryptoInterface.get_chart_color())
            has_data = True
        if has_data:
            print(data['distribution'])

        data['user_str'] = get_user_name_from_id(data['object'].user)
        data['target_date'] = data['object'].start_date+relativedelta(months=data['object'].time_period)
        data['progress_data'] = dict()
        id = data['object'].id
        
        full_file_path = settings.MEDIA_ROOT + '/goal/yearly_contrib/' + str(id) + '/chart_data.json'
        read_from_file_successful = False
        
        if os.path.exists(full_file_path):
            try:
                with open(full_file_path) as f:
                    chart_data = json.load(f)
                    read_from_file_successful = True
            except Exception as ex:
                print(f'exception opening {full_file_path}: {ex}')
                read_from_file_successful = False
            full_file_path = settings.MEDIA_ROOT + '/goal/yearly_contrib/' + str(id) + '/projection_data.json'
            try:
                with open(full_file_path) as f:
                    ret = json.load(f)
                    read_from_file_successful = True
            except Exception as ex:
                print(f'exception opening {full_file_path}: {ex}')
                read_from_file_successful = False
        
        if not read_from_file_successful:
            chart_data, ret = get_goal_yearly_contrib(id, None)

        data['progress_data']['chart_data'] = chart_data
        data['progress_data']['avg_growth'] = ret.get('avg_growth', 0)
        data['progress_data']['avg_contrib'] = ret.get('avg_contrib', 0)
        data['final_projection'] = ret.get('final_projection', 0)
        #total_contribution = ret.get('total_contribution', 0)
        total_contribution = float(data['object'].achieved_amt)
        contrib_percent = int(total_contribution*100/float(data['object'].final_val))
        project_percent = int(float(data['final_projection']-data['object'].achieved_amt)*100/float(data['object'].final_val))

        remaining_percent = 100 - contrib_percent - project_percent
        if remaining_percent < 0:
            remaining_percent = 0
        data['status_line'] = [contrib_percent, project_percent, remaining_percent]
        data['status_text'] = list()
        if ret.get('avg_growth', 0) > 0:
            yrly_investment_reqd = get_required_yrly_investment(total_contribution,ret.get('avg_growth'), data['target_date'], data['object'].final_val)
            data['status_text'].append(['avg_growth', yrly_investment_reqd, ret.get('avg_growth', 0)])
        if ret.get('avg_contrib', 0) > 0:
            growth_reqd = get_required_xirr(total_contribution, ret.get('avg_contrib', 0), data['target_date'], data['object'].final_val)
            data['status_text'].append(['avg_contrib', ret.get('avg_contrib', 0), growth_reqd])
        if ret.get('last_yr_contrib', 0)>0:
            growth_reqd = get_required_xirr(total_contribution, ret.get('last_yr_contrib', 0), data['target_date'], data['object'].final_val)
            data['status_text'].append(['last_year', ret.get('last_yr_contrib', 0), growth_reqd])
 
        yrly_investment_reqd = get_required_yrly_investment(total_contribution,8, data['target_date'], data['object'].final_val)
        data['status_text'].append(['default_8', yrly_investment_reqd, 8])

        yrly_investment_reqd = get_required_yrly_investment(total_contribution,12, data['target_date'], data['object'].final_val)
        data['status_text'].append(['default_12',yrly_investment_reqd, 12])

        data['curr_module_id'] = 'id_goal_module'
        print("GoalProgressData - returning:", data)
        print(data)
        return data

class GoalDeleteView(DeleteView):
    template_name = 'goals/goal_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Goal, id=id_)

    def get_success_url(self):
        return reverse('goals:goal-list')

    def delete(self, request, *args, **kwargs):
        delete_goal(kwargs['id'])
        return super(DeleteView, self).delete(request, *args, **kwargs)

def add_goal(request):
    # https://www.youtube.com/watch?v=Zx09vcYq1oc&list=PLLxk3TkuAYnpm24Ma1XenNeq1oxxRcYFT
    template = 'goals/add_goal.html'
    if request.method == 'POST':
        print(request.POST)
        if "submit" in request.POST:
            print("submit button pressed")
            name = request.POST['name']
            start_date = request.POST['startdate']
            user_id = request.POST['user']
            time_period = Decimal(request.POST['time_period'])
            curr_val = Decimal(request.POST['curr_val'])
            inflation = Decimal(request.POST['inflation'])
            final_val = Decimal(request.POST['final_val'])
            recurring_pay_goal = False
            expense_period = 0
            post_returns = 0
            notes = request.POST['notes']
            add_goal_entry(name, start_date, curr_val, time_period, inflation,
                final_val, user_id, recurring_pay_goal, expense_period,
                post_returns, notes)
        else:
            print("calculate button pressed")
            name = request.POST['name']
            start_date = request.POST['startdate']
            user = request.POST['user']
            time_period = Decimal(request.POST['time_period'])
            curr_val = Decimal(request.POST['curr_val'])
            inflation = Decimal(request.POST['inflation'])
            notes = request.POST['notes']

            val = one_time_pay_final_val(curr_val, inflation, time_period)
            print("calculated value", val)
            users = get_all_users()
            context = {'users':users, 'user':user, 'startdate':start_date, 'name': name, 'notes': notes,
                'time_period': time_period, 'curr_val': curr_val, 'inflation':inflation, 'final_val':val,
                'curr_module_id':'id_goal_module'}
            return render(request, template, context=context)
    users = get_all_users()
    context = {'users':users, 'curr_module_id': 'id_goal_module'}
    return render(request, template, context=context)

def add_retirement_goal(request):
    # https://www.youtube.com/watch?v=Zx09vcYq1oc&list=PLLxk3TkuAYnpm24Ma1XenNeq1oxxRcYFT
    template = 'goals/add_retirement_goal.html'
    operation = 'Create Retirement Goal'
    if request.method == 'POST':
        print(request.POST)
        if "submit" in request.POST:
            print("submit button pressed")
            name = request.POST['name']
            start_date = request.POST['startdate']
            user_id = request.POST['user']
            time_period = Decimal(request.POST['time_period'])
            curr_val = Decimal(request.POST['curr_val'])
            inflation = Decimal(request.POST['inflation'])
            final_val = Decimal(request.POST['final_val'])
            post_returns = Decimal(request.POST['roi_corpus'])
            recurring_pay_goal = True
            expense_period = Decimal(request.POST['expense_period'])
            post_returns = Decimal(request.POST['roi_corpus'])
            notes = request.POST['notes']
            add_goal_entry(name, start_date, curr_val, time_period*12, inflation,
                    final_val, user_id, recurring_pay_goal, expense_period*12,
                    post_returns, notes)
        else:
            print("calculate button pressed")
            name = request.POST['name']
            start_date = request.POST['startdate']
            user = request.POST['user']
            time_period = Decimal(request.POST['time_period'])
            curr_val = Decimal(request.POST['curr_val'])
            inflation = Decimal(request.POST['inflation'])
            expense_period = Decimal(request.POST['expense_period'])
            post_returns = Decimal(request.POST['roi_corpus'])
            notes = request.POST['notes']
            corpus = get_corpus_to_be_saved(int(curr_val), float(inflation), int(time_period), int(expense_period), float(post_returns))
            print("calculated value", corpus)
            dates, corpus_vals, expense_vals = get_depletion_vals(corpus, int(curr_val), int(time_period), int(expense_period), float(inflation),  float(post_returns), start_date)
            print(json.dumps(dates))
            users = get_all_users()
            context = {'users':users, 'user':user, 'startdate':start_date, 'name': name, 'notes':notes,
                        'time_period': time_period, 'curr_val': curr_val, 'inflation':inflation, 'final_val':corpus,
                        'expense_period': expense_period, 'roi_corpus':post_returns, 'labels':json.dumps(dates), 
                        'corpus_vals': corpus_vals, 'expense_vals': expense_vals, 'operation':operation, 'curr_module_id':'id_goal_module'}
            return render(request, template, context=context)
    users = get_all_users()
    context = {'users':users, "labels":None, "data":None, 'operation':operation, 'curr_module_id': 'id_goal_module'}
    return render(request, template, context)

def update_goal(request, id):
    operation = 'Edit Goal'
    try:
        goal_obj = Goal.objects.get(id=id)
        if goal_obj.recurring_pay_goal:
            template = 'goals/add_retirement_goal.html'
            if request.method == 'POST':
                print(request.POST)
                if "submit" in request.POST:
                    print("submit button pressed")
                    goal_obj.name = request.POST['name']
                    goal_obj.start_date = request.POST['startdate']
                    goal_obj.user = request.POST['user']
                    goal_obj.time_period = Decimal(request.POST['time_period'])*12
                    goal_obj.curr_val = Decimal(request.POST['curr_val'])
                    goal_obj.inflation = Decimal(request.POST['inflation'])
                    goal_obj.final_val = Decimal(request.POST['final_val'])
                    goal_obj.expense_period = Decimal(request.POST['expense_period'])*12
                    goal_obj.post_returns = Decimal(request.POST['roi_corpus'])
                    goal_obj.recurring_pay_goal = True
                    goal_obj.post_returns = Decimal(request.POST['roi_corpus'])
                    goal_obj.notes = request.POST['notes']
                    goal_obj.save()
                else:
                    print("calculate button pressed")
                    name = request.POST['name']
                    start_date = request.POST['startdate']
                    user = request.POST['user']
                    time_period = Decimal(request.POST['time_period'])
                    curr_val = Decimal(request.POST['curr_val'])
                    inflation = Decimal(request.POST['inflation'])
                    expense_period = Decimal(request.POST['expense_period'])
                    post_returns = Decimal(request.POST['roi_corpus'])
                    notes = request.POST['notes']
                    corpus = get_corpus_to_be_saved(int(curr_val), float(inflation), int(time_period), int(expense_period), float(post_returns))
                    print("calculated value", corpus)
                    dates, corpus_vals, expense_vals = get_depletion_vals(corpus, int(curr_val), int(time_period), int(expense_period), float(inflation),  float(post_returns), start_date)
                    print(json.dumps(dates))
                    users = get_all_users()
                    context = {'users':users, 'user':user, 'startdate':start_date, 'name': name, 'notes':notes,
                                'time_period': time_period, 'curr_val': curr_val, 'inflation':inflation, 'final_val':corpus,
                                'expense_period': expense_period, 'roi_corpus':post_returns, 'labels':json.dumps(dates), 
                                'corpus_vals': corpus_vals, 'expense_vals': expense_vals, 'operation':operation, 'curr_module_id':'id_goal_module'}
                    return render(request, template, context=context)
                return HttpResponseRedirect("../")
            else:
                users = get_all_users()
                dates, corpus_vals, expense_vals = get_depletion_vals(int(goal_obj.final_val), int(goal_obj.curr_val), int(goal_obj.time_period/12), int(goal_obj.expense_period/12), float(goal_obj.inflation),  float(goal_obj.post_returns), goal_obj.start_date.strftime("%Y-%m-%d"))
                context = {'users':users, 'user':goal_obj.user, 'startdate':goal_obj.start_date.strftime("%Y-%m-%d"), 'name': goal_obj.name,
                            'time_period': int(goal_obj.time_period/12), 'curr_val': goal_obj.curr_val,
                            'inflation':goal_obj.inflation, 'final_val':goal_obj.final_val,
                            'expense_period': int(goal_obj.expense_period/12), 'roi_corpus':goal_obj.post_returns,
                            'notes':goal_obj.notes, 'recurring_pay_goal': goal_obj.recurring_pay_goal, 'labels':json.dumps(dates),
                            'corpus_vals': corpus_vals, 'expense_vals': expense_vals, 'operation':operation, 'curr_module_id':'id_goal_module'}
                return render(request, template, context=context) 
        else:
            template = 'goals/add_goal.html'
            if request.method == 'POST':
                print(request.POST)
                if "submit" in request.POST:
                    print("submit button pressed")
                    goal_obj.name = request.POST['name']
                    goal_obj.start_date = request.POST['startdate']
                    goal_obj.user = request.POST['user']
                    goal_obj.time_period = Decimal(request.POST['time_period'])
                    goal_obj.curr_val = Decimal(request.POST['curr_val'])
                    goal_obj.inflation = Decimal(request.POST['inflation'])
                    goal_obj.final_val = Decimal(request.POST['final_val'])
                    goal_obj.recurring_pay_goal = False
                    goal_obj.expense_period = 0
                    goal_obj.post_returns = 0
                    goal_obj.notes = request.POST['notes']
                    goal_obj.save()
                else:
                    print("calculate button pressed")
                    name = request.POST['name']
                    start_date = request.POST['startdate']
                    user = request.POST['user']
                    time_period = Decimal(request.POST['time_period'])
                    curr_val = Decimal(request.POST['curr_val'])
                    inflation = Decimal(request.POST['inflation'])
                    notes = request.POST['notes']

                    val = one_time_pay_final_val(curr_val, inflation, time_period)
                    print("calculated value", val)
                    users = get_all_users()
                    context = {'users':users, 'user':user, 'startdate':start_date, 'name': name, 'notes':notes,
                        'time_period': time_period, 'curr_val': curr_val, 'inflation':inflation, 'final_val':val, 'operation':operation,
                        'curr_module_id':'id_goal_module'}
                    return render(request, template, context=context)
                return HttpResponseRedirect("../")
            else:
                users = get_all_users()
                context = {'users':users, 'user':goal_obj.user, 'startdate':goal_obj.start_date.strftime("%Y-%m-%d"), 'name': goal_obj.name,
                            'time_period': goal_obj.time_period, 'curr_val': goal_obj.curr_val,
                            'inflation':goal_obj.inflation, 'final_val':goal_obj.final_val,
                            'expense_period': goal_obj.expense_period, 'roi_corpus':goal_obj.post_returns,
                            'notes':goal_obj.notes, 'recurring_pay_goal': goal_obj.recurring_pay_goal, 'operation':operation,
                            'curr_module_id':'id_goal_module'}
                return render(request, template, context=context) 
    except Goal.DoesNotExist:
        pass

class GoalNames(APIView):
    authentication_classes = []
    permission_classes = []
    def get(self, request, format=None, user=None):
        data = dict()
        data['goal_list'] = list()
        if not user:
            return Response(data)
        print('user is', user)
        try:
            goal_list = dict()
            goal_objs = Goal.objects.filter(user=user)
            for goal_obj in goal_objs:
                goal_list[goal_obj.id] = goal_obj.name
            ext_user = get_ext_user(user)
            for u in get_users(ext_user):
                if u.id == int(user):
                    continue
                gos = Goal.objects.filter(user=u.id)
                for go in gos:
                    goal_list[go.id] = '* ' + go.name
            data['goal_list'] = goal_list
        except Exception as e:
            print(e)
        finally:
            print(data)
            return Response(data)


class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None):
        data = dict()
        try:
            goal_obj = Goal.objects.get(id=id)
            contrib = get_goal_contributions(id)
            debt = contrib['debt']
            equity = contrib['equity']
            gold = contrib['gold']
            cash = contrib['cash']
            achieved = contrib['total']
            target = goal_obj.final_val
            if target < 1:
                target = 1
            remaining = target - achieved
            if remaining < 0:
                remaining = 0
            remaining_per = round(remaining*100/target, 2)
            achieve_per = round(achieved*100/target, 2)
            data = {
                "id": id,
                "debt": debt,
                "equity": equity,
                "gold": gold,
                "cash":cash,
                "distrib_labels": contrib['distrib_labels'],
                "distrib_vals": contrib['distrib_vals'],
                "distrib_colors": contrib['distrib_colors'],
                "achieved": achieved,
                "remaining": remaining,
                "remaining_per": remaining_per,
                "achieve_per": achieve_per,
            }
        except Exception as e:
            print(e)
        finally:
            print(data)
            return Response(data)

class CurrentGoals(APIView):
    authentication_classes = []
    permission_classes = []
    def get(self, request, format=None, user_id=None):
        goals = list()
        if user_id:
            goal_objs = Goal.objects.filter(user=user_id)
        else:
            goal_objs = Goal.objects.all()
        for goal_obj in goal_objs:
            data = dict()
            data['id'] = goal_obj.id
            data['name'] = goal_obj.name
            data['start_date'] = goal_obj.start_date
            data['curr_val'] = goal_obj.curr_val
            data['final_val'] = goal_obj.final_val
            data['user'] = get_user_name_from_id(goal_obj.user)
            data['user_id'] = goal_obj.user
            data['notes'] = goal_obj.notes
            contrib = get_goal_contributions(goal_obj.id)
            data['debt'] = contrib['debt']
            data['equity'] = contrib['equity']
            data['gold'] = contrib['gold']
            data['cash'] = contrib['cash']
            data['achieved'] = contrib['total']
            target = goal_obj.final_val
            if target < 1:
                target = 1
            remaining = target - data['achieved']
            if remaining < 0:
                remaining = 0
            data['remaining'] = remaining
            data['remaining_per'] = int(remaining*100/target)
            data['achieve_per'] = int(data['achieved']*100/target)
            data['target_date'] = goal_obj.start_date + relativedelta(months=goal_obj.time_period)
            goals.append(data)
        return Response(goals)

class GoalProgressData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None, expected_return=None):
        print('inside goal progress data')
        data = dict()
        try:
            goal_obj = Goal.objects.get(id=id)
            #target_vals,target_dates = get_monthly_projected_vals_and_dates(goal_obj.start_date, goal_obj.start_amount, goal_obj.time_period, goal_obj.inflation)
            chart_data, ret = get_goal_yearly_contrib(id, expected_return)
            data['chart_data'] = chart_data
            data['avg_growth'] = ret.get('avg_growth', 0)
            data['avg_contrib'] = ret.get('avg_contrib', 0)
            print("GoalProgressData - returning:", data)
            
        except Exception as e:
            print('exception in GoalProgressData', e)
        finally:
            print('returning from finally', data)
            return Response(data)