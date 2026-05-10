; MED9.1 ECU Konfigurator - Inno Setup Script
; Wird von GitHub Actions automatisch kompiliert

#define MyAppName      "MED9.1 ECU Konfigurator"
#define MyAppVersion   "1.0.0"
#define MyAppExeName   "MED91_Konfigurator.exe"

[Setup]
AppId={{A3F2C891-7B4E-4D1A-B582-EC9D3F1A7C24}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher=ECU Tools

; Installation ohne Admin in den Benutzerordner
DefaultDirName={localappdata}\MED91_Konfigurator
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest

; Ausgabe
OutputDir=installer_output
OutputBaseFilename=MED91_Konfigurator_Setup_v{#MyAppVersion}

; Kompression
Compression=lzma2/ultra64
SolidCompression=yes

; Mindest-Windows: 10
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Wizard-Optik
WizardStyle=modern
WizardSizePercent=120
DisableWelcomePage=no

; Haftungsausschluss
LicenseFile=WARNUNG.rtf

[Languages]
Name: "german";  MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Die fertige EXE aus dem PyInstaller-Build
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Startmenü
Name: "{group}\{#MyAppName}";                    Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; Desktop (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
