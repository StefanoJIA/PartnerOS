# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec: FastAPI sidecar (D3). Prefer building in a clean venv (see docs/testing.md)."""

import os
from pathlib import Path

from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis

ROOT = Path(os.path.dirname(os.path.abspath(SPECPATH))).resolve()
if not (ROOT / "sidecar_entry.py").exists():
    ROOT = (ROOT / "backend").resolve()
if not (ROOT / "sidecar_entry.py").exists():
    raise RuntimeError(f"sidecar_entry.py not found; tried under {ROOT}")

# Uvicorn worker stacks are imported lazily — pin them for one-file bundles.
hiddenimports = [
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "passlib.handlers.bcrypt",
]

block_cipher = None

STOP_THE_BLEED_EXCLUDES = [
    "torch",
    "torchvision",
    "tensorflow",
    "IPython",
    "jupyter",
    "jupyterlab",
    "notebook",
    "matplotlib",
    "sphinx",
    "transformers",
    "sklearn",
    "pandas",
    "scipy",
    "bokeh",
    "dask",
    "detectron2",
    "bitsandbytes",
    "tensorflow",
    "tkinter",
    "pytest",
]

a = Analysis(
    [str(ROOT / "sidecar_entry.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=STOP_THE_BLEED_EXCLUDES,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="intellioffice-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_trace=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
