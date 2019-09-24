# Экспорт расписания занятий НГТУ (Новосибирский Государственный Технический Университет) в формат ICalendar
Конвертер генерирует текст для создания файла ICalendar (стандарт RFC 5545) который можно экспортировать в _Google Calendar_, _Apple Calendar_, да и в любой
другой популярный календарь.

Парсер актуален на момент 1 семестра 2019 года.  

Не было возможности протестировать для 2-го семестра, имейте ввиду.
  
P.S.
Сами понимаете, парсеры не идеальны, возможны ошибки при генерации. Скрипт создавался для личного использования. Мне отказались давать API, пришлось выкручиваться ¯\_(ツ)_/¯

## Использование
Для macOS / Linux / Windows
```bash
python3 -m venv .env
source .env/bin/acticate
pip3 install -r requirements.txt
python3 main.py [URL] > [filename].ics
```


## Более подробно можно посмотреть в справке
```bash
python3 main.py -h
usage: main.py [-h] [-s SUBGROUP] [-l LAST_WEEK] url

Генерация ICalendar для расписания бакалавров и магистрантов НГТУ. Парсер
актуален на 2019 год.

positional arguments:
  url                   Ссылка на расписание НГТУ взятая с сайта nstu.ru (для
                        конкретной группы!)

optional arguments:
  -h, --help            show this help message and exit
  -s SUBGROUP, --subgroup SUBGROUP
                        Номер подгруппы (для тех у кого в расписании указана
                        подгруппа)
  -l LAST_WEEK, --last-week LAST_WEEK
                        Номер последней недели в семестре (P.S. Парсеру
                        неоткуда взять эту инфу). По умолчанию последняя
                        неделя – 18
```

## Пример
С генерировать **ICalendar** файл для группы РГ-91, подгруппы 2 и установить последнюю неделю - 17.
```bash
python3 main.py https://ciu.nstu.ru/student/time_table_view?idgroup=33281&fk_timetable=40065 -s 2 -l 17 > РГ-91.ics

```
