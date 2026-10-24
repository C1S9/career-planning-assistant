# -*- mode: python ; coding: utf-8 -*-
"""Freeze an explicit public-file allowlist; never collect the project directory."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

root = Path(SPECPATH).parent
public_modules = ("app.py", "agent.py", "models.py", "prompts.py", "mentors.py", "version.py",
                  "evidence.py", "references.py", "search_topics.py", "coaching_skills.py", "permissions.py",
                  "student_tools.py", "student_market.py", "student_ui.py")
datas = [(str(root / name), "application") for name in public_modules]
datas += [(str(root / ".streamlit/config.toml"), "application/.streamlit")]
for name in ("evidence-informed-coaching", "mentor-decision-workflow", "realistic-action-planning"):
    datas.append((str(root / "skills" / name / "SKILL.md"), "application/skills/" + name))
datas += collect_data_files("streamlit", includes=["static/**"])
datas += copy_metadata("streamlit", recursive=True)
datas += copy_metadata("openai", recursive=True)

hiddenimports = ["agent", "models", "prompts", "mentors", "version", "evidence", "references", "search_topics", "coaching_skills", "permissions", "student_tools", "student_market", "student_ui"]
hiddenimports += collect_submodules("streamlit", filter=lambda name: not name.startswith(("streamlit.testing", "streamlit.hello")))
hiddenimports += [
    "uvicorn.logging", "uvicorn.loops.auto", "uvicorn.loops.asyncio",
    "uvicorn.protocols.http.auto", "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets.auto", "uvicorn.protocols.websockets.websockets_impl",
    "uvicorn.protocols.websockets.websockets_sansio_impl", "uvicorn.lifespan.on", "uvicorn.lifespan.off",
]

analysis = Analysis(
    [str(root / "desktop.py")], pathex=[str(root)], binaries=[], datas=datas,
    hiddenimports=hiddenimports, hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=["streamlit.testing", "streamlit.hello", "pytest", "IPython", "matplotlib", "scipy"],
    noarchive=False, optimize=1,
)
archive = PYZ(analysis.pure)
executable = EXE(
    archive, analysis.scripts, [], exclude_binaries=True, name="LifeDirectionAgent",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, disable_windowed_traceback=False,
    version=str(root / "packaging/windows_version_info.txt"),
    icon=str(root / "build/windows/app.ico"),
)
collection = COLLECT(executable, analysis.binaries, analysis.datas, strip=False, upx=False, name="LifeDirectionAgent")
