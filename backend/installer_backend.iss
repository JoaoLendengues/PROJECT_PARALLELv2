; Script para Inno Setup - Backend do Project Parallel
[Setup]
AppName=Project Parallel Backend
AppVersion=1.0.0
DefaultDirName={pf}\ProjectParallelBackend
DefaultGroupName=Project Parallel
UninstallDisplayIcon={app}\ProjectParallelBackend.exe
Compression=lzma2
SolidCompression=yes
OutputDir=installer
OutputBaseFilename=ProjectParallelBackend_Setup
PrivilegesRequired=admin

[Files]
Source: "dist\ProjectParallelBackend.exe"; DestDir: "{app}"
Source: "..\database\schema.sql"; DestDir: "{app}\database"; Flags: ignoreversion
Source: "..\README.md"; DestDir: "{app}"; Flags: isreadme

[Icons]
Name: "{group}\Project Parallel Backend"; Filename: "{app}\ProjectParallelBackend.exe"
Name: "{group}\Desinstalar"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Project Parallel Backend"; Filename: "{app}\ProjectParallelBackend.exe"

[Run]
Filename: "{app}\ProjectParallelBackend.exe"; Description: "Iniciar Backend do Project Parallel"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
