# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/opdscli/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'opdscli',
        'opdscli.cli',
        'opdscli.config',
        'opdscli.http',
        'opdscli.opds',
        'opdscli.commands',
        'opdscli.commands.catalog',
        'opdscli.commands.search',
        'opdscli.commands.latest',
        'opdscli.commands.download',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='opdscli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
