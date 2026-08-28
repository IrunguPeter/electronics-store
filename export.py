import csv

from paths import EXPORT_DIR

OUT_DIR = EXPORT_DIR


def _ensure_outdir():
    OUT_DIR.mkdir(exist_ok=True)


def export_csv(filename, headers, rows):
    """Write rows (list of tuples) to a CSV, return full path."""
    _ensure_outdir()
    path = OUT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
    return path


def export_pdf(title, sections, path=None):
    """Build a simple PDF report.

    sections = list of (heading, [ (col1, col2, ...), ... ])
    Uses reportlab if available, else falls back to CSV.
    Returns path actually written.
    """
    _ensure_outdir()
    if path is None:
        path = OUT_DIR / "report.pdf"

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import (
            Table,
            TableStyle,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
        )
    except ImportError:
        # Fallback: write a CSV named report.csv
        fallback = OUT_DIR / "report.csv"
        export_csv("report.csv", [], [])
        return fallback

    doc = SimpleDocTemplate(str(path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

    for heading, rows in sections:
        story.append(Paragraph(heading, styles["Heading2"]))
        if rows:
            data = [list(row) for row in rows]
            table = Table(data)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                            colors.HexColor("#f8f9fa"),
                            colors.white,
                        ]),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ]
                )
            )
            story.append(table)
        story.append(Spacer(1, 16))

    doc.build(story)
    return path
