# eventsApi.py
import datetime as dt
import os, json
from zoneinfo import ZoneInfo
from typing import Any, Iterable
from dateutil import parser as dtparser  
from google.oauth2 import service_account
from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event

SCOPES = ['https://www.googleapis.com/auth/calendar']
CAL_ID = os.getenv("CALENDAR_ID")
G_SERVICE_JSON = os.getenv("G_SERVICE_JSON")

creds_info = json.loads(G_SERVICE_JSON)
creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)

calendar = GoogleCalendar(CAL_ID, credentials=creds)

REQUIRED_FIELDS = {"summary", "start"}

def _parse_iso(value: str) -> dt.datetime | dt.date:
    return dtparser.isoparse(value)

def _apply_timezone(dt_or_date: dt.datetime | dt.date, tz_name: str | None, all_day: bool):
    if all_day or isinstance(dt_or_date, dt.date) and not isinstance(dt_or_date, dt.datetime):
        return dt_or_date
    d = dt_or_date
    if tz_name:
        tz = ZoneInfo(tz_name)
        if d.tzinfo is None:
            d = d.replace(tzinfo=tz) 
    else:
        if d.tzinfo is None:
            raise ValueError("Время без часового пояса. Добавь 'timezone' или укажи смещение (напр. +01:00).")
    return d

def dict_to_event(payload: dict[str, Any]) -> Event:
    missing = REQUIRED_FIELDS - payload.keys()
    if missing:
        raise ValueError(f"Отсутствуют обязательные поля: {', '.join(missing)}")

    all_day = bool(payload.get("all_day", False))
    tz_name = payload.get("timezone")

    start_raw = payload["start"]
    end_raw = payload.get("end")

    start_parsed = _parse_iso(start_raw)
    end_parsed = _parse_iso(end_raw) if end_raw else None

    start_final = _apply_timezone(start_parsed, tz_name, all_day)
    end_final = _apply_timezone(end_parsed, tz_name, all_day) if end_parsed else None

    if all_day:
        if isinstance(start_final, dt.datetime):
            start_final = start_final.date()
        if end_final is None:
            end_final = start_final
        elif isinstance(end_final, dt.datetime):
            end_final = end_final.date()

    return Event(
        summary=payload["summary"],
        start=start_final,
        end=end_final,
        description=payload.get("description"),
        location=payload.get("location"),
    )

def ensure_iter(obj: Any) -> Iterable[dict]:
    if isinstance(obj, dict):
        return [obj]
    if isinstance(obj, list):
        for i, item in enumerate(obj, 1):
            if not isinstance(item, dict):
                raise ValueError(f"Элемент #{i} не объект JSON.")
        return obj
    raise ValueError("Ожидал JSON-объект или массив объектов.")

def create_event(event: Event):
    return calendar.add_event(event)

def create_events_from_payload(payload: Any) -> tuple[int, list[str]]:
    created = 0
    errors: list[str] = []
    for idx, item in enumerate(ensure_iter(payload), 1):
        try:
            ev = dict_to_event(item)
            calendar.add_event(ev)
            created += 1
        except Exception as e:
            errors.append(f"#{idx}: {e}")
    return created, errors
