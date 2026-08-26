from __future__ import annotations

from pathlib import Path

from axe_playwright_python.sync_playwright import Axe
from axe_playwright_python.base import AxeResults
from playwright.sync_api import Page

# The Revised Section 508 standards (36 CFR 1194.1, Appendix A) incorporate
# WCAG 2.1 Level A and AA success criteria by reference. These are the
# axe-core rule tags that correspond to a VPAT 2.4 508 + WCAG (Revised 508)
# edition scan.
WCAG_508_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]

# axe-core's four impact levels, least to most severe.
IMPACT_LEVELS = ["minor", "moderate", "serious", "critical"]

RESULTS_DIR = Path(__file__).resolve().parent.parent / "test-results" / "axe"

_AXE = Axe()


def scan(page: Page, name: str, context: str | list | dict | None = None) -> AxeResults:
    """Run an axe-core scan of the current page state, scoped to WCAG 2.1 A/AA.

    Persists the full result set (violations, passes, incomplete,
    inapplicable) as JSON under test-results/axe/<name>.json, regardless of
    whether the caller asserts on it. That directory is uploaded as a CI
    artifact, so every scan is retained as evidence for the ACR even when a
    test doesn't fail.
    """
    # The app's layout wraps every route in a .fadeIn opacity transition
    # (assets/styles/transitions.css, 0.5s), applied uniformly regardless of
    # how the page was reached. A caller's "content is ready" wait (e.g.
    # waiting for a heading's text) can resolve well before that animation
    # finishes, and scanning mid-fade catches real elements at reduced
    # opacity, which axe correctly reports as failing color-contrast even
    # though the final, settled state is fine. Wait for in-flight
    # animations/transitions to finish before scanning, so results reflect
    # the real rendered page rather than an animation-timing artifact.
    page.evaluate(
        "() => Promise.all(document.getAnimations().map((a) => a.finished)).catch(() => {})"
    )
    results = _AXE.run(
        page,
        context=context,
        options={"runOnly": {"type": "tag", "values": WCAG_508_TAGS}},
    )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    results.save_to_file(RESULTS_DIR / f"{name}.json")
    return results


def assert_no_violations(
    page: Page,
    name: str,
    context: str | list | dict | None = None,
    allowed_rule_ids: tuple[str, ...] = (),
    min_impact: str = "serious",
) -> AxeResults:
    """Scan the page and fail the test on WCAG 2.1 A/AA violations at or
    above `min_impact`.

    `min_impact` defaults to "serious" -- axe-core's impact levels, least to
    most severe, are minor/moderate/serious/critical. "serious"/"critical"
    are the ones that actually block a screen reader or keyboard user
    (unlabeled controls, invalid ARIA, unreachable content); "minor"/
    "moderate" (e.g. borderline contrast ratios) are recorded in the saved
    JSON but don't fail the test on their own.

    `allowed_rule_ids` is only for specific, already-tracked findings (name
    the backlog item in a comment at the call site) -- not a general escape
    hatch for making a test pass.
    """
    threshold = IMPACT_LEVELS.index(min_impact)
    results = scan(page, name, context=context)
    violations = [
        v
        for v in results.response["violations"]
        if v["id"] not in allowed_rule_ids
        and IMPACT_LEVELS.index(v["impact"]) >= threshold
    ]
    if violations:
        ids = ", ".join(f"{v['id']} ({v['impact']})" for v in violations)
        filtered_report = AxeResults(
            {**results.response, "violations": violations}
        ).generate_report()
        raise AssertionError(
            f"{name}: {len(violations)} unresolved WCAG 2.1 A/AA violation(s) at "
            f"{min_impact}+ impact: {ids}\n"
            f"Full scan (including any below-threshold findings) saved to "
            f"{RESULTS_DIR / f'{name}.json'}\n\n"
            f"{filtered_report}"
        )
    return results
