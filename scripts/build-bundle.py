"""Build a local developer-skill download from the exact reviewed generic payload."""
import hashlib
import json
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

root = Path(__file__).resolve().parents[1]
pilot = json.loads((root / "pilot.json").read_text())
evidence = json.loads((root / "test/evidence" / f"pilot-{pilot['version']}.json").read_text())
assert evidence["summary"]["allInstructionChecksPassed"], "Resolve recorded failures before bundling"
paths = sorted(evidence["finalSourcePaths"])
assert len(paths) == len(set(paths))
files = {}
snapshot = hashlib.sha256()
for name in paths:
    path = PurePosixPath(name)
    assert not path.is_absolute() and ".." not in path.parts
    assert name in ("SKILL.md", "pilot.json") or (
        len(path.parts) == 2 and path.parts[0] == "references" and path.suffix == ".md"
    ), f"Not a generic skill payload file: {name}"
    content = (root / name).read_bytes()
    files[name] = content
    snapshot.update(name.encode() + b"\0" + content + b"\0")
assert snapshot.hexdigest() == evidence["finalSnapshotSha256"], "Sources changed since review"
assert hashlib.sha256((root / "PERSONAL-SECURITY-GUIDE.md").read_bytes()).hexdigest() == evidence["finalGuideSha256"]

out = root / "downloads"
out.mkdir(exist_ok=True)
archive = out / "personal-security-developer-skill.zip"
with ZipFile(archive, "w", compression=ZIP_DEFLATED) as bundle:
    for name, content in files.items():
        info = ZipInfo("personal-security/" + name, date_time=(2020, 1, 1, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        bundle.writestr(info, content)
with ZipFile(archive) as bundle:
    assert bundle.testzip() is None
    assert sorted(bundle.namelist()) == ["personal-security/" + name for name in paths]
    for name, content in files.items():
        assert bundle.read("personal-security/" + name) == content

manifest = {
    "version": pilot["version"],
    "scope": "Local fictional-rehearsal package; not a public release or security certification.",
    "snapshotSha256": snapshot.hexdigest(),
    "guideSha256": evidence["finalGuideSha256"],
    "archive": archive.name,
    "archiveSha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
    "files": {name: hashlib.sha256(content).hexdigest() for name, content in files.items()},
}
(out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(f"Built and verified {archive.relative_to(root)}: {len(files)} generic files; no research, logs or reports.")
