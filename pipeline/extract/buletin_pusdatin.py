"""Extract Buletin Konsumsi Pangan (Pusdatin Kementan) dari satudata.pertanian.go.id.

Daftar publikasi dicrawl dari https://satudata.pertanian.go.id/datasets/publikasi (halaman
berurutan, lima item per halaman), semua judul "Buletin Konsumsi Pangan" diambil, lalu PDF
tiap edisi diunduh dari halaman detailnya. Nama file PDF di server berupa hash, jadi nama
lokal memakai ID publikasi dan judul.

Hasil di data/raw/buletin/pdf/. Ekstraksi tabel prognosa dikerjakan di buletin_tables.py.
Jalankan:  python -m pipeline.extract.buletin_pusdatin [--refresh]
"""
import argparse
import re
import time

from bs4 import BeautifulSoup

from pipeline.extract.common import RAW_DIR, new_session, request_with_retry, save_raw, target_path

SITE = "https://satudata.pertanian.go.id"
LISTING = SITE + "/datasets/publikasi"
OUT = RAW_DIR / "buletin" / "pdf"
PAUSE_SECONDS = 0.5
PAGE_STEP = 5


def list_bulletins(session):
    """Crawl semua halaman listing, kembalikan {id_publikasi: judul} untuk Buletin Konsumsi Pangan."""
    found = {}
    offset = 0
    last_offset = None
    while last_offset is None or offset <= last_offset:
        url = LISTING + (f"/{offset}" if offset else "")
        soup = BeautifulSoup(request_with_retry(session, "GET", url).text, "lxml")
        if last_offset is None:  # tautan "Last" memuat offset halaman terakhir
            last = soup.find("a", string=re.compile("Last"))
            last_offset = int(last["href"].rstrip("/").split("/")[-1]) if last else 0
        for link in soup.find_all("a", href=re.compile(r"/details/publikasi/\d+")):
            title = re.sub(r"\s+", " ", link.get_text(" ", strip=True))
            if title.lower().startswith("buletin konsumsi pangan"):
                found[int(link["href"].rstrip("/").split("/")[-1])] = title
        offset += PAGE_STEP
        time.sleep(PAUSE_SECONDS)
    return found


def slugify(title):
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


def main():
    parser = argparse.ArgumentParser(description="Unduh Buletin Konsumsi Pangan ke data/raw/buletin")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    session = new_session()
    bulletins = list_bulletins(session)
    print(f"{len(bulletins)} edisi ditemukan")

    for publication_id, title in sorted(bulletins.items()):
        path = target_path(OUT / f"{publication_id}_{slugify(title)}.pdf", args.refresh)
        if path is None:
            continue
        detail_url = f"{SITE}/details/publikasi/{publication_id}"
        detail = request_with_retry(session, "GET", detail_url).text
        pdf_links = re.findall(r"https?://[^\"'\s]+\.pdf", detail)
        if not pdf_links:
            print(f"  tidak ada tautan PDF: {title}")
            continue
        pdf = request_with_retry(session, "GET", pdf_links[0], timeout=300)
        save_raw(
            path,
            pdf.content,
            "buletin_pusdatin",
            {"detail_url": detail_url, "pdf_url": pdf_links[0], "title": title, "publication_id": publication_id},
        )
        print(f"{title}: {len(pdf.content) / 1e6:.1f} MB")
        time.sleep(PAUSE_SECONDS)


if __name__ == "__main__":
    main()
