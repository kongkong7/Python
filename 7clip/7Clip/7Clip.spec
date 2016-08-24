# -*- mode: python -*-

block_cipher = None


a = Analysis(['7Clip.py'],
             pathex=['D:\\04_Study\\Python\\7clip\\7Clip'],
             binaries=None,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='7Clip',
          debug=False,
          strip=False,
          upx=True,
          console=True )
