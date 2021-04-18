import datetime
from django.shortcuts import render
from shared.handle_get import get_start_day_across_portfolio, get_all_users, get_user_name_from_id
from epf.epf_helper import get_tax_for_user as gtuepf
from ppf.ppf_helper import get_tax_for_user as gtuppf
from mutualfunds.mf_helper import get_tax_for_user as gtumf

# Create your views here.

def tax_home(request):
    template = 'tax/tax_home.html'
    return render(request, template)

def tax_details(request):
    template = 'tax/tax_details.html'

    users = get_all_users()
    start_date = get_start_day_across_portfolio()
    years = list()
    for yr in range(start_date.year, datetime.date.today().year+1):
        years.append(yr)
    context = {'users':users, 'years':years, 'data':dict()}
    if request.method == 'POST':
        user_id = request.POST['user']
        country = request.POST['country']
        year = int(request.POST['year'])
        print(f'Getting tax details for user {user_id}, {country} for year {year}')
        from_date = datetime.date(year=year, month=4, day=1)
        to_date = datetime.date(year=year+1, month=3, day=31)
        if to_date > datetime.date.today():
            to_date = datetime.date.today()
        if country == 'USA':
            from_date = datetime.date(year=year, month=1, day=1)
            to_date = datetime.date(year=year, month=12, day=31)
            if to_date > datetime.date.today():
                to_date = datetime.date.today()
        context['data']['epf'] = gtuepf(user_id, from_date, to_date)
        context['data']['ppf'] = gtuppf(user_id, from_date, to_date)
        context['data']['mf'] = gtumf(user_id, from_date, to_date)
        context['user'] = user_id
        context['year'] = year
        context['from_date'] = from_date
        context['to_date'] = to_date
        context['user_name'] = get_user_name_from_id(user_id)
        context['country'] = country
    print(context)
    return render(request, template, context)