from .models import Share, Transactions

class ShareInterface:
    @classmethod
    def get_start_day(self, user_id=None):
        start_day = None
        try:
            if user_id:
                objs = Share.objects.filter(user=user_id)
            else:
                objs = Share.objects.all()
            
            for obj in objs:
                share_trans = Transactions.objects.filter(share=obj)
                for trans in share_trans:
                    if not start_day:
                        start_day = trans.trans_date
                    else:
                        start_day = start_day if start_day < trans.trans_date else trans.trans_date
        except Exception as ex:
            print(f'exception finding start day for shares {ex}')
        return start_day

    @classmethod
    def get_no_goal_amount(self, user_id=None):
        amt = 0
        if user_id:
            objs = Share.objects.filter(user=user_id)
        else:
            objs = Share.objects.all()
        for obj in objs:
            if not obj.goal:
                amt += 0 if not obj.latest_value else obj.latest_value
        return amt
