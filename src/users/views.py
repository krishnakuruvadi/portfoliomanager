from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import (
    ListView,
    DetailView,
    DeleteView
)
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.template import Context
from shared.handle_delete import delete_user
from shared.handle_chart_data import get_user_contributions
from .models import User
from shared.utils import get_date_or_none_from_string
from epf.epf_interface import EpfInterface
from espp.espp_interface import EsppInterface
from fixed_deposit.fd_interface import FdInterface
from ppf.ppf_interface import PpfInterface
from ssy.ssy_interface import SsyInterface
from shares.share_interface import ShareInterface
from mutualfunds.mf_interface import MfInterface
from retirement_401k.r401k_interface import R401KInterface
from rsu.rsu_interface import RsuInterface
from insurance.insurance_interface import InsuranceInterface
import datetime
from shared.utils import get_min


# Create your views here.
class UserListView(ListView):
    template_name = 'users/user_list.html'
    queryset = User.objects.all()
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['curr_module_id'] = 'id_user_module'
        print(data)
        return data

def contrib_deduct_str(c, d):
    return str(int(c)) + ' / ' + str(int(d))

class UserDetailView(DetailView):
    template_name = 'users/user_detail.html'

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(User, id=id_)

    def get_context_data(self, **kwargs):
        id_ = self.kwargs.get("id")
        data = super().get_context_data(**kwargs)

        start_day = datetime.date.today()
        start_day = get_min(EpfInterface.get_start_day_for_user(id_), start_day)
        start_day = get_min(EsppInterface.get_start_day_for_user(id_), start_day)
        start_day = get_min(FdInterface.get_start_day_for_user(id_), start_day)
        start_day = get_min(MfInterface.get_start_day_for_user(id_), start_day)
        start_day = get_min(PpfInterface.get_start_day_for_user(id_), start_day)
        start_day = get_min(SsyInterface.get_start_day_for_user(id_), start_day)
        start_day = get_min(ShareInterface.get_start_day_for_user(id_), start_day)
        start_day = get_min(R401KInterface.get_start_day_for_user(id_), start_day)
        start_day = get_min(RsuInterface.get_start_day_for_user(id_), start_day)
        start_day = get_min(InsuranceInterface.get_start_day_for_user(id_), start_day)

        new_start_day = datetime.date(start_day.year, start_day.month, 1)
        
        curr_yr = datetime.date.today().year
        investment_types = list()
        yrly = dict()
        for yr in range(start_day.year, curr_yr+1):
            total_c = 0
            total_d = 0
            yrly[yr] = dict()
            c, d = PpfInterface.get_user_yearly_contrib(id_, yr)
            if c > 0 and not 'PPF' in investment_types:
                investment_types.append('PPF')
            yrly[yr]['PPF'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c,d = R401KInterface.get_user_yearly_contrib(id_, yr)
            if c > 0 and not '401K' in investment_types:
                investment_types.append('401K')
            yrly[yr]['401K'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c,d = RsuInterface.get_user_yearly_contrib(id_, yr)
            if c > 0 and not 'RSU' in investment_types:
                investment_types.append('RSU')
            yrly[yr]['RSU'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c,d = InsuranceInterface.get_user_yearly_contrib(id_, yr)
            if c > 0 and not 'Insurance' in investment_types:
                investment_types.append('Insurance')
            yrly[yr]['Insurance'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c,d = EpfInterface.get_user_yearly_contrib(id_, yr)
            if c > 0 and not 'EPF' in investment_types:
                investment_types.append('EPF')
            yrly[yr]['EPF'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c, d = SsyInterface.get_user_yearly_contrib(id_, yr)
            if (c != 0 or d !=0) and not 'SSY' in investment_types:
                investment_types.append('SSY')
            yrly[yr]['SSY'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c, d = MfInterface.get_user_yearly_contrib(id_, yr)
            if (c != 0 or d !=0) and not 'MF' in investment_types:
                investment_types.append('MF')
            yrly[yr]['MF'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c, d = EsppInterface.get_user_yearly_contrib(id_, yr)
            if (c != 0 or d !=0) and not 'ESPP' in investment_types:
                investment_types.append('ESPP')
            yrly[yr]['ESPP'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c, d = FdInterface.get_user_yearly_contrib(id_, yr)
            if (c != 0 or d !=0) and not 'FD' in investment_types:
                investment_types.append('FD')
            yrly[yr]['FD'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            c, d = ShareInterface.get_user_yearly_contrib(id_, yr)
            if (c != 0 or d !=0) and not 'Shares' in investment_types:
                investment_types.append('Shares')
            yrly[yr]['Shares'] = contrib_deduct_str(c, d)
            total_c += int(c)
            total_d += int(d)

            yrly[yr]['Total'] = contrib_deduct_str(total_c, total_d)

        for item in ['PPF', '401K', 'RSU', 'EPF', 'ESPP', 'SSY', 'MF', 'FD', 'Shares', 'Insurance']:
            if item not in investment_types:
                for yr in range(start_day.year, curr_yr+1):
                    del yrly[yr][item]
        investment_types.append('Total')

        data['yrly_investment'] = yrly
        data['investment_types'] = investment_types
        data['curr_module_id'] = 'id_user_module'
        print(data)
        return data


class UserDeleteView(DeleteView):
    template_name = 'users/user_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(User, id=id_)

    def get_success_url(self):
        return reverse('users:user-list')
    
    def delete(self, request, *args, **kwargs):
        print(request)
        delete_user(kwargs['id'])
        return super(DeleteView, self).delete(request, *args, **kwargs)

def add_user(request):
    template = 'users/add_user.html'
    if request.method == 'POST':
        name = request.POST['name']
        short_name = request.POST['short_name']
        dob = get_date_or_none_from_string(request.POST['dob'])
        email = request.POST['email']
        notes = request.POST['notes']
        User.objects.create(name=name, dob=dob, notes=notes, email=email, short_name=short_name)
    context = {'curr_module_id': 'id_user_module'}
    return render(request, template, context=context)

def update_user(request, id):
    template = 'users/add_user.html'
    try:
        user_obj = User.objects.get(id=id)
        if request.method == 'POST':
            user_obj.name = request.POST['name']
            user_obj.short_name = request.POST['short_name']
            user_obj.email = request.POST['email']
            user_obj.dob = request.POST['dob']
            user_obj.notes = request.POST['notes']
            user_obj.save()
        else:
            short_name = user_obj.short_name
            if not short_name:
                short_name = ''
            context = {'curr_module_id': 'id_user_module', 'name': user_obj.name, 'short_name': short_name, 'email':user_obj.email, 'dob':user_obj.dob.strftime("%Y-%m-%d"), 'notes':user_obj.notes}
            return render(request, template, context=context)
        return HttpResponseRedirect("../")
    except User.DoesNotExist:
        pass

class ChartData(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, format=None, id=None):
        data = dict()
        try:
            user_obj = User.objects.get(id=id)
            contrib = get_user_contributions(id)
            debt = contrib['debt']
            equity = contrib['equity']
            achieved = contrib['total']
            target = contrib['target']
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

class Users(APIView):
    authentication_classes = []
    permission_classes = []
    def get(self, request, format=None):
        data = dict()
        data['user_list'] = list()
        user_objs = User.objects.all()
        for user_obj in user_objs:
            obj = dict()
            obj['id'] = user_obj.id
            obj['name'] = user_obj.name
            data['user_list'].append(obj)
        return Response(data)