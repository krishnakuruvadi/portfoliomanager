from .models import RSUAward, RestrictedStockUnits

class RsuInterface:
    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = RSUAward.objects.filter(user=user_id)
            else:
                objs = RSUAward.objects.all()
            
            for obj in objs:
                trans = RestrictedStockUnits.objects.filter(award=obj)
                for t in trans:
                    if not start_day:
                        start_day = t.vest_date
                    else:
                        start_day = start_day if start_day < t.vest_date else t.vest_date
        except Exception as ex:
            print(f'exception finding start day for 401K {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        if user_id:
            objs = RSUAward.objects.filter(user=user_id)
        else:
            objs = RSUAward.objects.all()
        for obj in objs:
            if not obj.goal:
                trans = RestrictedStockUnits.objects.filter(award=obj)
                for t in trans:
                    amt += 0 if not obj.latest_value else obj.latest_value
        return amt
