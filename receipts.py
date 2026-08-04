"""Local receipt-file storage for the native Expense App Desktop."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from app_paths import user_data_dir


ALLOWED_RECEIPT_TYPES = {
    ".pdf": "PDF",
    ".png": "PNG image",
    ".jpg": "JPEG image",
    ".jpeg": "JPEG image",
    ".webp": "WebP image",
    ".bmp": "Bitmap image",
    ".tif": "TIFF image",
    ".tiff": "TIFF image",
}
MAX_RECEIPT_BYTES = 25 * 1024 * 1024


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _has_expected_signature(path: Path, suffix: str) -> bool:
    with path.open("rb") as source:
        header = source.read(16)
    if suffix == ".pdf":
        return header.startswith(b"%PDF-")
    if suffix == ".png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    if suffix in {".jpg", ".jpeg"}:
        return header.startswith(b"\xff\xd8\xff")
    if suffix == ".webp":
        return header.startswith(b"RIFF") and header[8:12] == b"WEBP"
    if suffix == ".bmp":
        return header.startswith(b"BM")
    if suffix in {".tif", ".tiff"}:
        return header.startswith((b"II*\x00", b"MM\x00*"))
    return False


def _display_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


class ReceiptStore:
    """Copies validated receipt files into the per-user app-data directory."""

    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else user_data_dir() / "receipts"
        self.manifest_path = self.root / "receipts.json"

    def _load_manifest(self) -> list[dict]:
        if not self.manifest_path.exists():
            return []
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return data if isinstance(data, list) else []

    def _save_manifest(self, entries: list[dict]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.manifest_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        os.replace(temporary, self.manifest_path)

    def import_files(self, paths) -> dict[str, list[str]]:
        """Import files and return user-facing imported, skipped, and failed messages."""
        result = {"imported": [], "skipped": [], "failed": []}
        entries = self._load_manifest()
        known_digests = {entry.get("sha256") for entry in entries}
        self.root.mkdir(parents=True, exist_ok=True)

        for raw_path in paths:
            source = Path(raw_path)
            try:
                if not source.is_file():
                    raise ValueError("file does not exist")
                suffix = source.suffix.lower()
                if suffix not in ALLOWED_RECEIPT_TYPES:
                    raise ValueError("only PDF and supported image files are allowed")
                size = source.stat().st_size
                if not size:
                    raise ValueError("file is empty")
                if size > MAX_RECEIPT_BYTES:
                    raise ValueError("file is larger than 25 MB")
                if not _has_expected_signature(source, suffix):
                    raise ValueError("file content does not match its extension")
                digest = _file_digest(source)
            except (OSError, ValueError) as error:
                result["failed"].append(f"{source.name}: {error}")
                continue

            if digest in known_digests:
                result["skipped"].append(f"{source.name}: already uploaded")
                continue

            stored_name = f"{digest[:16]}{suffix}"
            destination = self.root / stored_name
            try:
                temporary = self.root / f".{stored_name}.uploading"
                shutil.copyfile(source, temporary)
                os.replace(temporary, destination)
                entries.append({
                    "original_name": source.name,
                    "stored_name": stored_name,
                    "type": ALLOWED_RECEIPT_TYPES[suffix],
                    "uploaded_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
                    "size_bytes": size,
                    "sha256": digest,
                })
                self._save_manifest(entries)
                known_digests.add(digest)
                result["imported"].append(source.name)
            except OSError as error:
                temporary = self.root / f".{stored_name}.uploading"
                temporary.unlink(missing_ok=True)
                result["failed"].append(f"{source.name}: could not be stored ({error})")
        return result

    def list_receipts(self) -> list[dict]:
        entries = []
        for entry in self._load_manifest():
            stored_name = entry.get("stored_name")
            if not isinstance(stored_name, str) or not (self.root / stored_name).is_file():
                continue
            entries.append({
                "File name": entry.get("original_name", stored_name),
                "Type": entry.get("type", "Unknown"),
                "Uploaded": entry.get("uploaded_at", ""),
                "Size": _display_size(int(entry.get("size_bytes", 0))),
                "Stored name": stored_name,
            })
        return sorted(entries, key=lambda entry: entry["Uploaded"], reverse=True)

    def receipt_path(self, entry: dict) -> Path | None:
        stored_name = entry.get("Stored name")
        path = self.root / str(stored_name) if stored_name else None
        return path if path and path.is_file() else None
