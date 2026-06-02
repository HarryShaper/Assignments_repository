#define MyAppName "ShowTools"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "ShaperVFX"
#define MyAppExeName "ShowTools.exe"

[Setup]
AppId={{7A8E0F28-8D7B-4B83-9D83-SHOWTOOLS001}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\..\dist_installer
OutputBaseFilename=ShowTools_Setup_v1.0.0
SetupIconFile=showtools.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Files]
Source: "..\..\dist\ShowTools\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "showtools.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{userdesktop}\ShowTools"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\showtools.ico"; Tasks: desktopicon
Name: "{group}\ShowTools"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\showtools.ico"
Name: "{usersendto}\ShowTools"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\showtools.ico"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch ShowTools"; Flags: nowait postinstall skipifsilent