"""Helper khusus audit: pembaca data (dari pipeline.readers), penulisan laporan, dan tabel Markdown."""
import numpy as np

from pipeline.readers import *  # noqa: F401,F403
from pipeline.readers import ROOT

REPORTS = ROOT / "pipeline" / "audit" / "reports"


def to_markdown(frame, index=False, floatfmt="{:.1f}"):
    """Tabel Markdown sederhana tanpa dependensi tambahan."""
    frame = frame.reset_index() if index else frame
    header = "| " + " | ".join(str(c) for c in frame.columns) + " |"
    divider = "| " + " | ".join("---" for _ in frame.columns) + " |"
    lines = [header, divider]
    for _, row in frame.iterrows():
        cells = []
        for value in row:
            if isinstance(value, (float, np.floating)):
                cells.append("" if np.isnan(value) else floatfmt.format(value))
            else:
                cells.append(str(value))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_report(name, text):
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / name).write_text(text, encoding="utf-8")
    print(f"ditulis: pipeline/audit/reports/{name}")
