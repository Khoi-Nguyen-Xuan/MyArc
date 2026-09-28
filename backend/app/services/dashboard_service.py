from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.course_codes import normalize_course_title
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


WEEKS_SHOWN = 8


def get_current_state(db: Session, user_id: int) -> DashboardCurrentStateResponse:
    courses = db.query(Course).filter(Course.user_id == user_id).all()
    today = date.today()
    this_monday = today - timedelta(days=today.weekday())
    window_end = this_monday + timedelta(weeks=WEEKS_SHOWN)  # exclusive

    # flatten every course's assessments into (course_name, type, score_percent, date),
    # keeping only the ones due in the next WEEKS_SHOWN weeks (today included)
    flat: list[dict] = []
    undated = 0
    for course in courses:
        for item in course.assessments or []:
            item_date = _parse_assessment_date(item.get("date"))
            if item_date is None:
                undated += 1
                continue
            if item_date < today or item_date >= window_end:
                continue
            flat.append(
                {
                    "course_name": normalize_course_title(course.course_name or "") or "Untitled course",
                    "type": item.get("type", "assessment"),
                    "score_percent": item.get("score_percent", 0.0),
                    "date": item_date,
                }
            )

    # always return WEEKS_SHOWN consecutive Mon-Sun weeks, empty ones included,
    # so the frontend can draw a continuous 8-week strip
    by_week: dict[date, dict[date, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for entry in flat:
        d = entry["date"]
        by_week[d - timedelta(days=d.weekday())][d].append(entry)

    week_entries: list[WeekEntry] = []
    for i in range(WEEKS_SHOWN):
        week_start = this_monday + timedelta(weeks=i)
        days = by_week.get(week_start, {})
        date_entries = [
            DateEntry(
                date=d,
                course_test=[
                    CourseTestItem(course_name=e["course_name"], type=e["type"], score_percent=e["score_percent"])
                    for e in days[d]
                ],
            )
            for d in sorted(days)
        ]
        week_entries.append(
            WeekEntry(start_date=week_start, end_date=week_start + timedelta(days=6), dates=date_entries)
        )

    if not flat:
        return DashboardCurrentStateResponse(
            overload="Low",
            priority_course="",
            busiest_upcoming_week="",
            current_course_tracking=len(courses),
            undated_assessments=undated,
            upcoming_weeks=week_entries,
        )

    # busiest = most grade weight due in one week
    def week_weight(week: WeekEntry) -> float:
        return sum(t.score_percent for de in week.dates for t in de.course_test)

    busiest = max(week_entries, key=week_weight)
    busiest_weight = week_weight(busiest)
    busiest_str = f"{busiest.start_date.isoformat()} to {busiest.end_date.isoformat()}"

    if busiest_weight >= 0.25:
        overload = "High"
    elif busiest_weight >= 0.10:
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
        undated_assessments=undated,
        upcoming_weeks=week_entries,
    )
