# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['graphsh/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['gremlinpython', 'neo4j', 'boto3', 'prompt_toolkit', 'rich', 'click', 'pydantic', 'rdflib', 'pygments'],
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
    a.binaries,
    a.datas,
    [],
    name='graphsh',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
