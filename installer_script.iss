; Script gerado para o Projeto Parallel
; Estrutura: One Directory (com pasta _internal)
; Usando caminhos relativos para portabilidade

[Setup]
; Informações Básicas do App
AppName=Project Parallel
AppVersion=1.1.7
AppPublisher=JoaoLendengues
AppPublisherURL=https://github.com/JoaoLendengues/PROJECT_PARALLELv2
AppSupportURL=https://github.com/JoaoLendengues/PROJECT_PARALLELv2
DefaultDirName={autopf}\ProjectParallel
DefaultGroupName=Project Parallel
AllowNoIcons=yes
PrivilegesRequired=lowest
OutputDir=installer_output
OutputBaseFilename=ProjectParallel_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\main.exe

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar ícone na Área de Trabalho"; GroupDescription: "Ícones adicionais:"
Name: "startmenuicon"; Description: "Criar ícone no Menu Iniciar"; GroupDescription: "Ícones adicionais:"; Flags: unchecked

[Files]
; ✅ Copia o executável principal (caminho relativo)
Source: "desktop\output\main\main.exe"; DestDir: "{app}"; Flags: ignoreversion

; ✅ Copia a pasta _internal COMPLETA (caminho relativo)
Source: "desktop\output\main\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Ícone do Menu Iniciar
Name: "{group}\Project Parallel"; Filename: "{app}\main.exe"
; Ícone da Área de Trabalho (condicional)
Name: "{autodesktop}\Project Parallel"; Filename: "{app}\main.exe"; Tasks: desktopicon
; Desinstalador
Name: "{group}\Desinstalar Project Parallel"; Filename: "{uninstallexe}"

[Run]
; Executa o app após a instalação
Filename: "{app}\main.exe"; Description: "Executar Project Parallel agora"; Flags: postinstall nowait skipifsilent