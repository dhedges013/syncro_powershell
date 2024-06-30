<#

This powershell takes a Syncro Device Asset Field Data Point and updates a Matching Hudu Asset Custom Field

The script assumes you have hard coded the Hudu CompanyID and Hudu AssetID into Syncro Device Custom Fields inorder to make the Hudu Put API Call

Platform Variables:
$CompanyID = "6" this is the hudu companyID stored in a Syncro Custom Asset Field
$AssetID = "38" this is a hudu assetID stored in a Syncro Custom Asset Field
$APIKey = "Z7wzwZBmp9fwd3trkF1Cvjtx" this is a hudu api key
$customSyncro = "balance" this could be any data point and is optional as a platform variable. You could also assign the value directly in the script based on what you are looking for


Updating a Custom Field in Hudu on an exisiting Asset requires special Syntax and can be tricky on first attempt. 
When I build out the Json obejct with the Custom Data Point see below example:

$CustomFields = @{
    CustomSyncro = $customSyncro  
}

CustomSyncro needs to be changed to the actual field name in Hudu
$customSyncro is just a platform variable in syncro which you pick the asset field you want piped into the script

Example:
In Hudu I created a custom asset field called powerPlan, which will store the Power Plan of a Windows Machine; Power Save, High Performance, Balanced, etc
you would build out $CustomFields like so:

$CustomFields = @{
    powerPlan = $customSyncro  
}

Where $customSyncro is already assigned the value of what the actual Powerplan is via powershell or piping in a Syncro Platform Variable.

#>

function Update-HuduAsset {
    param (
        [string]$CompanyID,
        [string]$AssetID,
        [string]$APIKey,
        [hashtable]$CustomFields
    )

    # API Endpoint
    $url = "https://$subdomain.huducloud.com/api/v1/companies/$CompanyID/assets/$AssetID"

    # Headers
    $headers = @{
        "accept"        = "application/json"
        "x-api-key"     = $APIKey
        "Content-Type"  = "application/json"
    }

    # Convert the custom fields to JSON manually
    $customFieldsJson = $CustomFields | ConvertTo-Json -Depth 10
    $body = @{
        asset = @{
            custom_fields = @($CustomFields)
        }
    }

    # Convert the body to JSON
    $bodyJson = $body | ConvertTo-Json -Depth 10

    # Replace the custom_fields with properly formatted JSON
    $bodyJson = $bodyJson -replace '"custom_fields":\s*\[\s*"System.Collections.Hashtable"\s*\]', "`"custom_fields`": $customFieldsJson"
    write-host $bodyJson
    # Invoke-RestMethod
    try {
        $response = Invoke-RestMethod -Uri $url -Method Put -Headers $headers -Body $bodyJson
        return $response
    } catch {
        Write-Error "Failed to update asset: $_"
    }
}

# Example usage
#$CompanyID = "6" this is the hudu companyID stored in a Syncro Custom Asset Field
#$AssetID = "38" this is a hudu assetID stored in a Syncro Custom Asset Field
#$APIKey = "Z7wzwZBmp9fwd3trkF1Cvjtx" this is a hudu api key

#change the CustomSyncro words on the left side of the array to the name of the field in Hudu
# the $customSyncro is the Syncro Asset Field value you want to push into Hudu
$CustomFields = @{
    CustomSyncro = $customSyncro  
}

Update-HuduAsset -CompanyID $CompanyID -AssetID $AssetID -APIKey $APIKey -CustomFields $CustomFields
