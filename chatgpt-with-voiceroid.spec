# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['src\\chatgpt-with-voiceroid\\chatgpt-with-voiceroid.py'],
             pathex=['src\\chatgpt-with-voiceroid'],
             binaries=[],
             datas=[('src\\chatgpt-with-voiceroid\\LICENSE', 'LICENSE')],
             hiddenimports=['tiktoken_ext.openai_public', 'tiktoken_ext'],
             hookspath=[],
             hooksconfig={},
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
          name='chatgpt-with-voiceroid',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None , version='src\\chatgpt-with-voiceroid\\file_version_info.txt', icon='src\\chatgpt-with-voiceroid\\icon.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='chatgpt-with-voiceroid')
