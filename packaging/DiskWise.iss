#define MyAppNameZh "磁盘智理"
#define MyAppNameEn "DiskWise"
#define MyAppVersion "1.0.0"
#define MyAppExeName "DiskWise.exe"

[Setup]
AppId={{C72DBFB2-81A5-49E4-B32A-BBF7BFE6D9AF}
AppName={#MyAppNameZh} ({#MyAppNameEn})
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\DiskWise
DefaultGroupName={#MyAppNameZh}
OutputDir=..\installer-output
OutputBaseFilename=DiskWise-Setup-{#MyAppVersion}
SetupIconFile=..\assets\diskwise.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest

[Files]
Source: "..\dist\DiskWise\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppNameZh}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppNameZh}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式 / Create a desktop shortcut"; GroupDescription: "附加选项 / Additional options:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppNameZh}"; Flags: nowait postinstall skipifsilent
