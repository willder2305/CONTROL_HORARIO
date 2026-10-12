; Instalador Inno Setup del agente biometrico local.
; El script requiere que build-installer.ps1 prepare local-agent\runtime\appsettings.json fuera del control de versiones.
#define MyAppName "Control Horario Biometric Agent"
#define MyAppVersion "1.0.3"
#define MyAppPublisher "Control Horario"
#define MyAppExeName "ControlHorarioBiometricAgent.exe"

[Setup]
AppId={{6F58D8D8-B293-4D65-A1F1-C6B6D1F0C950}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={commonpf32}\ControlHorarioBiometricAgent
DefaultGroupName=Control Horario
DisableProgramGroupPage=yes
OutputDir=..\..\output\biometric-agent
OutputBaseFilename=ControlHorarioBiometricAgent-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x86 x64compatible
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
Source: "..\..\backend\zk9500_bridge\bin\*"; DestDir: "{app}\bridge"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\runtime\appsettings.json"; DestDir: "{commonappdata}\ControlHorarioBiometricAgent"; DestName: "appsettings.json"; Flags: ignoreversion onlyifdoesntexist
Source: "..\appsettings.example.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\scripts\start-agent.ps1"; DestDir: "{app}\scripts"; Flags: ignoreversion

[Registry]
Root: HKLM; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "ControlHorarioBiometricAgent"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue

[Run]
Filename: "{app}\{#MyAppExeName}"; Flags: nowait runhidden postinstall skipifsilent

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    { Elimina la tarea defectuosa creada por versiones anteriores. }
    Exec(ExpandConstant('{sys}\schtasks.exe'), '/Delete /TN "ControlHorarioBiometricAgent" /F', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  end;
end;
