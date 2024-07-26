Import-Module $env:SyncroModule
<#
Use the dropdown variable to select a choco package for a one time install push. Chocolatey needs to be installed beforehand.
If you have a 3rd party update policy assigned to the machine, Syncro will automatically install Chocolatey for you.
If the Chocolatey command "choco" is not found, an RMM alert is generated. Feel free to add your own favorite packages to the dropdown variables list. 

Chocolatey needs to be installed before hand. If you have a 3rd party update policy assigned to the machine, 
Syncro will automatically install Chocolatey for you.

Tested
Firefox - choco install firefox 
Chrome - choco install googlechrome
notepad++ - choco install notepadplusplus.install 
7zip - choco install 7zip.install
Zoom - choco install zoom
Slack - choco install slack
Google Drive - choco install googledrive
Greenshot choco install greenshot
Edge - choco install microsoft-edge
FileZilla - choco install filezilla
Putty - choco install putty
GIMP - choco install gimp
DC Reader - choco install adobereader

#>

if (Get-Command choco -ErrorAction SilentlyContinue) {
    Write-Output "Chocolatey is installed."
    Log-Activity -Message "Choco Package: $choco_install one-time install pushed" -EventName "Choco Install"
    choco install $choco_install -y
} else {
    Write-Output "Chocolatey is not installed."
    Rmm-Alert -Category 'Chocolatey missing' -Body "Chocolatey install is missing. A one-time app install was ran for $choco_install but the choco command was not found. Please make sure Chocolatey is installed and try again."
    Log-Activity -Message "FAILED Choco Install Package: $choco_install one-time install" -EventName "Choco Install"
    exit 1
}



