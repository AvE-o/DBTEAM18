from datetime import datetime

#2022-07-01 00:00:00 to 2022-07-01
def convert_date_to_day(date):
    day = date.strftime('%Y-%m-%d')
    return day

def convert_exp_date_to_sql_date(day):
    date_str = '05/23'  # MM/YY格式的日期
    date_obj = datetime.strptime(date_str, '%m/%y')
    mysql_date_str = date_obj.strftime('%Y-%m-%d %H:%M:%S')
    return mysql_date_str
