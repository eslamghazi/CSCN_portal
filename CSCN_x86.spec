# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['uvicorn.loops.asyncio', 'uvicorn.protocols.http.h11_impl', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan.on', 'multipart', 'sqlalchemy.dialects.sqlite']
hiddenimports += collect_submodules('api')
hiddenimports += collect_submodules('application')
hiddenimports += collect_submodules('infrastructure')
hiddenimports += collect_submodules('domain')
hiddenimports += collect_submodules('config')
hiddenimports += collect_submodules('database')
hiddenimports += collect_submodules('uvicorn')


a = Analysis(
    ['web_main.py'],
    pathex=[],
    binaries=[],
    datas=[('.env', '.'), ('frontend\\dist', 'frontend\\dist'), ('ui\\resources\\fonts', 'ui\\resources\\fonts'), ('ui\\resources\\icons', 'ui\\resources\\icons')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CSCN_x86',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['ui\\resources\\icons\\app.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='CSCN_x86',
)
