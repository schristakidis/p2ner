
[Setup]
AppName=P2ner
AppVersion=0.3
DefaultDirName={pf}\P2ner
DefaultGroupName=P2ner
UninstallDisplayIcon={app}\P2ner.exe
Compression=lzma2
SolidCompression=yes
OutputDir=.

[Files]
Source: "win32\dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\P2NER"; Filename: "{app}\P2ner.exe"

