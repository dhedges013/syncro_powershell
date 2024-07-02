Import-Module $env:SyncroModule
<#

This powershell scripts builds an array of all the assets for a particular company from your Hudu Accoutn . The script assumes you already know what the CompanyID is in Hudu.
Ideally this would already be stored in a Syncro Custom Field, could be Customer or Asset Custom Field.


Password Variable Example:

$apiKey = "Z53SUNMLuNFphGAh" #this is Hudu's API Key

Platform Variable:
$subdomain = "hedgesmsp" this would be your Hudu subdomain
$companyId = "6" this is the Hudu Company


#>

write-host "Computers's Name is $computerFriendlyName"

#If the Syncro Platform Variable is null or blank, ask the computer for its name
if(-not $computerFriendlyName){
    $computerFriendlyName = [System.Environment]::MachineName
    write-host "Computers's Name is $computerFriendlyName"
}
else{
    write-host "Computers's Name is $computerFriendlyName"
}

# Define the base URI
$baseUri = "https://$subdomain.huducloud.com/api/v1/companies/$companyId/assets/?page="

$headers = @{
    'accept' = 'application/json'
    'x-api-key' = $apiKey
}

# Initialize an empty list to hold all assets
$allAssets = @()

# Initialize pagination variables
$page = 1
$morePages = $true

while ($morePages) {
    write-host "baseuri $baseUri"
    # Construct the URI for the current page
    $uri = "$baseUri"+$page
    
    write-host "This is the url: $uri"
    # Make the GET request and store the response
    $response = Invoke-RestMethod -Method Get -Uri $uri -Headers $headers
    
    # Check if the response is empty
    if (-not $response -or $response.assets.Count -eq 0) {
        write-host "response is null or there are no assets, set morepages to false"
        $morePages = $false
    } else {       
        # Convert the modified JSON string to a PowerShell object
        $assetList = $response  | ConvertFrom-Json

        # Add the assets from this page to the allAssets list
        $allAssets += $assetList.assets
        if($allAssets.assets.Count -eq 0){
            $morePages = $false
        }

        # Increment the page number for the next iteration
        $page++
    }
}

# Iterate through each asset and compare the name
foreach ($asset in $assets) {
    $name = $asset.name
    write-host "checking $name"
    
    if ($asset.name -eq $computerFriendlyName) {
        
        Write-Host "Found asset with name: $computerFriendlyName"
        $id = $asset.id
        write-host "ID is $id"
        
        Set-Asset-Field -Name "hudu asset id" -Value $id
        exit 0
        
    }
}
