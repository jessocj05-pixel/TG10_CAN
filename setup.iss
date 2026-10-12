[Setup]
AppName=TG10 Control
AppVersion=1.0
DefaultDirName={autopf}\TG10 Control
DefaultGroupName=TG10 Control
OutputDir=installer_output
OutputBaseFilename=TG10_Control_Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\TG10_Control.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "drivers\CH341SER.EXE"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\TG10 Control"; Filename: "{app}\TG10_Control.exe"
Name: "{autodesktop}\TG10 Control"; Filename: "{app}\TG10_Control.exe"

[Run]
Filename: "{tmp}\CH341SER.EXE"; Description: "Install USB-CAN driver (CH341SER)"; Flags: postinstall skipifsilent runascurrentuser
Filename: "{app}\TG10_Control.exe"; Description: "Launch TG10 Control"; Flags: postinstall nowait skipifsilent unchecked