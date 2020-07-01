import datetime

def get_float_or_none_from_string(input):
    if input != None and input != '':
        try:
            res = float(input)
            return res
        except Exception as e:
            print('error converting ', input, ' to float')
    return None

def get_int_or_none_from_string(input):
    if input != None and input != '':
        try:
            res = int(input)
            return res
        except Exception as e:
            print('error converting ', input, ' to int')
    return None

# default format expected of kind 2020-06-01
def get_date_or_none_from_string(input, format='%Y-%m-%d'):
    if input != None and input != '':
        try:
            res = datetime.datetime.strptime(input, format)
            return res
        except Exception as e:
            print('error converting ', input, ' to date')
    return None

def convert_date_to_string(input, format='%Y-%m-%d'):
    return input.strftime("%Y-%m-%d")