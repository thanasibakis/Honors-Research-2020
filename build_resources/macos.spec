# -*- mode: python ; coding: utf-8 -*-

from datetime import datetime

block_cipher = None


a = Analysis(['../src/app.py'],
             pathex=['./lib'],
             binaries=[],
             datas=[('../src/data/simdata.pckl', '.')],
             hiddenimports=['scipy.special.cython_special', 'pkg_resources.py2_warn'],
             hookspath=['./hooks'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='MUGIC Plot',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='MUGIC Plot')
app = BUNDLE(coll,
             name=f'MUGIC Plot {dt.date(dt.now())}.app',
             icon=None,
             bundle_identifier=None)
