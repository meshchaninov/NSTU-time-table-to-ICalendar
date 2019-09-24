from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from typing import List, Tuple
import datetime
import requests
import re
import csv

WEEK_DAY = ('Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота')


@dataclass
class HeadStruct:
    today: datetime.date = None
    week_number: int = None
    group: str = None
    semester_num: int = None


@dataclass
class LessonStruct:
    day: str = None
    start_time: datetime.time = None
    end_time: datetime.time = None
    even: str = None
    name: str = None
    week: List[int] = field(default_factory=list)
    lecturers: List[str] = field(default_factory=list)
    auditory: List[str] = field(default_factory=list)
    sub_group: int = None


class FieldNotFound(Exception):
    pass

class NameNotFound(Exception):
    pass

class ParserStateMachine:
    def __init__(self, url):
        self._url: str = url
        self._time_table: List[LessonStruct] = []
        self._head: HeadStruct = None
        self._state_machine()

    def _get_page(self, url: str) -> str:
        return requests.get(url).text

    def _get_soup(self, url: str) -> BeautifulSoup:
        page = self._get_page(url)
        return BeautifulSoup(page, features='html5lib')

    def _clean_string_by_separ(self, string: str) -> List[str]:
        string = re.split(r'[\n\xa0;]|\s{2,}', string)
        string = [s.strip() for s in string]
        string = [s for s in string if s != '']
        return string

    def _fetch_data(self, url: str) -> Tuple[List[List[str]], List[List[str]]]:
        soup = self._get_soup(url)
        soup = [re.findall(r'[^\\n]+' , x.text) for x in soup.find('table').find_all('tr')]
        all_data = [[self._clean_string_by_separ(dirty) for dirty in elem][0] for elem in soup]
        head, data = all_data[:4], all_data[5:]
        return head, data

    def _check_suggestion(self, regex: str, string: str) -> bool:
        check = re.match(r'^'+regex+r'$', string)
        return False if not check else True

    def _check_is_time(self, string: str) -> bool:
        return self._check_suggestion(r'\d+:\d+ - \d+:\d+', string)

    def _check_is_even(self, string: str) -> bool:
        return string == 'Ч' or string == 'Н'

    def _check_is_name(self, string: str) -> bool:
        return self._check_suggestion(r'[А-Я].+', string)

    def _check_is_week(self, string: str) -> bool:
        return self._check_suggestion(r'нед.:[\s\d]+', string)

    def _check_is_lecturer(self, string: str) -> bool:
        return self._check_suggestion(r'[А-я]+(\s[А-я]\.)+', string)

    def _check_is_auditory(self, string: str) -> bool:
        return self._check_suggestion(r'((\d+[а-я]*\-\d+[а-я]*)\s?)+', string) or self._check_suggestion(r'[а-я\s]+', string)

    def _check_is_subgroup(self, string: str) -> bool:
        return self._check_suggestion(r'\d+ п\.гр\.', string)

    def _get_start_end_time(self, times: str) -> Tuple[datetime.time, datetime.time]:
        data = re.findall(r'\d+', times)
        start_time = datetime.time(int(data[0]), int(data[1]))
        end_time = datetime.time(int(data[2]), int(data[3]))
        return start_time, end_time

    def _get_week_numbers(self, weeks: str) -> List[int]:
        data = re.findall(r'\d+', weeks)
        return [int(num) for num in data]

    def _get_num_subgroup(self, string: str) -> int:
        data = re.search(r'(\d+)', string)
        return int(data.group(0))

    def _get_auditory(self, string: str) -> List[str]:
        data = re.findall(r'((\d+[а-я]*\-\d+[а-я]*)\s?)', string)
        if not data:
            return [string]
        return [elem[0] for elem in data]

    def _state_machine_data(self, data: List[List[str]]) -> List[LessonStruct]:
        time_table: List[LessonStruct] = []
        day: str = None
        start_time, end_time = None, None
        for line in data:
            # Если строчка из одного элемента считаем, что это либо день недели, либо строка без полезных данных
            if len(line) == 1:
                if line[0] in WEEK_DAY:
                    day = line[0]
                continue
            lesson = LessonStruct(day=day)
            for elem in line:
                if self._check_is_time(elem):
                    start_time, end_time = self._get_start_end_time(elem)
                    lesson.start_time = start_time
                    lesson.end_time = end_time
                elif self._check_is_even(elem):
                    lesson.even = elem
                elif self._check_is_lecturer(elem):
                    lesson.lecturers.append(elem)
                elif self._check_is_auditory(elem):
                    auditory = self._get_auditory(elem)
                    for e in auditory:
                        lesson.auditory.append(e)
                elif self._check_is_week(elem):
                    lesson.week = self._get_week_numbers(elem)
                elif self._check_is_subgroup(elem):
                    lesson.sub_group = self._get_num_subgroup(elem)
                elif self._check_is_name(elem):
                    lesson.name = elem
                else:
                    raise FieldNotFound

            # Если не найдено время на этой строке, значит оно указано на предыдущей (из-за rowspawn=2 и
            # кривых рук программиста:( )
            if lesson.end_time is None and lesson.start_time is None:
                lesson.start_time = start_time
                lesson.end_time = end_time
            if lesson.name is None:
                raise NameNotFound
            time_table.append(lesson)
        return time_table

    def _get_date_in_head(self, string: str) -> datetime.date:
        MONTHS = (
            'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
            'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
        )
        res = re.findall(r'(\d+)\s([а-я]+)\s(\d+)', string)[0]
        return datetime.date(int(res[2]), MONTHS.index(res[1]) + 1, int(res[0]))

    def _get_week_number_in_head(self, string: str) -> int:
        res = re.search(r'\d+', string)
        return int(res.group(0))

    def _get_group_in_head(self, string: str) -> str:
        res = re.search(r'Группа (.+)', string)
        return res.group(0)

    def _get_semestr_in_head(self, string: str) -> int:
        res = re.search(r'\d+', string)
        return int(res.group(0))

    def _state_machine_head(self, head: List[List[str]]) -> HeadStruct:
        all_i_need = head[0]
        today = self._get_date_in_head(all_i_need[0])
        week_number = self._get_week_number_in_head(all_i_need[2])
        group = self._get_group_in_head(all_i_need[3])
        semester = self._get_semestr_in_head(all_i_need[4])
        return HeadStruct(today=today, week_number=week_number, group=group, semester_num=semester)

    def _state_machine(self) -> None:
        head, data = self._fetch_data(self._url)
        self._time_table = self._state_machine_data(data)
        self._head = self._state_machine_head(head)

    def get_time_table(self) -> List[LessonStruct]:
        return self._time_table

    def get_head_table(self) -> HeadStruct:
        return self._head

    # TODO: DO THIS
    # def to_csv_file(self) -> None:
    #     with open(self._head.group + ' ' + str(self._head.semester_num) + ' семестр', 'w') as csv_file:
    #         head = f'День,Начало,Конец,Ч/Н,Наиминование,'
    #         for lesson in self._time_table:
    #
    #             line = f'{lesson.day},{lesson.start_time},{lesson.end_time},{lesson.even},{lesson.name},{lesson.lecturers},{lesson.sub_group},{lesson.auditory}\n'
    #             csv_file.write(line)



def main():
    url = "https://ciu.nstu.ru/student/time_table_view?idgroup=33255&fk_timetable=39553&nomenu=1&print=1"
    time_table = ParserStateMachine(url)
    print(time_table.get_time_table())



if __name__ == "__main__":
    main()