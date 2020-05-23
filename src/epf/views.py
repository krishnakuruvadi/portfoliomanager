from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    ListView,
    DeleteView
)
from .forms import EpfModelForm
from .models import Epf, EpfEntry
import datetime
from dateutil.relativedelta import relativedelta



# Create your views here.
class EpfCreateView(CreateView):
    template_name = 'epfs/epf_create.html'
    form_class = EpfModelForm
    queryset = Epf.objects.all() # <blog>/<modelname>_list.html
    #success_url = '/'

    def form_valid(self, form):
        print(form.cleaned_data)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('epfs:epf-list')

class EpfListView(ListView):
    template_name = 'epfs/epf_list.html'
    queryset = Epf.objects.all() # <blog>/<modelname>_list.html

class EpfDeleteView(DeleteView):
    template_name = 'epfs/epf_delete.html'
    
    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Epf, id=id_)

    def get_success_url(self):
        return reverse('epfs:epf-list')

class EpfDetailView(DetailView):
    template_name = 'epfs/epf_detail.html'
    #queryset = Ppf.objects.all()

    def get_object(self):
        id_ = self.kwargs.get("id")
        return get_object_or_404(Epf, id=id_)

def get_fy_details(fy):
    print('retrieving data for fy', fy)
    month_abbr = ['apr_', 'may_', 'jun_', 'jul_', 'aug_', 'sep_', 'oct_', 'nov_', 'dec_', 'jan_', 'feb_', 'mar_']
    datetime_str = '04/01/' + fy
    datetime_object = datetime.datetime.strptime(datetime_str, '%m/%d/%Y')
    ret = dict()
    for i in range(len(month_abbr)):
        date = datetime_object+relativedelta(months=i)
        try:
            contrib = EpfEntry.objects.get(trans_date=date)
            ret[month_abbr[i] + 'int'] = int(contrib.interest_contribution)
            ret[month_abbr[i] + 'er'] = int(contrib.employer_contribution)
            ret[month_abbr[i] + 'em'] = int(contrib.employee_contribution)
        except EpfEntry.DoesNotExist:
            pass
    return ret


def add_contribution(request, id):
    template = 'epfs/epf_add_contrib.html'
    epf_obj = get_object_or_404(Epf, id=id)
    epf_start_year = epf_obj.start_date.year
    this_year = datetime.date.today().year if datetime.date.today().month < 4 else datetime.date.today().year+1
    fy_list = ['Select']
    for i in range(epf_start_year, this_year):
        fy_list.append(str(i) + '-' + str(i+1)[2:])
    month_abbr = ['apr_', 'may_', 'jun_', 'jul_', 'aug_', 'sep_', 'oct_', 'nov_', 'dec_', 'jan_', 'feb_', 'mar_']
    if request.method == 'POST':
        print(request.POST)
        print(request.POST.get('fy'))
        
        if "submit" in request.POST:
            print("submit button pressed")
            fy = request.POST.get('fy')
            fy = fy[0:4]
            datetime_str = '04/01/' + fy
            datetime_object = datetime.datetime.strptime(datetime_str, '%m/%d/%Y')
                
            for i in range(len(month_abbr)):
                interest_str = request.POST.get(month_abbr[i] + 'int')
                employee_str = request.POST.get(month_abbr[i] + 'em')
                employer_str = request.POST.get(month_abbr[i] + 'er')
                print('interest_str',interest_str,' employee_str', employee_str, ' employer_str', employer_str)
                interest = int(float(interest_str)) if interest_str != '' else 0
                employee = int(float(employee_str)) if employee_str != '' else 0
                employer = int(float(employer_str)) if employer_str != '' else 0
                if (interest + employee + employer) > 0:
                    date = datetime_object+relativedelta(months=i)
                    try:
                        contrib = EpfEntry.objects.get(trans_date=date)
                        contrib.employee_contribution = employee
                        contrib.employer_contribution = employer
                        contrib.interest_contribution = interest
                        contrib.save()
                    except EpfEntry.DoesNotExist:
                        EpfEntry.objects.create(epf_id=epf_obj,
                                                trans_date=date,
                                                employee_contribution=employee,
                                                employer_contribution=employer,
                                                interest_contribution=interest)
        else:
            print("fetch button pressed")
            fy = request.POST.get('fy')
            if fy != 'Select':
                context = get_fy_details(fy[0:4])
                context['fy_list']=fy_list
                context['sel_fy'] = fy
                context['object'] = {'number':epf_obj.number, 'company':epf_obj.company}
                print(context)
                return render(request, template, context)
    
    context = {'fy_list':fy_list, 'object': {'number':epf_obj.number, 'company':epf_obj.company, 'sel_fy':'select'}}
    return render(request, template, context)
