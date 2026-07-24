#define MyAppName "Odysseus"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Odysseus"
#define MyAppExeName "Odysseus.cmd"

[Setup]
AppId={{B03F8AF9-D8B5-4A3F-A81B-5D6E778F76AA}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Odysseus
DefaultGroupName=Odysseus
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename=Odysseus-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "..\..\dist\app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Odysseus"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Odysseus"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[UninstallDelete]
; User data under %LOCALAPPDATA%\Odysseus is intentionally preserved.
