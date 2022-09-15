from .models import InvestmentData
import datetime

def get_investment_data(ext_user):
    if not ext_user:
        try:
            all_investment_data = InvestmentData.objects.get(user='all')
            return all_investment_data
            
        except InvestmentData.DoesNotExist:
            today = datetime.date.today()
            id = InvestmentData.objects.create(
                user='all',
                as_on_date=today,
                start_day_across_portfolio=today
                )
            return id