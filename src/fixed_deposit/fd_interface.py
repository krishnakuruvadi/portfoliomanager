from .models import FixedDeposit

class FdInterface:
    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = FixedDeposit.objects.filter(user=user_id)
            else:
                objs = FixedDeposit.objects.all()
            
            for obj in objs:
                if not start_day:
                    start_day = obj.start_date
                else:
                    start_day = start_day if start_day < obj.start_date else obj.start_date
        except Exception as ex:
            print(f'exception finding start day for fd {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        if user_id:
            objs = FixedDeposit.objects.filter(user=user_id)
        else:
            objs = FixedDeposit.objects.all()
        for obj in objs:
            if not obj.goal:
                amt += 0 if not obj.final_val else obj.final_val
        return amt
