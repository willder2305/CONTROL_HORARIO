#define MyAppName "Control Horario Biometric Agent"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Control Horario"
#define MyAppExeName "ControlHorarioBiometricAgent.exe"

[Setup]
AppId={{6F58D8D8-B293-4D65-A1F1-C6B6D1F0C950}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={pf32}\ControlHorarioBiometricAgent
DefaultGroupName=Control Horario
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=ControlHorarioBiometricAgent-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x86 x64
ArchitecturesInstallIn64BitMode=
UninstallDisplayName=Control Horario Biometric Agent
CloseApplications=yes
SetupLogging=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Dirs]
Name: "{commonappdata}\ControlHorarioBiometricAgent"
Name: "{commonappdata}\ControlHorarioBiometricAgent\logs"
Name: "{app}\bridge"
Name: "{app}\scripts"

[Files]
Source: "..\bin\ControlHorarioBiometricAgent.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\bin\bridge\Zk9500Bridge.exe"; DestDir: "{app}\bridge"; Flags: ignoreversion
Source: "..\appsettings.example.json"; DestDir: "{commonappdata}\ControlHorarioBiometricAgent"; DestName: "appsettings.json"; Flags: ignoreversion onlyifdoesntexist
Source: "..\appsettings.example.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\scripts\install-startup.ps1"; DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "..\scripts\uninstall-startup.ps1"; DestDir: "{app}\scripts"; Flags: ignoreversion
Source: "..\scripts\start-agent.ps1"; DestDir: "{app}\scripts"; Flags: ignoreversion

[Run]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\scripts\install-startup.ps1"""; Flags: runhidden waituntilterminated
Filename: "{app}\ControlHorarioBiometricAgent.exe"; Description: "Iniciar agente biometrico"; Flags: nowait runhidden postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\WindowsPowerShell\v1.0\powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -File ""{app}\scripts\uninstall-startup.ps1"""; Flags: runhidden waituntilterminated
