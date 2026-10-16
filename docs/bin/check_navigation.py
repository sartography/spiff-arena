#!/usr/bin/env python3
"""Check rendered BPMN navigation: python3 bin/check_navigation.py _build/html."""

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


class SidebarLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_sidebar = False
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "aside" and attrs.get("id") == "docs-sidebar":
            self.in_sidebar = True
        if self.in_sidebar and tag == "a":
            self.links.append(attrs)

    def handle_endtag(self, tag):
        if tag == "aside":
            self.in_sidebar = False


def check(build_dir):
    bpmn = "reference/bpmn/"
    pages = {
        "message_events_vs_tasks": "message_events",
        "exclusive_gateways_example": "gateways",
        "inclusive_gateway_example": "gateways",
        "parallel_gateways_example": "gateways",
    }
    cases = [(bpmn + page, bpmn + parent, bpmn + "index") for page, parent in pages.items()]
    cases.append((
        "how_to_guides/building_diagrams/send_and_receive_messages",
        "how_to_guides/building_diagrams/index",
        "how_to_guides/building_diagrams/index",
    ))
    errors = []
    for page, parent, index in cases:
        for source in set((page, parent, index)):
            parser = SidebarLinks()
            source_file = build_dir / f"{source}.html"
            parser.feed(source_file.read_text(encoding="utf-8"))
            matches = []
            for link in parser.links:
                url = urlsplit(link.get("href", ""))
                target = (source_file.parent / url.path).resolve() if url.path else source_file.resolve()
                if not url.scheme and target == (build_dir / f"{page}.html").resolve() and not url.fragment:
                    matches.append(link)
            if not matches:
                errors.append(f"{source}: missing sidebar page link to {page}")
            if source == page and not any(
                "current" in link.get("class", "").split() for link in matches
            ):
                errors.append(f"{page}: missing current-page sidebar link")
    if errors:
        raise SystemExit("\n".join(errors))
    print("Message guide and BPMN sidebar navigation checks passed (5 pages).")


if __name__ == "__main__":
    check(Path(sys.argv[1] if len(sys.argv) > 1 else "_build/html"))
