[Setup]
AppName=Modpack Downloader
AppVersion=0.1.2
DefaultDirName={autopf}\ModpackDownloader
DefaultGroupName=Modpack Downloader
OutputDir=dist
OutputBaseFilename=modpack-downloader-setup

[Files]
Source: "dist\modpack-downloader.exe"; DestDir: "{app}"

[Registry]
Root: HKCR; Subkey: "modpack-dl"; ValueType: string; ValueName: ""; ValueData: "URL:Modpack Downoader"; Flags: uninsdeletekey
Root: HKCR; Subkey: "modpack-dl"; ValueType: string; ValueName: "URL Protocol"; ValueData: ""
Root: HKCR; Subkey: "modpack-dl\shell\open\command"; ValueType: string; ValueData: """{app}\modpack-downloader.exe"" ""%1"""

[Icons]
Name: "{group}\Modpack Downloader"; Filename: "{app}\modpack-downloader.exe"
