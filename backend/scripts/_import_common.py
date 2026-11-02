"""Helpers shared by the winery data import scripts."""

import io
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DATA_DIR = Path(__file__).parent.parent / "data"
_XLSX_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def read_source(file: Path | None, url: str) -> bytes:
    return file.read_bytes() if file else fetch(url)


def resolve_dsn(dsn: str | None) -> str:
    if dsn:
        return dsn
    from app.core.config import get_settings
    return get_settings().DATABASE_URL


def make_session(dsn: str):
    engine = create_async_engine(dsn, echo=False, pool_pre_ping=True)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


def read_xlsx(content: bytes) -> dict[str, list[dict]]:
    """Read every sheet as a list of {header: value} rows, using the first row as headers."""
    archive = zipfile.ZipFile(io.BytesIO(content))
    strings = [
        "".join(t.text or "" for t in item.iter(f"{_XLSX_NS}t"))
        for item in ET.fromstring(archive.read("xl/sharedStrings.xml"))
    ]
    sheets = {}
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    for position, sheet in enumerate(workbook.find(f"{_XLSX_NS}sheets"), start=1):
        rows = []
        data = ET.fromstring(archive.read(f"xl/worksheets/sheet{position}.xml")).find(f"{_XLSX_NS}sheetData")
        for row in data:
            cells = {}
            for cell in row:
                value = cell.find(f"{_XLSX_NS}v")
                if value is not None:
                    column = re.match("[A-Z]+", cell.get("r")).group()
                    cells[column] = strings[int(value.text)] if cell.get("t") == "s" else value.text
            rows.append(cells)
        headers = rows[0] if rows else {}
        sheets[sheet.get("name")] = [
            {headers.get(column, column): value for column, value in row.items()} for row in rows[1:]
        ]
    return sheets
