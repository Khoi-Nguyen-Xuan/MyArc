from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.course import Course
from app.schemas.dashboard import (
    CourseTestItem,
    DashboardCurrentStateResponse,
    DateEntry,
    WeekEntry,
)


def _parse_assessment_date(raw) -> date | None:
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str):
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return None
    return None


def get_current_state(db: Session, user_id: int) -> DashboardCurrentStateResponse:
    courses = db.query(Course).filter(Course.user_id == user_id).all()
    today = date.today()

    # flatten every course's assessments into (course_name, type, score_percent, date),
    # keeping only today-or-later ones
    flat: list[dict] = []
    for course in courses:
        for item in course.assessments or []:
            item_date = _parse_assessment_date(item.get("date"))
            if item_date is None or item_date < today:
                continue
            flat.append(
                {
                    "course_name": course.course_name or "Untitled course",
                    "type": item.get("type", "assessment"),
                    "score_percent": item.get("score_percent", 0.0),
                    "date": item_date,
                }
            )

    if not flat:
        return DashboardCurrentStateResponse(
            overload="Low",
            priority_course="",
            busiest_upcoming_week="",
            current_course_tracking=len(courses),
            upcoming_weeks=[],
        )

    # group into Mon-Sun weeks, then by exact date within each week
    weeks: dict[date, dict[date, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for entry in flat:
        d = entry["date"]
        week_start = d - timedelta(days=d.weekday())
        weeks[week_start][d].append(entry)

    week_entries: list[WeekEntry] = []
    for week_start in sorted(weeks.keys()):
        week_end = week_start + timedelta(days=6)
        date_entries = []
        for d in sorted(weeks[week_start].keys()):
            course_tests = [
                CourseTestItem(
                    course_name=e["course_name"],
                    type=e["type"],
                    score_percent=e["score_percent"],
                )
                for e in weeks[week_start][d]
            ]
            date_entries.append(DateEntry(date=d, course_test=course_tests))
        week_entries.append(WeekEntry(start_date=week_start, end_date=week_end, dates=date_entries))

    busiest = max(week_entries, key=lambda w: sum(len(de.course_test) for de in w.dates))
    busiest_count = sum(len(de.course_test) for de in busiest.dates)
    busiest_str = f"{busiest.start_date.isoformat()} to {busiest.end_date.isoformat()}"

    if busiest_count >= 3:
        overload = "High"
    elif busiest_count >= 1:
        overload = "Medium"
    else:
        overload = "Low"

    # soonest deadline wins; ties broken by higher weight
    soonest = min(flat, key=lambda e: (e["date"], -e["score_percent"]))

    return DashboardCurrentStateResponse(
        overload=overload,
        priority_course=soonest["course_name"],
        busiest_upcoming_week=busiest_str,
        current_course_tracking=len(courses),
        upcoming_weeks=week_entries,
    )
