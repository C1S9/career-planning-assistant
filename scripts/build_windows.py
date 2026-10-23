"""Build, smoke-test, and package the Windows app from public files only."""

import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from version import __version__


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def make_icon(path):
    from PIL import Image, ImageDraw
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    drawing = ImageDraw.Draw(image)
    drawing.rounded_rectangle((8, 8, 248, 248), radius=58, fill="#246B5C")
    drawing.ellipse((48, 48, 208, 208), outline="#DFEEE5", width=8)
    drawing.polygon([(163, 81), (143, 143), (81, 163), (108, 108)], fill="#FFFFFF")
    drawing.polygon([(163, 81), (143, 143), (108, 108)], fill="#C9DED2")
    image.save(path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def copy_license_notices(bundle):
    """Keep dependency notices without choosing a license for the owner's code."""
    destination = bundle / "dependency-licenses"
    destination.mkdir(exist_ok=True)
    lines = ["Third-party dependency notices", "", "Application license selection is separate from these dependency licenses.", ""]
    for distribution in sorted(metadata.distributions(), key=lambda item: item.metadata.get("Name", "").lower()):
        name = distribution.metadata.get("Name", "unknown")
        license_name = distribution.metadata.get("License-Expression") or distribution.metadata.get("License") or "See bundled metadata/notices"
        lines.append(f"{name} {distribution.version}: {license_name.splitlines()[0]}")
        for relative in distribution.files or ():
            basename = Path(str(relative)).name.lower()
            if basename.startswith(("license", "copying", "notice")):
                source = Path(distribution.locate_file(relative))
                if source.is_file() and source.stat().st_size < 2_000_000:
                    target = destination / name / Path(str(relative)).name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if python_license.is_file():
        shutil.copyfile(python_license, destination / "Python-LICENSE.txt")
    (bundle / "THIRD_PARTY_NOTICES.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    if platform.system() != "Windows" or platform.machine().upper() not in {"AMD64", "X86_64"}:
        raise SystemExit("Build this Windows x64 package using a Windows x64 Python interpreter.")
    work = ROOT / "build/windows"
    release = ROOT / "release"
    work.mkdir(parents=True, exist_ok=True)
    release.mkdir(exist_ok=True)
    make_icon(work / "app.ico")
    if not args.skip_build:
        subprocess.run([
            sys.executable, "-m", "PyInstaller", "--noconfirm", "--distpath", str(ROOT / "dist"),
            "--workpath", str(work / "pyinstaller"), str(ROOT / "packaging/windows.spec"),
        ], cwd=ROOT, check=True)
    bundle = ROOT / "dist/LifeDirectionAgent"
    executable = bundle / "LifeDirectionAgent.exe"
    if not executable.is_file():
        raise SystemExit("No built Windows executable was found.")
    report_path = work / "smoke-result.json"
    environment = os.environ.copy()
    for name in ("DEEPSEEK_API_KEY", "DEEPSEEK_MODEL", "GITHUB_TOKEN", "GH_TOKEN", "PYTHONPATH", "PYTHONHOME"):
        environment.pop(name, None)
    # Only Windows system commands are on PATH: the frozen smoke test must not
    # accidentally depend on this computer's external Python installation.
    environment["PATH"] = str(Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32")
    environment["PYTHONNOUSERSITE"] = "1"
    subprocess.run([
        str(executable), "--self-test", "--data-dir", str(work / "smoke data"), "--report", str(report_path),
    ], cwd=work, env=environment, check=True, timeout=180)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not report.get("ok") or report.get("version") != __version__:
        raise SystemExit("The packaged application did not pass its isolated smoke test.")
    shutil.copyfile(ROOT / "docs/WINDOWS_QUICKSTART.md", bundle / "START_HERE.txt")
    copy_license_notices(bundle)
    source_files = ["app.py", "agent.py", "models.py", "prompts.py", "mentors.py", "version.py", "desktop.py", ".streamlit/config.toml", "requirements.txt",
                    "evidence.py", "references.py", "search_topics.py", "coaching_skills.py", "permissions.py"]
    source_files += [f"skills/{name}/SKILL.md" for name in ("evidence-informed-coaching", "mentor-decision-workflow", "realistic-action-planning")]
    manifest = {"version": __version__, "python": platform.python_version(), "architecture": "windows-x64", "source_sha256": {name: digest(ROOT / name) for name in source_files}, "smoke_test": report, "credentials_included": False}
    (bundle / "BUILD_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    forbidden = {"secrets.toml", ".env", "learner-profile.md"}
    for path in bundle.rglob("*"):
        if path.is_file() and (path.name in forbidden or path.name.startswith("secrets.toml.")):
            raise SystemExit("A private filename was found in the distributable; packaging stopped.")
    archive = release / f"LifeDirectionAgent-v{__version__}-windows-x64.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipped:
        for path in sorted(bundle.rglob("*")):
            if path.is_file():
                zipped.write(path, path.relative_to(bundle.parent))
    checksum = digest(archive)
    (release / "SHA256SUMS.txt").write_text(f"{checksum}  {archive.name}\n", encoding="utf-8")
    (release / "BUILD_REPORT.json").write_text(json.dumps({**manifest, "archive": archive.name, "archive_bytes": archive.stat().st_size, "archive_sha256": checksum}, indent=2), encoding="utf-8")
    print(json.dumps({"version": __version__, "archive": str(archive), "archive_bytes": archive.stat().st_size, "sha256": checksum, "smoke_test": report}, indent=2))


if __name__ == "__main__":
    main()
