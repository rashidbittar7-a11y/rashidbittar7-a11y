"""Build a terminal-style profile using public GitHub data and the standard library."""

import json
import re
from datetime import date, datetime, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
USERNAME = "rashidbittar7-a11y"
PALETTE = ("#192322", "#164936", "#217a50", "#32b774", "#78e4a0")
FONT = "Consolas, 'Liberation Mono', monospace"
# Dark colours are written inline; the light variant swaps each one (GitHub picks via prefers-color-scheme).
LIGHT = {
    "#0d1416": "#f7f9f8", "#2a3739": "#d3dcda", "#4b6263": "#a9b7b5", "#78e4a0": "#17794a",
    "#93a8a7": "#4f6463", "#718988": "#5c706f", "#c9d4d3": "#2b3635", "#d7e5e1": "#1f2a29",
    "#edf5f2": "#0f1716", "#48645c": "#9fb3ad", "#192322": "#e3e9e7", "#164936": "#a6e3bd",
    "#217a50": "#5cc48a", "#32b774": "#2e9e62", "#1d2a2b": "#eef2f1",
}
STACK = ("JavaScript", "TypeScript", "Node.js", "SQLite", "HTML", "CSS", "REST-APIs", "Python", "Git", "GitHub Actions")


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.tooltips = {}
        self.tooltip_id = None
        self.tooltip_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("td", "rect") and "data-date" in attrs:
            self.cells[attrs["id"]] = {
                "date": attrs["data-date"], "level": int(attrs["data-level"])
            }
        if tag == "tool-tip" and attrs.get("for"):
            self.tooltip_id = attrs["for"]
            self.tooltip_text = []

    def handle_data(self, data):
        if self.tooltip_id:
            self.tooltip_text.append(data)

    def handle_endtag(self, tag):
        if tag == "tool-tip" and self.tooltip_id:
            self.tooltips[self.tooltip_id] = "".join(self.tooltip_text).strip()
            self.tooltip_id = None


def parse_calendar(source, today):
    parser = CalendarParser()
    parser.feed(source)
    days = []
    for cell_id, cell in parser.cells.items():
        text = parser.tooltips.get(cell_id, "")
        match = re.match(r"([\d,]+) contributions? on\b", text)
        if text.startswith("No contributions on "):
            count = 0
        elif match:
            count = int(match[1].replace(",", ""))
        else:
            raise ValueError(f"Contribution count missing for {cell['date']}")
        if cell["level"] not in range(5) or (count == 0) != (cell["level"] == 0):
            raise ValueError("Invalid contribution intensity")
        date.fromisoformat(cell["date"])
        days.append({**cell, "count": count})
    days.sort(key=lambda day: day["date"])
    if not 365 <= len(days) <= 371:
        raise ValueError("Incomplete GitHub calendar; existing graphics were kept")
    dates = [date.fromisoformat(day["date"]) for day in days]
    if any((b - a).days != 1 for a, b in zip(dates, dates[1:])):
        raise ValueError("Calendar has gaps or duplicate dates")
    if not 0 <= (today - dates[-1]).days <= 2:
        raise ValueError("GitHub calendar is stale or in the future")
    return days


def svg_document(width, height, title, description, content, extra_css=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title>
<desc id="desc">{escape(description)}</desc>
<style>
text {{ font-family: {FONT}; }}
.line {{ animation: print .55s both; }}
.day {{ animation: appear .35s backwards; }}
@keyframes print {{ from {{ opacity: 0; transform: translateY(5px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes appear {{ from {{ opacity: 0; transform: translateY(-4px); }} to {{ opacity: 1; transform: translateY(0); }} }}
{extra_css}
@media (prefers-reduced-motion: reduce) {{ .line, .day, .ascii-row {{ animation: none !important; }} }}
</style>
<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="14" fill="#0d1416" stroke="#2a3739"/>
{content}
</svg>
'''


def text(x, y, value, size=15, fill="#c9d4d3", attrs=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" {attrs}>{escape(str(value))}</text>'


def chrome(label, width=1000):
    return (
        '<path d="M1 47H999" stroke="#2a3739"/>'
        '<circle cx="25" cy="25" r="4" fill="#4b6263"/>'
        '<circle cx="43" cy="25" r="4" fill="#4b6263"/>'
        '<circle cx="61" cy="25" r="4" fill="#78e4a0"/>'
        + text(86, 30, label, 13, "#93a8a7")
        + text(width - 26, 30, "R / B", 12, "#718988", 'text-anchor="end"')
    )


def render_terminal():
    rows = (ROOT / "portrait.txt").read_text(encoding="ascii").splitlines()
    parts = [chrome("rashid@github: ~ / whoami")]
    parts.append('<path d="M366 80V357" stroke="#2a3739"/>')
    parts.append(text(37, 94, "IDENTITY / 01", 12, "#718988"))
    for index, row in enumerate(rows):
        parts.append(text(
            38, 110 + index * 5, row, 5, "#d7e5e1",
            f'xml:space="preserve" class="ascii-row" style="animation-delay:{index * .018:.2f}s"'
        ))
    parts.extend([
        text(37, 367, "RASHID BITTAR", 14, "#78e4a0"),
        text(407, 105, "rashid@github", 26, "#edf5f2", 'font-weight="700"'),
        text(407, 132, "---------------------------", 16, "#48645c"),
    ])
    fields = [
        ("Name", "Rashid Bittar"),
        ("Fokus", "Webentwicklung"),
        ("Stack", "JavaScript / TypeScript"),
        ("Projekte", "Privat entwickelt"),
        ("Antrieb", "Ideen in Anwendungen verwandeln"),
    ]
    for index, (key, value) in enumerate(fields):
        parts.append(f'<g class="line" style="animation-delay:{.7 + index * .13:.2f}s">')
        parts.append(text(407, 176 + index * 35, key, 16, "#78e4a0"))
        parts.append(text(517, 176 + index * 35, value, 16))
        parts.append('</g>')
    parts.append('<path d="M32 382H968" stroke="#2a3739"/>')
    parts.append(text(37, 418, '~/profile $ build --learn --improve', 16, "#93a8a7", 'class="line" style="animation-delay:1.5s"'))
    css = '''.ascii-row { animation: type .5s both; }
@keyframes type { from { opacity: 0; clip-path: inset(0 100% 0 0); } to { opacity: 1; clip-path: inset(0); } }'''
    return svg_document(
        1000, 450, "Rashid Bittar – Terminal-Profil",
        "ASCII-Porträt aus dem öffentlichen GitHub-Avatar. Rashid Bittar, Webentwicklung mit JavaScript und TypeScript. Projekte werden privat entwickelt.",
        "".join(parts), css
    )


def render_mobile_terminal():
    rows = (ROOT / "portrait.txt").read_text(encoding="ascii").splitlines()
    parts = [
        '<path d="M1 47H639" stroke="#2a3739"/>',
        '<circle cx="25" cy="25" r="4" fill="#78e4a0"/>',
        text(45, 30, "rashid@github: ~ / whoami", 15, "#93a8a7"),
        text(320, 92, "RASHID BITTAR", 24, "#edf5f2", 'text-anchor="middle" font-weight="700"'),
    ]
    for index, row in enumerate(rows):
        parts.append(text(
            140, 124 + index * 6.25, row, 6.25, "#d7e5e1",
            f'xml:space="preserve" class="line" style="animation-delay:{index * .018:.2f}s"'
        ))
    parts.append('<path d="M35 442H605" stroke="#2a3739"/>')
    fields = [
        ("Name", "Rashid Bittar"), ("Fokus", "Webentwicklung"),
        ("Stack", "JavaScript / TypeScript"), ("Projekte", "Privat entwickelt"),
        ("Antrieb", "Ideen in Anwendungen verwandeln"),
    ]
    for index, (key, value) in enumerate(fields):
        parts.append(f'<g class="line" style="animation-delay:{.8 + index * .13:.2f}s">')
        parts.append(text(35, 491 + index * 45, key, 20, "#78e4a0"))
        parts.append(text(165, 491 + index * 45, value, 20))
        parts.append('</g>')
    parts.append('<path d="M35 712H605" stroke="#2a3739"/>')
    parts.append(text(35, 751, "$ build --learn --improve", 21, "#93a8a7"))
    return svg_document(640, 786, "Rashid Bittar – Terminal-Profil", "ASCII-Porträt und Infokarte, für schmale Ansichten.", "".join(parts))


def light(svg):
    return re.sub("|".join(LIGHT), lambda m: LIGHT[m[0]], svg)


def render_stack():
    parts = [chrome("rashid@github: ~ / stack"), text(37, 94, "STACK / 02", 12, "#718988")]
    x, y = 37, 120
    for index, name in enumerate(STACK):
        width = 26 + len(name) * 9
        if x + width > 963:
            x, y = 37, y + 48
        parts.append(
            f'<g class="line" style="animation-delay:{.2 + index * .06:.2f}s">'
            f'<rect x="{x}" y="{y}" width="{width}" height="34" rx="17" fill="#1d2a2b" stroke="#2a3739"/>'
            + text(x + 13, y + 22, name, 15, "#d7e5e1") + '</g>'
        )
        x += width + 10
    parts.append(text(37, y + 78, "~/stack $ lernen, bauen, verbessern", 14, "#93a8a7"))
    return svg_document(1000, y + 104, "Stack von Rashid Bittar", "Technologien: " + ", ".join(STACK) + ".", "".join(parts))


def render_heatmap(days, today):
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    best = max(day["count"] for day in days)
    start = date.fromisoformat(days[0]["date"])
    sunday_offset = (start.weekday() + 1) % 7
    parts = [chrome("rashid@github: ~ / contributions")]
    parts.extend([
        text(36, 96, f"{total:,}".replace(",", "."), 35, "#edf5f2", 'font-weight="700"'),
        text(133, 93, "ÖFFENTLICHE BEITRÄGE", 13, "#93a8a7"),
        text(963, 92, "Stand " + today.strftime("%d.%m.%Y") + " / UTC", 12, "#718988", 'text-anchor="end"'),
    ])
    for row, label in [(1, "Mo"), (3, "Mi"), (5, "Fr")]:
        parts.append(text(35, 150 + row * 16 + 10, label, 11, "#718988"))
    months = ("", "Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez")
    last_month = None
    for index, day in enumerate(days):
        current = date.fromisoformat(day["date"])
        week, row = divmod(index + sunday_offset, 7)
        x, y = 72 + week * 16, 150 + row * 16
        if current.month != last_month and (index == 0 or week > 1):
            parts.append(text(x, 133, months[current.month], 11, "#93a8a7"))
            last_month = current.month
        delay = .15 + week * .018 + row * .035
        parts.append(
            f'<rect class="day" x="{x}" y="{y}" width="12" height="12" rx="2.5" '
            f'fill="{PALETTE[day["level"]]}" style="animation-delay:{delay:.3f}s">'
            f'<title>{current.isoformat()}: {day["count"]} Beiträge</title></rect>'
        )
    parts.append(text(36, 292, f"{active} aktive Tage  /  Bester Tag: {best} Beiträge", 12, "#93a8a7"))
    parts.append(text(802, 291, "Weniger", 10, "#718988"))
    for index, color in enumerate(PALETTE):
        parts.append(f'<rect x="{854 + index * 15}" y="281" width="10" height="10" rx="2" fill="{color}"/>')
    parts.append(text(963, 291, "Mehr", 10, "#718988", 'text-anchor="end"'))
    parts.append(text(36, 330, "Nur öffentlich sichtbare Beiträge. Private Projektdaten bleiben privat.", 11, "#718988"))
    return svg_document(
        1000, 354, "Öffentlicher GitHub-Beitragskalender von Rashid Bittar",
        f"{total} Beiträge im angezeigten GitHub-Kalender, {active} aktive Tage. Stand {today.isoformat()}. Nur öffentliche GitHub-Daten.",
        "".join(parts)
    )


def main():
    today = datetime.now(timezone.utc).date()
    request = Request(
        f"https://github.com/users/{USERNAME}/contributions",
        headers={"User-Agent": "RashidProfileArt/1.0", "Accept-Language": "en-US"},
    )
    # Deliberately unauthenticated: private repository activity is not collected.
    with urlopen(request, timeout=40) as response:
        days = parse_calendar(response.read().decode("utf-8"), today)
    graphics = {
        "terminal": render_terminal(),
        "terminal-mobile": render_mobile_terminal(),
        "stack": render_stack(),
        "contributions": render_heatmap(days, today),
    }
    outputs = {f"{name}.svg": svg for name, svg in graphics.items()}
    outputs.update({f"{name}-light.svg": light(svg) for name, svg in graphics.items()})
    outputs.update({
        "contributions.json": json.dumps({"updated": today.isoformat(), "days": days}, indent=2) + "\n",
    })
    for filename, contents in outputs.items():
        (ROOT / filename).write_text(contents, encoding="utf-8")
    print(f"Generated profile art: {len(days)} days, {sum(day['count'] for day in days)} public contributions")


if __name__ == "__main__":
    main()
