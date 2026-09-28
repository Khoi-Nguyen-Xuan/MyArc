from datetime import date as date_type

from pydantic import BaseModel


class CourseTestItem(BaseModel):
    course_name: str
    type: str
    score_percent: float


class DateEntry(BaseModel):
    date: date_type
    course_test: list[CourseTestItem]


class WeekEntry(BaseModel):
    start_date: date_type
    end_date: date_type
    dates: list[DateEntry]


class DashboardCurrentStateResponse(BaseModel):
    overload: str
    priority_course: str
    busiest_upcoming_week: str
    current_course_tracking: int
    # assessments the syllabus gave no date for; they can't be placed on the calendar
    undated_assessments: int = 0
    upcoming_weeks: list[WeekEntry]
