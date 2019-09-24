from NSTU_time_table.TimeTableToIcs import TimeTableToIcs
import argparse


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='''
    Генерация ICalendar для расписания бакалавров и магистрантов НГТУ.
    
    Парсер актурален на 2019 год.
    ''')
    arg_parser.add_argument('url', type=str, help='Ссылка на расписание НГТУ')
    arg_parser.add_argument('-s', '--subgroup', type=int, help='Номер подгруппы (для тех у кого в расписании указана подгруппа)')
    arg_parser.add_argument('-l', '--last', type=int, default=18 ,help='Номер последней недели в семестре (P.S. Парсеру неоткуда взять эту инфу). По умолячанию последняя неделя – 18')
    args = arg_parser.parse_args()

    time_table = TimeTableToIcs(url=args.url, subgroup=args.subgroup, last_week=args.last)
    print(time_table.get_events())

