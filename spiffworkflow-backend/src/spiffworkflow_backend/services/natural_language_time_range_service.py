import re
from datetime import date
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError

import dateparser


class NaturalLanguageTimeRangeService:
    TIME_RANGE_PATTERN = re.compile(
        r"^\s*(?P<start_hour>\d{1,2})(?::(?P<start_minute>\d{2}))?\s*"
        r"(?P<start_meridiem>am|pm)?\s*-\s*"
        r"(?P<end_hour>\d{1,2})(?::(?P<end_minute>\d{2}))?\s*"
        r"(?P<end_meridiem>am|pm)?"
        r"(?:\s+(?P<date_text>.+?))?\s*$",
        re.IGNORECASE,
    )

    @classmethod
    def resolve(
        cls,
        *,
        expression: str,
        reference_instant: str,
        time_zone: str,
        date_order: str = "MDY",
        prefer_completed_range: bool = True,
        maximum_hours: int = 16,
    ) -> dict:
        try:
            zone = ZoneInfo(time_zone)
            reference = datetime.fromisoformat(reference_instant.replace("Z", "+00:00")).astimezone(zone)
        except (ValueError, ZoneInfoNotFoundError):
            return cls._invalid("invalid_context", "The reference instant or time zone is invalid.")

        match = cls.TIME_RANGE_PATTERN.fullmatch(expression)
        if match is None:
            return cls._invalid("invalid_expression", "Enter a time range such as 9-11:30am yesterday.")

        start_hour = int(match.group("start_hour"))
        end_hour = int(match.group("end_hour"))
        start_minute = int(match.group("start_minute") or 0)
        end_minute = int(match.group("end_minute") or 0)
        if start_minute > 59 or end_minute > 59:
            return cls._invalid("invalid_time", "Minutes must be between 00 and 59.")

        start_meridiem_text = match.group("start_meridiem")
        end_meridiem_text = match.group("end_meridiem")
        uses_24_hour_time = (
            start_meridiem_text is None
            and end_meridiem_text is None
            and (start_hour == 0 or start_hour > 12 or end_hour == 0 or end_hour > 12)
        )
        allows_overnight = uses_24_hour_time or start_meridiem_text is not None or end_meridiem_text is not None
        if uses_24_hour_time:
            start_meridiems = [None]
            end_meridiems = [None]
        elif start_meridiem_text is None and end_meridiem_text is not None:
            start_meridiems = [end_meridiem_text.lower()]
        else:
            start_meridiems = cls._meridiem_candidates(start_hour, start_meridiem_text)
        if uses_24_hour_time:
            end_meridiems = [None]
        elif end_meridiem_text is None and start_meridiem_text is not None:
            end_meridiems = [start_meridiem_text.lower()]
        else:
            end_meridiems = cls._meridiem_candidates(end_hour, end_meridiem_text)

        date_text = match.group("date_text")
        resolved_date = cls._resolve_date(date_text, reference.date(), date_order)
        if isinstance(resolved_date, dict):
            return resolved_date
        range_date, date_assumptions = resolved_date
        candidates: list[tuple[datetime, datetime, str | None, str | None, bool]] = []
        local_time_errors: set[str] = set()
        range_too_long = False
        range_dates = [range_date]
        if date_text is None and prefer_completed_range:
            range_dates.append(range_date - timedelta(days=1))
        for candidate_date in range_dates:
            for start_meridiem in start_meridiems:
                for end_meridiem in end_meridiems:
                    start, start_error = cls._local_datetime(candidate_date, start_hour, start_minute, start_meridiem, zone)
                    end, end_error = cls._local_datetime(candidate_date, end_hour, end_minute, end_meridiem, zone)
                    if start_error:
                        local_time_errors.add(start_error)
                    if end_error:
                        local_time_errors.add(end_error)
                    rolled_overnight = False
                    if start is not None and end is not None and end <= start and allows_overnight:
                        end += timedelta(days=1)
                        rolled_overnight = True
                    if start is not None and end is not None and end > start:
                        if end - start > timedelta(hours=maximum_hours):
                            range_too_long = True
                            continue
                        if date_text is not None or not prefer_completed_range or end <= reference:
                            candidates.append((start, end, start_meridiem, end_meridiem, rolled_overnight))

        if not candidates:
            if "ambiguous" in local_time_errors:
                return {
                    "status": "ambiguous",
                    "errors": [
                        {
                            "code": "ambiguous_local_time",
                            "message": "That local time occurs twice because the clock moves backward; use exact editing.",
                        }
                    ],
                }
            if "nonexistent" in local_time_errors:
                return cls._invalid(
                    "nonexistent_local_time",
                    "That local time does not exist because the clock moves forward.",
                )
            if range_too_long:
                return cls._invalid(
                    "range_too_long",
                    f"The time range cannot be longer than {maximum_hours} hours.",
                )
            return cls._invalid("unresolved_range", "The time range could not be resolved unambiguously.")

        start, end, start_meridiem, end_meridiem, rolled_overnight = max(
            candidates,
            key=cls._candidate_score,
        )
        assumptions = []
        if start_meridiem_text is None and end_meridiem_text is None:
            if start_meridiem == end_meridiem and start_meridiem is not None:
                assumptions.append(f"assuming {start_meridiem.upper()}")
        elif start_meridiem_text is None:
            assumptions.append(f"assuming start is {start_meridiem.upper()}")
        elif end_meridiem_text is None:
            assumptions.append(f"assuming end is {end_meridiem.upper()}")
        if date_text is None:
            assumptions.append("today" if start.date() == reference.date() else "yesterday")
        assumptions.extend(date_assumptions)
        if rolled_overnight:
            assumptions.append("overnight into the following day")

        return {
            "status": "valid",
            "value": {
                "expression": expression,
                "start": cls._utc_string(start),
                "end": cls._utc_string(end),
                "time_zone": time_zone,
            },
            "assumptions": assumptions,
        }

    @staticmethod
    def _meridiem_candidates(hour: int, meridiem: str | None) -> list[str | None]:
        if meridiem is not None:
            return [meridiem.lower()]
        if hour == 0 or hour > 12:
            return [None]
        return ["am", "pm"]

    @staticmethod
    def _local_datetime(
        range_date: date,
        hour: int,
        minute: int,
        meridiem: str | None,
        zone: ZoneInfo,
    ) -> tuple[datetime | None, str | None]:
        if meridiem is None:
            if hour > 23:
                return None, None
            resolved_hour = hour
        else:
            if hour < 1 or hour > 12:
                return None, None
            resolved_hour = hour % 12 + (12 if meridiem == "pm" else 0)
        local_value = datetime.combine(range_date, datetime.min.time()).replace(hour=resolved_hour, minute=minute)
        candidates: dict[object, datetime] = {}
        for fold in (0, 1):
            aware_value = local_value.replace(tzinfo=zone, fold=fold)
            round_trip = aware_value.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
            if round_trip == local_value:
                candidates[aware_value.utcoffset()] = aware_value
        if not candidates:
            return None, "nonexistent"
        if len(candidates) > 1:
            return None, "ambiguous"
        return next(iter(candidates.values())), None

    @classmethod
    def _resolve_date(cls, date_text: str | None, reference_date: date, date_order: str) -> tuple[date, list[str]] | dict:
        if date_text is None or date_text.lower() == "today":
            return reference_date, []
        if date_text.lower() == "yesterday":
            return reference_date - timedelta(days=1), []

        if date_order not in ("MDY", "DMY", "YMD"):
            return cls._invalid("invalid_date_order", "Date order must be MDY, DMY, or YMD.")

        try:
            return date.fromisoformat(date_text), []
        except ValueError:
            pass

        parts = date_text.split("/")
        if len(parts) not in (2, 3) or any(not part.isdigit() for part in parts):
            parsed_date = dateparser.parse(
                date_text,
                settings={
                    "DATE_ORDER": date_order,
                    "PREFER_DATES_FROM": "past",
                    "RELATIVE_BASE": datetime.combine(reference_date, datetime.min.time()),
                },
            )
            if parsed_date is None:
                return cls._invalid("invalid_date", "Enter today, yesterday, a named date, or an ISO date.")
            assumptions = []
            if re.search(r"\b\d{4}\b", date_text) is None:
                assumptions.append(f"assuming year {parsed_date.year}")
            return parsed_date.date(), assumptions

        values = [int(part) for part in parts]
        assumptions: list[str] = []
        if len(values) == 2:
            if date_order == "YMD":
                return cls._invalid("invalid_date", "YMD dates must include a year.")
            month, day = values if date_order == "MDY" else reversed(values)
            year = reference_date.year
            try:
                resolved = date(year, month, day)
            except ValueError:
                return cls._invalid("invalid_date", "The date is not valid.")
            if resolved > reference_date:
                resolved = date(year - 1, month, day)
            assumptions.append(f"assuming year {resolved.year}")
            return resolved, assumptions

        positions = {part: index for index, part in enumerate(date_order)}
        try:
            return date(values[positions["Y"]], values[positions["M"]], values[positions["D"]]), assumptions
        except ValueError:
            return cls._invalid("invalid_date", "The date is not valid.")

    @staticmethod
    def _utc_string(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    @staticmethod
    def _candidate_score(candidate: tuple[datetime, datetime, str | None, str | None, bool]) -> tuple:
        start, end = candidate[0], candidate[1]
        is_daytime = 6 <= start.hour <= 18 and 7 <= end.hour <= 22
        return is_daytime, end, -(end - start).total_seconds()

    @staticmethod
    def _invalid(code: str, message: str) -> dict:
        return {"status": "invalid", "errors": [{"code": code, "message": message}]}
