import pytest

from spiffworkflow_backend.services.natural_language_time_range_service import NaturalLanguageTimeRangeService


def test_resolves_completed_shorthand_range_in_browser_time_zone() -> None:
    result = NaturalLanguageTimeRangeService.resolve(
        expression="12-1",
        reference_instant="2026-08-30T18:00:00Z",
        time_zone="America/New_York",
        date_order="MDY",
        prefer_completed_range=True,
    )

    assert result == {
        "status": "valid",
        "value": {
            "expression": "12-1",
            "start": "2026-08-30T16:00:00Z",
            "end": "2026-08-30T17:00:00Z",
            "time_zone": "America/New_York",
        },
        "assumptions": ["assuming PM", "today"],
    }


def test_propagates_meridiem_and_resolves_relative_date() -> None:
    result = NaturalLanguageTimeRangeService.resolve(
        expression="9-11:30am yesterday",
        reference_instant="2026-08-30T18:00:00Z",
        time_zone="America/New_York",
        date_order="MDY",
        prefer_completed_range=True,
    )

    assert result == {
        "status": "valid",
        "value": {
            "expression": "9-11:30am yesterday",
            "start": "2026-08-29T13:00:00Z",
            "end": "2026-08-29T15:30:00Z",
            "time_zone": "America/New_York",
        },
        "assumptions": ["assuming start is AM"],
    }


def test_resolves_configured_short_date_to_most_recent_occurrence() -> None:
    result = NaturalLanguageTimeRangeService.resolve(
        expression="3-5 8/12",
        reference_instant="2026-08-30T18:00:00Z",
        time_zone="America/New_York",
        date_order="MDY",
        prefer_completed_range=True,
    )

    assert result == {
        "status": "valid",
        "value": {
            "expression": "3-5 8/12",
            "start": "2026-08-12T19:00:00Z",
            "end": "2026-08-12T21:00:00Z",
            "time_zone": "America/New_York",
        },
        "assumptions": ["assuming PM", "assuming year 2026"],
    }


def test_rolls_explicit_overnight_range_into_the_following_day() -> None:
    result = NaturalLanguageTimeRangeService.resolve(
        expression="23:00-01:00 yesterday",
        reference_instant="2026-08-30T18:00:00Z",
        time_zone="America/New_York",
        date_order="MDY",
        prefer_completed_range=True,
    )

    assert result == {
        "status": "valid",
        "value": {
            "expression": "23:00-01:00 yesterday",
            "start": "2026-08-30T03:00:00Z",
            "end": "2026-08-30T05:00:00Z",
            "time_zone": "America/New_York",
        },
        "assumptions": ["overnight into the following day"],
    }


def test_rejects_nonexistent_daylight_saving_time() -> None:
    result = NaturalLanguageTimeRangeService.resolve(
        expression="2:30am-3:30am 3/8/2026",
        reference_instant="2026-03-09T12:00:00Z",
        time_zone="America/New_York",
        date_order="MDY",
    )

    assert result == {
        "status": "invalid",
        "errors": [
            {
                "code": "nonexistent_local_time",
                "message": "That local time does not exist because the clock moves forward.",
            }
        ],
    }


def test_requires_exact_choice_for_duplicated_daylight_saving_time() -> None:
    result = NaturalLanguageTimeRangeService.resolve(
        expression="1am-2am 11/1/2026",
        reference_instant="2026-11-02T12:00:00Z",
        time_zone="America/New_York",
        date_order="MDY",
    )

    assert result == {
        "status": "ambiguous",
        "errors": [
            {
                "code": "ambiguous_local_time",
                "message": "That local time occurs twice because the clock moves backward; use exact editing.",
            }
        ],
    }


@pytest.mark.parametrize(
    ("expression", "reference_instant", "time_zone", "expected_start", "expected_end"),
    [
        ("12-1", "2026-08-30T18:00:00Z", "America/New_York", "2026-08-30T16:00:00Z", "2026-08-30T17:00:00Z"),
        (
            "9-11:30am yesterday",
            "2026-08-30T18:00:00Z",
            "America/New_York",
            "2026-08-29T13:00:00Z",
            "2026-08-29T15:30:00Z",
        ),
        ("3-5 8/12", "2026-08-30T18:00:00Z", "America/New_York", "2026-08-12T19:00:00Z", "2026-08-12T21:00:00Z"),
        (
            "3am-5am 8/12",
            "2026-08-30T18:00:00Z",
            "America/New_York",
            "2026-08-12T07:00:00Z",
            "2026-08-12T09:00:00Z",
        ),
        (
            "23:00-01:00 yesterday",
            "2026-08-30T18:00:00Z",
            "America/New_York",
            "2026-08-30T03:00:00Z",
            "2026-08-30T05:00:00Z",
        ),
        ("12-1", "2026-08-30T11:00:00Z", "Europe/Helsinki", "2026-08-30T09:00:00Z", "2026-08-30T10:00:00Z"),
        (
            "9-11:30am yesterday",
            "2026-08-30T11:00:00Z",
            "Europe/Helsinki",
            "2026-08-29T06:00:00Z",
            "2026-08-29T08:30:00Z",
        ),
        ("3-5 8/12", "2026-08-30T11:00:00Z", "Europe/Helsinki", "2026-08-12T12:00:00Z", "2026-08-12T14:00:00Z"),
        (
            "3am-5am 8/12",
            "2026-08-30T11:00:00Z",
            "Europe/Helsinki",
            "2026-08-12T00:00:00Z",
            "2026-08-12T02:00:00Z",
        ),
        (
            "23:00-01:00 yesterday",
            "2026-08-30T11:00:00Z",
            "Europe/Helsinki",
            "2026-08-29T20:00:00Z",
            "2026-08-29T22:00:00Z",
        ),
    ],
)
def test_fixed_interpretation_corpus_in_multiple_zones(
    expression: str,
    reference_instant: str,
    time_zone: str,
    expected_start: str,
    expected_end: str,
) -> None:
    result = NaturalLanguageTimeRangeService.resolve(
        expression=expression,
        reference_instant=reference_instant,
        time_zone=time_zone,
        date_order="MDY",
        prefer_completed_range=True,
    )

    assert result["status"] == "valid"
    assert result["value"]["start"] == expected_start
    assert result["value"]["end"] == expected_end


def test_prefers_yesterday_daytime_over_today_overnight_before_range_finishes() -> None:
    result = NaturalLanguageTimeRangeService.resolve(
        expression="12-1",
        reference_instant="2026-08-30T14:00:00Z",
        time_zone="America/New_York",
        date_order="MDY",
        prefer_completed_range=True,
    )

    assert result["status"] == "valid"
    assert result["value"]["start"] == "2026-08-29T16:00:00Z"
    assert result["value"]["end"] == "2026-08-29T17:00:00Z"
    assert result["assumptions"] == ["assuming PM", "yesterday"]


def test_rejects_ranges_longer_than_configured_maximum() -> None:
    result = NaturalLanguageTimeRangeService.resolve(
        expression="1am-10pm today",
        reference_instant="2026-08-30T23:00:00Z",
        time_zone="America/New_York",
        maximum_hours=16,
    )

    assert result == {
        "status": "invalid",
        "errors": [{"code": "range_too_long", "message": "The time range cannot be longer than 16 hours."}],
    }


@pytest.mark.parametrize(
    ("expression", "expected_start", "expected_end"),
    [
        ("9-11am Aug 12", "2026-08-12T13:00:00Z", "2026-08-12T15:00:00Z"),
        ("09:00-11:00 2026-08-12", "2026-08-12T13:00:00Z", "2026-08-12T15:00:00Z"),
    ],
)
def test_resolves_named_and_iso_dates(expression: str, expected_start: str, expected_end: str) -> None:
    result = NaturalLanguageTimeRangeService.resolve(
        expression=expression,
        reference_instant="2026-08-30T18:00:00Z",
        time_zone="America/New_York",
        date_order="MDY",
    )

    assert result["status"] == "valid"
    assert result["value"]["start"] == expected_start
    assert result["value"]["end"] == expected_end


def test_rolls_range_with_explicit_meridiems_overnight() -> None:
    result = NaturalLanguageTimeRangeService.resolve(
        expression="11pm-1am yesterday",
        reference_instant="2026-08-30T18:00:00Z",
        time_zone="America/New_York",
    )

    assert result["status"] == "valid"
    assert result["value"]["start"] == "2026-08-30T03:00:00Z"
    assert result["value"]["end"] == "2026-08-30T05:00:00Z"
    assert result["assumptions"] == ["overnight into the following day"]


def test_honors_dmy_short_date_configuration() -> None:
    result = NaturalLanguageTimeRangeService.resolve(
        expression="3-5 12/8",
        reference_instant="2026-08-30T18:00:00Z",
        time_zone="America/New_York",
        date_order="DMY",
    )

    assert result["status"] == "valid"
    assert result["value"]["start"] == "2026-08-12T19:00:00Z"
    assert result["value"]["end"] == "2026-08-12T21:00:00Z"
