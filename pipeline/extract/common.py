"""Helper yang dipakai semua script extract: request dengan retry dan penulisan file raw + metadata."""
import hashlib
import json
import time
from datetime import date
from pathlib import Path

import requests

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
EXTRACTION_DATE = date.today()

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; cabai-price-spike research pipeline)"}


def new_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def request_with_retry(session, method, url, retries=4, backoff=8, timeout=120, **kwargs):
    """Request dengan retry untuk timeout, error jaringan, 429 dan 5xx. Jeda naik tiap percobaan."""
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            response = session.request(method, url, timeout=timeout, **kwargs)
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(f"HTTP {response.status_code}", response=response)
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            last_error = error
            if attempt < retries:
                wait = backoff * attempt
                print(f"  percobaan {attempt}/{retries} gagal ({error}); ulang dalam {wait} detik")
                time.sleep(wait)
    raise RuntimeError(f"Gagal setelah {retries} percobaan: {url}") from last_error


def save_raw(path, content, source, request, n_rows=None, notes=None):
    """Simpan respons apa adanya, plus sidecar <nama>.meta.json (D-14).

    File yang sudah ada tidak pernah ditimpa. Extract ulang dengan --refresh
    menulis file baru dengan tanggal extraction di nama file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        content = content.encode("utf-8")
    # tulis ke file sementara lalu ganti nama, supaya sesi yang terputus tidak meninggalkan file setengah jadi
    temp_path = path.with_name(path.name + ".part")
    temp_path.write_bytes(content)
    temp_path.replace(path)

    meta = {
        "source": source,
        "extraction_date": EXTRACTION_DATE.isoformat(),
        "request": request,
        "n_rows": n_rows,
        "n_bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }
    if notes:
        meta["notes"] = notes
    meta_path = path.with_name(path.name + ".meta.json")  # ditulis terakhir: tanda bahwa file lengkap
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def is_valid(path):
    """File raw dianggap valid kalau sidecar ada, hash cocok, dan JSON-nya bisa dibaca."""
    path = Path(path)
    meta_path = path.with_name(path.name + ".meta.json")
    if not path.exists() or not meta_path.exists():
        return False
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        content = path.read_bytes()
        if not content or hashlib.sha256(content).hexdigest() != meta["sha256"]:
            return False
        if path.suffix == ".json":
            json.loads(content)
        return True
    except (ValueError, KeyError, OSError):
        return False


def target_path(path, refresh=False):
    """Path tujuan penulisan, atau None kalau potongan ini sudah ada dan valid (dilewati).

    File yang ada tapi rusak (tanpa sidecar, hash tidak cocok) ditulis ulang.
    Dengan refresh=True file lama dibiarkan dan hasil baru memakai tanggal extraction di nama.
    """
    path = Path(path)
    if refresh:
        return path.with_name(f"{path.stem}__{EXTRACTION_DATE:%Y%m%d}{path.suffix}") if path.exists() else path
    return None if is_valid(path) else path
