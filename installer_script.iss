#define MyAppName "Project Parallel"
#define MyAppPublisher "JoaoLendengues"
#define MyAppURL "https://github.com/JoaoLendengues/PROJECT_PARALLELv2"

#ifndef MyAppVersion
  #define MyAppVersion "1.1.7"
#endif

#ifndef BuildRoot
  #define BuildRoot "desktop\output\main"
#endif

[Setup]
AppId={{3D50B072-6E6D-4A85-A7A2-3EE33F1D6CB1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\ProjectParallel
DefaultGroupName={#MyAppName}
UsePreviousAppDir=yes
AllowNoIcons=yes
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=ProjectParallel_Setup_v{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\main.exe
CloseApplications=force
RestartApplications=no

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar icone na Area de Trabalho"; GroupDescription: "Icones adicionais:"
Name: "startmenuicon"; Description: "Criar icone no Menu Iniciar"; GroupDescription: "Icones adicionais:"; Flags: unchecked

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "{#BuildRoot}\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#BuildRoot}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "desktop\.env"; DestDir: "{app}"; DestName: ".env"; Flags: ignoreversion onlyifdoesntexist uninsneveruninstall skipifsourcedoesntexist

[Icons]
Name: "{group}\Project Parallel"; Filename: "{app}\main.exe"
Name: "{autodesktop}\Project Parallel"; Filename: "{app}\main.exe"; Tasks: desktopicon
Name: "{group}\Desinstalar Project Parallel"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\main.exe"; Description: "Executar Project Parallel agora"; Flags: postinstall nowait skipifsilent
