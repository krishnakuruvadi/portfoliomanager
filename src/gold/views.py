from django.shortcuts import render
from shared.handle_get import *
from decimal import Decimal
from .models import Gold, SellTransaction
from django.db import IntegrityError
from shared.utils import *
from django.http import HttpResponseRedirect
from django.urls import reverse
from tasks.tasks import update_gold_vals
from goal.goal_helper import get_goal_id_name_mapping_for_user

# Create your views here.


def get_trans(request):
    template = 'gold/trans_list.html'
    context = dict()
    context['goal_name_mapping'] = get_all_goals_id_to_name_mapping()
    context['user_name_mapping'] = get_all_users()
    context['curr_module_id'] = 'id_gold_module'
    context['object_list'] = list()
    latest_value = 0
    buy_value = 0
    unrealised_gain = 0
    realised_gain = 0
    total_weight = 0
    unsold_weight = 0
    for g in Gold.objects.all():
        context['object_list'].append(g)
        latest_value += g.latest_value if g.latest_value else 0
        buy_value += g.buy_value
        realised_gain += g.realised_gain if g.realised_gain else 0
        unrealised_gain += g.unrealised_gain if g.unrealised_gain else 0
        unsold_weight += g.unsold_weight if g.unsold_weight else 0
        total_weight += g.weight
    context['latest_value'] = round(latest_value, 2)
    context['total_investment'] = round(buy_value, 2)
    context['unrealised_gain'] = round(unrealised_gain, 2)
    context['realised_gain'] = round(realised_gain, 2)
    context['total_weight'] = total_weight
    context['unsold_weight'] = unsold_weight
    return render(request, template, context)

def add_trans(request):
    template = 'gold/add_trans.html'
    context = dict()
    message = ''
    message_color = 'ignore'
    if request.method == 'POST':
        try:
            goal = request.POST.get('goal', '')
            if goal != '':
                goal_id = Decimal(goal)
            else:
                goal_id = None
            notes = request.POST['notes']
            user = request.POST['user']
            weight = Decimal(request.POST['weight'])
            per_gm = Decimal(request.POST['per_gram'])
            buy_value = Decimal(request.POST['buy_value'])
            buy_date = get_date_or_none_from_string(request.POST['buy_date'])
            buy_type = request.POST['buy_type']
            purity = '24K'
            if buy_type == 'Physical':
                purity = request.POST['purity']
            Gold.objects.create(
                user=user,
                goal=goal_id,
                notes=notes,
                weight=weight,
                per_gm=per_gm,
                buy_value=buy_value,
                buy_date=buy_date,
                buy_type=buy_type,
                unsold_weight=weight,
                purity=purity
            )
            message_color = 'green'
            message = 'Buy transaction added successfully'
            update_gold_vals(user)
        except IntegrityError as ie:
            print(f'exception when adding Gold trans {ie}')
            message = 'Transaction exists'
            message_color = 'red'

    users = get_all_users()
    context = {'users':users, 'message': message, 'message_color':message_color, 'curr_module_id': 'id_gold_module'}
    return render(request, template, context)

def trans_delete(request, id):
    try:
        g = Gold.objects.get(id=id)
        user = g.user
        g.delete()
        update_gold_vals(user)
    except Gold.DoesNotExist:
        print(f'Transaction not found {id} for delete')
    
    return HttpResponseRedirect(reverse('gold:trans-list'))

def delete_all_trans(request):
    try:
        g = Gold.objects.all().delete()
        update_gold_vals()
    except Exception as ex:
        print(f'Exception {ex} during delete all transactions')
    
    return HttpResponseRedirect(reverse('gold:trans-list'))

def update_trans(request, id):
    template = 'gold/update_trans.html'
    context = dict()
    message = ''
    message_color = 'ignore'
    try:
        g = Gold.objects.get(id=id)
        if request.method == 'POST':
            try:
                goal = request.POST.get('goal', '')
                if goal != '':
                    goal_id = Decimal(goal)
                else:
                    goal_id = None
                g.goal = goal_id
                g.notes = request.POST['notes']
                g.weight = Decimal(request.POST['weight'])
                g.per_gm = Decimal(request.POST['per_gm'])
                g.buy_value = Decimal(request.POST['buy_value'])
                g.save()
                message = 'Update successful'
                message_color = 'green'
                update_gold_vals(g.user)
            except IntegrityError as ie:
                print(f'exception when updating Gold trans {ie}')
                message = 'Update failed'
                message_color = 'red'
    except Gold.DoesNotExist:
        return HttpResponseRedirect(reverse('gold:trans-list'))
    g = Gold.objects.get(id=id)
    context['message'] = message
    context['message_color'] = message_color
    context['user'] = get_user_name_from_id(g.user)
    context['goal'] = g.goal if g.goal else ''
    context['goals'] = {'goal_list':get_goal_id_name_mapping_for_user(g.user)}
    context['buy_value'] = g.buy_value
    context['buy_date'] = g.buy_date
    context['id'] = g.id
    context['weight'] = g.weight
    context['per_gm'] = g.per_gm
    context['buy_type'] = g.buy_type
    return render(request, template, context)

def trans_detail(request, id):
    template = 'gold/gold_detail.html'
    context = dict()
    try:
        g = Gold.objects.get(id=id)
        context['user'] = get_user_name_from_id(g.user)
        context['goal'] = get_goal_name_from_id(g.goal)
        context['notes'] = g.notes
        context['weight'] = g.weight
        context['per_gm'] = g.per_gm
        context['buy_value'] = g.buy_value
        context['buy_date'] = g.buy_date
        context['buy_type'] = g.buy_type
        context['as_on'] = g.as_on_date
        context['unsold'] = g.unsold_weight
        context['realised_gain'] = g.realised_gain
        context['unrealised_gain'] = g.unrealised_gain
        context['roi'] = g.roi
        context['latest_value'] = g.latest_value
        print(context)
        return render(request, template, context)
    except Gold.DoesNotExist:
        return HttpResponseRedirect(reverse('gold:trans-list'))

def sell_transactions(request,id):
    template = 'gold/sell_trans_list.html'

    context = dict()
    try:
        g = Gold.objects.get(id=id)
        st = SellTransaction.objects.filter(buy_trans=g)
        context['object_list'] = list()
        for trans in st:
            context['object_list'].append(trans)
        context['buy_id'] = g.id
        context['buy_date'] = g.buy_date
        return render(request, template, context)
    except Gold.DoesNotExist:
        return HttpResponseRedirect(reverse('gold:trans-list'))

def sell_trans_detail(request, id, sell_id):
    pass

def delete_sell(request, id):
    try:
        g = Gold.objects.get(id=id)
        SellTransaction.objects.filter(buy_trans=g).delete()
        update_gold_vals(g.user)
        return HttpResponseRedirect(reverse('gold:sell-transactions',kwargs={'id':g.id}))
    except Gold.DoesNotExist:
        return HttpResponseRedirect(reverse('gold:trans-list'))

def add_sell_trans(request, id):
    template = 'gold/add_sell_trans.html'
    message = ''
    message_color='ignore'
    context = dict()
    try:
        g = Gold.objects.get(id=id)
        if request.method == 'POST':
            try:
                notes = request.POST['notes']
                weight = Decimal(request.POST['weight'])
                per_gm = Decimal(request.POST['per_gram'])
                sell_value = Decimal(request.POST['sell_value'])
                trans_date = get_date_or_none_from_string(request.POST['sell_date'])
                SellTransaction.objects.create(
                    buy_trans=g,
                    notes=notes,
                    weight=weight,
                    per_gm=per_gm,
                    trans_amount=sell_value,
                    trans_date=trans_date
                )
                message_color = 'green'
                message = 'Sell Transaction added successfully'
                update_gold_vals(g.user)
            except IntegrityError as ie:
                print(f'exception when adding Gold sell trans {ie}')
                message = 'Transaction exists'
                message_color = 'red'
        context = {'message': message, 'message_color':message_color, 'buy_id':g.id, 'buy_date':g.buy_date, 'unsold_weight':g.unsold_weight, 'curr_module_id': 'id_gold_module'}
        return render(request, template, context)
    except Gold.DoesNotExist:
        return HttpResponseRedirect(reverse('gold:trans-list'))