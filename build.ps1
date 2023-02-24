PyInstaller --noconfirm --clean ".\chatgpt-with-voiceroid.spec"
Remove-Item dist\chatgpt-with-voiceroid.zip
Compress-Archive -Path dist\chatgpt-with-voiceroid -DestinationPath dist\chatgpt-with-voiceroid.zip
Copy-Item src\chatgpt-with-voiceroid\SeikaSay2.exe dist\chatgpt-with-voiceroid\
