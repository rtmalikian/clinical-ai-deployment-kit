"""Backup + restore drill (stdlib only).

Creates a timestamped .tar.gz of a source directory with a SHA-256
manifest, and restores it verifying every file hash — the restore
drill evidence artefact for HIPAA 164.308(a)(7) contingency planning
and SOC 2 CC7.4. Retention helper prunes backups older than N days.
"""
from __future__ import annotations
import hashlib, json, tarfile, time
from pathlib import Path

def _sha(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""): h.update(chunk)
    return h.hexdigest()

def create_backup(source: str|Path, dest_dir: str|Path, label: str="backup") -> Path:
    source, dest_dir = Path(source), Path(dest_dir); dest_dir.mkdir(parents=True, exist_ok=True)
    stamp=time.strftime("%Y%m%dT%H%M%S")
    archive=dest_dir/f"{label}-{stamp}.tar.gz"
    manifest={}
    files=[p for p in source.rglob("*") if p.is_file() and ".venv" not in p.parts and "__pycache__" not in p.parts]
    for p in files: manifest[str(p.relative_to(source))]=_sha(p)
    with tarfile.open(archive,"w:gz") as tar:
        for rel in manifest: tar.add(source/rel, arcname=rel)
        info=tarfile.TarInfo("MANIFEST.json"); data=json.dumps(manifest,indent=2).encode()
        info.size=len(data)
        import io; tar.addfile(info, io.BytesIO(data))
    return archive

def restore_backup(archive: str|Path, dest: str|Path) -> dict:
    dest=Path(dest); dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive,"r:gz") as tar:
        manifest=json.loads(tar.extractfile("MANIFEST.json").read())
        tar.extractall(dest)  # trusted local archive created by create_backup
    (dest/"MANIFEST.json").unlink(missing_ok=True)
    verified=0; mismatched=[]
    for rel, expected in manifest.items():
        p=dest/rel
        if not p.exists() or _sha(p)!=expected: mismatched.append(rel)
        else: verified+=1
    return {"files": len(manifest), "verified": verified, "mismatched": mismatched, "ok": not mismatched}

def prune_old_backups(dest_dir: str|Path, retention_days: int, now: float|None=None) -> list[str]:
    now = now or time.time(); removed=[]
    for p in Path(dest_dir).glob("*.tar.gz"):
        if now - p.stat().st_mtime > retention_days*86400:
            p.unlink(); removed.append(p.name)
    return removed
