import unittest
from datetime import date, timedelta
from xml.etree import ElementTree

from update_profile import parse_calendar, render_heatmap, render_terminal


TODAY = date(2026, 10, 23)


def calendar_fixture():
    start = TODAY - timedelta(days=369)
    cells = []
    for index in range(370):
        current = start + timedelta(days=index)
        count = 12 if index == 369 else 0
        label = f"{count} contributions on October 23rd." if count else "No contributions on October 19th."
        cells.append(
            f'<td id="day-{index}" data-date="{current}" data-level="{4 if count else 0}"></td>'
            f'<tool-tip for="day-{index}">{label}</tool-tip>'
        )
    return "".join(cells)


class ProfileTests(unittest.TestCase):
    def test_real_counts_dates_and_valid_svg(self):
        days = parse_calendar(calendar_fixture(), TODAY)
        self.assertEqual(len(days), 370)
        self.assertEqual(sum(day["count"] for day in days), 12)
        self.assertEqual(days[-1]["date"], TODAY.isoformat())
        for source in (render_terminal(), render_heatmap(days, TODAY)):
            root = ElementTree.fromstring(source)
            self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
            self.assertNotIn("<script", source)
            self.assertNotIn("https://", source)
            self.assertIn("prefers-reduced-motion", source)

    def test_thousands_in_tooltips(self):
        source = calendar_fixture().replace("12 contributions", "1,234 contributions")
        self.assertEqual(parse_calendar(source, TODAY)[-1]["count"], 1234)

    def test_missing_tooltips_and_stale_data_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "count missing"):
            parse_calendar(calendar_fixture().replace('for="day-369"', 'for="missing"'), TODAY)
        with self.assertRaisesRegex(ValueError, "stale"):
            parse_calendar(calendar_fixture(), TODAY + timedelta(days=3))
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            parse_calendar("<html>GitHub temporarily unavailable</html>", TODAY)

    def test_gaps_are_rejected(self):
        source = calendar_fixture().replace('data-date="2026-10-22"', 'data-date="2026-10-21"')
        with self.assertRaisesRegex(ValueError, "gaps or duplicate"):
            parse_calendar(source, TODAY)


if __name__ == "__main__":
    unittest.main()
