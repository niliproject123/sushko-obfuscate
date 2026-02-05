# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Sushko desktop app.

Run from the project root:
    pyinstaller desktop/sushko.spec
"""

import os
from pathlib import Path

block_cipher = None
root = Path(SPECPATH).parent  # project root

a = Analysis(
    [str(root / 'desktop' / 'launcher.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[
        # Frontend static build
        (str(root / 'static'), 'static'),
        # Backend config (settings.json etc.)
        (str(root / 'api' / 'config'), os.path.join('api', 'config')),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'api',
        'api.main',
        'api.routes',
        'api.routes.extract',
        'api.routes.config',
        'api.processors',
        'api.processors.pdf_processor',
        'api.detectors',
        'api.obfuscators',
        'api.config',
        'api.config.loader',
        'api.storage',
        'api.storage.temp',
        'multipart',
        'pytesseract',
        'pdf2image',
        'pdfplumber',
        'fitz',
        'PIL',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy.testing'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='sushko',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Show console so user can see server status
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='sushko',
)
