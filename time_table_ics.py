from typing import Tuple, List, Dict

from ics import Calendar, Event
from dateutil.tz import tzlocal
import datetime
from parser import NstuTimeTableParse, LessonStruct, HeadStruct, WEEK_DAY


class TimeTableToIcs:
    def __init__(self, url: str, subgroup: int = 0, last_week: int = 18):
        self._url = url
        self._last_week = last_week
        self._calendar = Calendar()
        self._head, self._data = self._get_data(url)
        self._beginning_of_weeks = self._get_beginning_of_weeks(
            self._get_current_week_in_year(),
            self._head.week_number,
            self._last_week
        )
        self._even_weeks = {
            week_key: week_value for week_key, week_value in self._beginning_of_weeks.items() if week_key % 2 == 0
        }
        self._not_even_weeks = {
            week_key: week_value for week_key, week_value in self._beginning_of_weeks.items() if week_key % 2 == 1
        }
        self._subgroup = subgroup

    def _get_data(self, url: str) -> Tuple[HeadStruct, List[LessonStruct]]:
        data = NstuTimeTableParse(url)
        return data.get_head_table(), data.get_time_table()

    def _get_start_week_by_number(self, number: int) -> datetime.datetime:
        return datetime.datetime.strptime(f'{datetime.datetime.now().year}-{number}-1', '%G-%V-%u')

    def _get_beginning_of_weeks(
            self,
            calendar_current_week_in_year: int,
            timetable_current_week: int,
            last_week: int
    ) -> Dict[int, datetime.date]:
        begin = calendar_current_week_in_year - timetable_current_week
        weeks = {i: self._get_start_week_by_number(begin + i) for i in range(1, last_week + 1)}
        return weeks

    def _get_current_week_in_year(self) -> int:
        return datetime.datetime.now().isocalendar()[1]

    def _week_day_to_number(self, day: str) -> int:
        return WEEK_DAY.index(day)

    def _get_template_event_object(
            self,
            name: str,
            auditory: List[str],
            lecturers: List[str],
            year: int,
            month: int,
            day: int,
            begin_hour: int,
            begin_minute: int,
            end_hour: int,
            end_minute: int
    ) -> Event:
        begin = datetime.datetime(
            year=year,
            month=month,
            day=day,
            hour=begin_hour,
            minute=begin_minute,
            tzinfo=tzlocal()
        )
        end = datetime.datetime(
            year=year,
            month=month,
            day=day,
            hour=end_hour,
            minute=end_minute,
            tzinfo=tzlocal()
        )
        return Event(
            name=name,
            location=f'НГТУ {" ".join(auditory)}' if auditory else '',
            description=f'Преподователи: {" ".join(lecturers)}' if lecturers else '',
            begin=begin,
            end=end
        )

    def _generate_events_by_lesson(self, lesson: LessonStruct) -> List[Event]:

        def gen_events(weeks: Dict[int, datetime.date], lesson: LessonStruct) -> List[Event]:
            events: List[Event] = []
            for week_number, begin_week in weeks.items():
                week_offset = self._week_day_to_number(lesson.day)
                delta = datetime.timedelta(days=week_offset)
                lesson_date = begin_week + delta
                event = self._get_template_event_object(
                    name=lesson.name,
                    auditory=lesson.auditory,
                    lecturers=lesson.lecturers,
                    year=lesson_date.year,
                    month=lesson_date.month,
                    day=lesson_date.day,
                    begin_hour=lesson.start_time.hour,
                    begin_minute=lesson.start_time.minute,
                    end_hour=lesson.end_time.hour,
                    end_minute=lesson.end_time.minute
                )
                events.append(event)
            return events
        if (self._subgroup and lesson.sub_group == self._subgroup) or not lesson.sub_group:
            if lesson.week:
                weeks = {week_number: self._beginning_of_weeks[week_number] for week_number in lesson.week}
                events = gen_events(weeks, lesson)
                return events
            elif lesson.even:
                weeks = self._even_weeks if lesson.even == 'Ч' else self._not_even_weeks
                events = gen_events(weeks, lesson)
                return events
            else:
                events = gen_events(self._beginning_of_weeks, lesson)
                return events
        else:
            return [Event()]

    def get_events(self) -> Calendar:
        for lesson in self._data:
            events = self._generate_events_by_lesson(lesson)
            for event in events:
                self._calendar.events.add(event)
        return self._calendar


def main():
    t = TimeTableToIcs(url="https://ciu.nstu.ru/student/time_table_view?idgroup=33276&fk_timetable=40006&nomenu=1&print=1", subgroup=1)
    cal = t.get_events()
    print(cal)
    with open("test.ics", "w") as file:
        file.writelines(cal)


if __name__ == '__main__':
    main()
