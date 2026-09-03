#define MyAppNameZh "文件管家"
#define MyAppNameEn "FileCare"
#define MyAppVersion "1.1.0"
#define MyAppExeName "FileCare.exe"

[Setup]
AppId={{C72DBFB2-81A5-49E4-B32A-BBF7BFE6D9AF}
AppName={#MyAppNameZh} ({#MyAppNameEn})
AppVersion={#MyAppVersion}
AppPublisher=FileCare Contributors
AppPublisherURL=https://github.com/jack3344wong/diskwise
AppSupportURL=https://github.com/jack3344wong/diskwise/issues
AppUpdatesURL=https://github.com/jack3344wong/diskwise/releases
DefaultDirName={autopf}\FileCare
DefaultGroupName={#MyAppNameZh}
DisableProgramGroupPage=yes
OutputDir=..\installer-output
OutputBaseFilename=FileCare-Setup-{#MyAppVersion}
SetupIconFile=..\assets\filecare.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoCompany=FileCare Contributors
VersionInfoDescription=FileCare 文件管家安装程序
VersionInfoProductName={#MyAppNameEn}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoVersion={#MyAppVersion}.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
; 发布目标：Windows 7 SP1 64 位及更新的 64 位 Windows。
MinVersion=6.1sp1
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
; 安装页内嵌动画帧：只解压到临时目录，不会留在用户电脑上。
; 放在实际程序文件之前，避免 SolidCompression 下提前解压时扫描大量数据。
Source: "..\assets\installer\frames\installer-frame-*.png"; Flags: dontcopy noencryption
Source: "..\assets\filecare.ico"; Flags: dontcopy noencryption
Source: "..\dist\FileCare\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppNameZh}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: startmenuicon
Name: "{group}\卸载软件"; Filename: "{uninstallexe}"; IconFilename: "{uninstallexe}"; Tasks: startmenuicon
Name: "{autodesktop}\{#MyAppNameZh}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式 / Create a desktop shortcut"; GroupDescription: "附加选项 / Additional options:"
Name: "startmenuicon"; Description: "创建开始菜单文件夹 / Create a Start Menu folder"; GroupDescription: "附加选项 / Additional options:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Parameters: "--build-name-index --index-budget-seconds 20"; StatusMsg: "正在建立首批文件搜索索引…"; Flags: runhidden waituntilterminated runasoriginaluser
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppNameZh}"; Flags: nowait postinstall skipifsilent

[Code]
const
  AnimationFrameCount = 60;
  AnimationInterval = 140;
  WMSetIcon = $0080;
  IconSmall = 0;
  IconBig = 1;
  ImageIcon = 1;
  LRLoadFromFile = $0010;
  LRDefaultSize = $0040;
  SMCXScreen = 0;
  SMCYScreen = 1;

var
  AnimationFrames: array of TBitmapImage;
  AnimationFrame: Integer;
  AnimationVisibleFrame: Integer;
  AnimationTimer: UINT_PTR;
  AnimationReady, AnimationMode: Boolean;
  InstallerIcon: THandle;
  NormalLeft, NormalTop, NormalWidth, NormalHeight: Integer;
  OuterLeft, OuterTop, OuterWidth, OuterHeight: Integer;
  BevelLeft, BevelTop, BevelWidth, BevelHeight: Integer;
  BackLeft, BackTop, BackWidth, BackHeight: Integer;
  NextLeft, NextTop, NextWidth, NextHeight: Integer;
  CancelLeft, CancelTop, CancelWidth, CancelHeight: Integer;
  NormalBorderStyle: TFormBorderStyle;

function SetTimer(hWnd: HWND; nIDEvent: UINT_PTR; uElapse: UINT;
  lpTimerFunc: NativeInt): UINT_PTR;
external 'SetTimer@user32.dll stdcall';

function KillTimer(hWnd: HWND; uIDEvent: UINT_PTR): BOOL;
external 'KillTimer@user32.dll stdcall';

function LoadImage(hInst: THandle; Name: String; ImageType: UINT;
  CX, CY: Integer; Flags: UINT): THandle;
external 'LoadImageW@user32.dll stdcall';

function SendMessage(hWnd: HWND; Msg: UINT; WParam: NativeUInt;
  LParam: NativeInt): NativeInt;
external 'SendMessageW@user32.dll stdcall';

function DestroyIcon(Icon: THandle): BOOL;
external 'DestroyIcon@user32.dll stdcall';

function GetSystemMetrics(Index: Integer): Integer;
external 'GetSystemMetrics@user32.dll stdcall';

procedure SetInstallerWindowIcon;
begin
  if InstallerIcon <> 0 then
  begin
    SendMessage(WizardForm.Handle, WMSetIcon, IconBig, InstallerIcon);
    SendMessage(WizardForm.Handle, WMSetIcon, IconSmall, InstallerIcon);
  end;
end;

function AnimationFramePath(FrameIndex: Integer): String;
begin
  Result := ExpandConstant('{tmp}\installer-frame-' +
    Format('%.3d', [FrameIndex]) + '.png');
end;

procedure ShowAnimationFrame(FrameIndex: Integer);
begin
  if (not AnimationReady) or (FrameIndex < 0) or
     (FrameIndex >= AnimationFrameCount) then
    Exit;

  { 所有帧已在进入安装页前解码；此处只切换内存图像，避免安装解压时掉帧。 }
  if AnimationVisibleFrame >= 0 then
    AnimationFrames[AnimationVisibleFrame].Visible := False;
  AnimationFrames[FrameIndex].BringToFront;
  AnimationFrames[FrameIndex].Visible := AnimationMode;
  AnimationVisibleFrame := FrameIndex;
end;

procedure AnimationTimerProc(Arg1: HWND; Arg2: UINT;
  Arg3: UINT_PTR; Arg4: DWORD);
begin
  if WizardForm.CurPageID = wpInstalling then
  begin
    AnimationFrame := (AnimationFrame + 1) mod AnimationFrameCount;
    ShowAnimationFrame(AnimationFrame);
  end;
end;

procedure StartAnimation;
begin
  if (not AnimationReady) or (AnimationTimer <> 0) then
    Exit;
  AnimationTimer := SetTimer(0, 0, AnimationInterval,
    CreateCallback(@AnimationTimerProc));
end;

procedure StopAnimation;
begin
  if AnimationTimer <> 0 then
  begin
    KillTimer(0, AnimationTimer);
    AnimationTimer := 0;
  end;
end;

procedure LayoutAnimation;
var
  CardWidth, CardHeight, CardLeft, CardTop: Integer;
begin
  CardWidth := ScaleX(640);
  CardHeight := (CardWidth * 9) div 16;
  CardLeft := (GetSystemMetrics(SMCXScreen) - CardWidth) div 2;
  CardTop := (GetSystemMetrics(SMCYScreen) - CardHeight) div 2;

  WizardForm.BorderStyle := bsNone;
  WizardForm.SetBounds(CardLeft, CardTop, CardWidth, CardHeight);
  WizardForm.Color := clWhite;
  for CardWidth := 0 to AnimationFrameCount - 1 do
    AnimationFrames[CardWidth].SetBounds(
      0, 0, WizardForm.ClientWidth, WizardForm.ClientHeight);
  SetInstallerWindowIcon;
end;

procedure EnterAnimationMode;
begin
  if AnimationMode or (not AnimationReady) then
    Exit;
  AnimationMode := True;

  { 保留同一个安装窗口和任务栏按钮，仅把向导控件移出可视区。 }
  WizardForm.OuterNotebook.Left := -10000;
  WizardForm.Bevel.Left := -10000;
  WizardForm.BackButton.Left := -10000;
  WizardForm.NextButton.Left := -10000;
  WizardForm.CancelButton.Left := -10000;
  LayoutAnimation;
  ShowAnimationFrame(AnimationFrame);
  StartAnimation;
end;

procedure LeaveAnimationMode;
begin
  if not AnimationMode then
    Exit;
  StopAnimation;
  AnimationMode := False;
  if AnimationVisibleFrame >= 0 then
    AnimationFrames[AnimationVisibleFrame].Visible := False;

  WizardForm.BorderStyle := NormalBorderStyle;
  WizardForm.SetBounds(NormalLeft, NormalTop, NormalWidth, NormalHeight);
  WizardForm.OuterNotebook.SetBounds(OuterLeft, OuterTop, OuterWidth, OuterHeight);
  WizardForm.Bevel.SetBounds(BevelLeft, BevelTop, BevelWidth, BevelHeight);
  WizardForm.BackButton.SetBounds(BackLeft, BackTop, BackWidth, BackHeight);
  WizardForm.NextButton.SetBounds(NextLeft, NextTop, NextWidth, NextHeight);
  WizardForm.CancelButton.SetBounds(CancelLeft, CancelTop, CancelWidth, CancelHeight);
  SetInstallerWindowIcon;
end;

procedure InitializeWizard;
begin
  AnimationTimer := 0;
  AnimationFrame := 0;
  AnimationReady := False;
  AnimationMode := False;
  AnimationVisibleFrame := -1;
  InstallerIcon := 0;

  NormalLeft := WizardForm.Left;
  NormalTop := WizardForm.Top;
  NormalWidth := WizardForm.Width;
  NormalHeight := WizardForm.Height;
  NormalBorderStyle := WizardForm.BorderStyle;
  OuterLeft := WizardForm.OuterNotebook.Left;
  OuterTop := WizardForm.OuterNotebook.Top;
  OuterWidth := WizardForm.OuterNotebook.Width;
  OuterHeight := WizardForm.OuterNotebook.Height;
  BevelLeft := WizardForm.Bevel.Left;
  BevelTop := WizardForm.Bevel.Top;
  BevelWidth := WizardForm.Bevel.Width;
  BevelHeight := WizardForm.Bevel.Height;
  BackLeft := WizardForm.BackButton.Left;
  BackTop := WizardForm.BackButton.Top;
  BackWidth := WizardForm.BackButton.Width;
  BackHeight := WizardForm.BackButton.Height;
  NextLeft := WizardForm.NextButton.Left;
  NextTop := WizardForm.NextButton.Top;
  NextWidth := WizardForm.NextButton.Width;
  NextHeight := WizardForm.NextButton.Height;
  CancelLeft := WizardForm.CancelButton.Left;
  CancelTop := WizardForm.CancelButton.Top;
  CancelWidth := WizardForm.CancelButton.Width;
  CancelHeight := WizardForm.CancelButton.Height;

  if WizardSilent then
    Exit;

  ExtractTemporaryFiles('{tmp}\installer-frame-*.png');
  ExtractTemporaryFile('filecare.ico');
  InstallerIcon := LoadImage(0, ExpandConstant('{tmp}\filecare.ico'),
    ImageIcon, 0, 0, LRLoadFromFile or LRDefaultSize);
  SetInstallerWindowIcon;

  { 预载并解码全部帧。安装时只改变可见性，避免每帧磁盘读取造成卡顿。 }
  SetArrayLength(AnimationFrames, AnimationFrameCount);
  for AnimationFrame := 0 to AnimationFrameCount - 1 do
  begin
    AnimationFrames[AnimationFrame] := TBitmapImage.Create(WizardForm);
    AnimationFrames[AnimationFrame].Parent := WizardForm;
    AnimationFrames[AnimationFrame].Stretch := True;
    AnimationFrames[AnimationFrame].Center := True;
    AnimationFrames[AnimationFrame].Visible := False;
    AnimationFrames[AnimationFrame].PngImage.LoadFromFile(
      AnimationFramePath(AnimationFrame));
  end;
  AnimationFrame := 0;
  AnimationReady := True;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpInstalling then
  begin
    if AnimationReady then
      EnterAnimationMode;
  end
  else
    LeaveAnimationMode;
end;

procedure DeinitializeSetup;
begin
  StopAnimation;
  if InstallerIcon <> 0 then
    DestroyIcon(InstallerIcon);
end;
