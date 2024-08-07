Import-Module $env:SyncroModule

<#

The run-as needs to be set to Logged In User, instead of the default system.

You could pair this script with ar. if there is an event id alert for logged in user, trigger this script to run.

v1.0.1

This script utilizes platform variables and API calls to look for a matching Syncro Contact based on Current Logged In User
and assign it to the asset. The script will error out if no match is found or if two or more contacts are found.
The overwrite_assigned_contact variable is set to no by default and will error out the script if there is already
an assigned contact.  You can toggle the matching the condition by changing the dropdown variable $match_condition.
By default, the script will try to match based off the Syncro Contact's lastname. Troubleshooting logs are written
to the console output for review.

You will need to create your own API Key with the following permissions:

Assets - Edit
Customers - List/Search
Customers - View Detail
---------------------------------------------------------
SYNCRO Platform Variable for Manual Override in script. Example of how Syncro passed in the variables valuesMostly Used for troubleshooting
Troubleshooting logs are written to the console output for review.

Password Variables:

$apiKey ="T295149d4cd-4e37874823e0f868"  Real API Keys are longer but this is example formating

Platform Variables:

$customer = "301625"
subdomain = "hedgesmsp"
$assetId = "87295"
$assigned_contact = "user"

Dropdown Variables:

$overwrite_assigned_contact
    "no" - default
    "yes"

$match_condition
    "fullname"
    "lastname"
    "firstname"

$RMM_ALERT
    "no" - default
    "yes"

This script utilizes platform variables and API calls to look for a matching Syncro Contact based on Current Logged In User 
and assign it to the asset. The script will error out if no match is found or if two or more contacts are found.
The overwrite_assigned_contact variable is set to no by default and will error out the script if there is already an assigned
contact.You can toggle the matching the condition by changing the dropdown variable $match_condition. By default, the script 
will try to match based off the Syncro Contact's lastname

You will need to create your own API Key with the following permissions:

Assets - Edit
Customers - List/Search
Customers - View Detail

#>

# Default dropdown variable for $overwrite_assigned_contact is set to "no". If someone already assigned a contact to the asset the script would not overwrite it.
# This setting makes it safe to bulk run the script multiple times on all your assets
# Script exits with an error if there is already an assigned contact on the Syncro Device
if ($overwrite_assigned_contact -eq "no" -and -not [string]::IsNullOrWhiteSpace($assigned_contact)) {
    Write-Host "overwrite_already_assigned contact is set to no and there is a contact assigned that is not null or space"
    Write-Host "exiting script"
    Log-Activity -Message "Contact already assigned. Exiting Contact Assignment Script" -EventName "Contact Override"
    exit 1    
}

write-host "Matching will be BASED ON ------ $match_condition ------ Change the default variable called match_condition to change this"
write-host "--------------------------------------------------------------"

$headers = @{
    "accept" = "application/json"
    "Authorization" = "Bearer $apiKey" # Corrected authorization token prefix to "Bearer"
}

# Get Current Logged in User Variable
$loggedUser = Get-WmiObject -Class Win32_ComputerSystem | Select-Object -ExpandProperty UserName
Write-Output "Currently logged-in user: $loggedUser"
$domain, $username = $loggedUser -split "\\"
Write-Output "Domain: $domain"
Write-Output "Username: $username"

# Remove domain and replace '.' with a space in the username
$username = $username -replace "\.", " "
Write-Output "Modified Username should read 'FirstName LastName'. This will be used to match against the list of contacts in syncro, variable for '$username' is $username"

# Find all Contacts for Customer and assign them to an array
$allContacts = @()
$page = 1
do {
    $contacts = Invoke-RestMethod -Uri "https://$subdomain.syncromsp.com/api/v1/contacts?customer_id=$customer&page=$page" -Headers $headers -Method Get
    $allContacts += $contacts.contacts
    $total_pages = $contacts.meta.total_pages

    $page++
} while ($page -le $total_pages)

Write-Host "Total Pages of contacts: $total_pages" # Moved the write-host outside the loop

#Function that takes the Last Name of the Contact and checks the Logged In User for a match 
function Find-MatchingContacts {   
    param (
        [string]$loggedUser,        
        [array]$AllContacts
    )

    $matched = @()

    foreach($contact in $AllContacts) {
        
        $name = $contact.name
        $firstName, $lastName = $name -split ' ', 2
        
        #Write-Host "Checking Contact. Variables are: name - $name --- firstname --> $firstName lastname --> $lastName"
        
        if ($match_condition -eq "fullname"){
            if (-not $name) {
                $nameLower = $name.ToLower()
            }
            else {
                #Write-Host "Error: lastName --> $lastName - is null - Skipping this contact named --> $name"
                #Write-Host "------"
                continue
            }


        }
        elseif ($match_condition -eq "lastname") {
            if (-not $lastName) {
                $nameLower = $lastName.ToLower()
            }
            else {
                #Write-Host "Error: lastName --> $lastName - is null - Skipping this contact named --> $name"
                #Write-Host "------"
                continue
            }
        }
        else {
            
            if (-not $firstName) { 
                $nameLower = $firstName.ToLower()
            }
            else {
                #Write-Host "Error: firstName --> $firstName - is null - Skipping this contact named --> $name"
                #Write-Host "------"
                continue
            }
            
        }
            
        if (-not $username) {  # Check if $LoggedUser is not null
            $username = $username.ToLower()            
            #Write-host "Username variable assigned is: $username" 
        }
        else {
            Write-Host "Error: Unable to find Logged username or username is null, skipping this contact"
            Write-Host "------"
            end # Skip this iteration and move to the next contact
        }
        
        if (-not [string]::IsNullOrWhiteSpace($nameLower)) {  # Check if $nameLower is not empty
            if ($username -like "*$nameLower*" -or $nameLower -like "*$username*") {
                Write-Host "matching based off $match_condition ---- 1. username like nameLower --> $username like $nameLower OR 2. Name is like username -->: $nameLower like $username"
                Write-Host "Found matching contact based on name: $nameLower matches with $username"
                $contactid = $contact.id
                write-host "Adding Name: $name and contact object's ID: $contactid to the matched array"
                Write-Host "------"
                $matched += "$name $contactid" # Concatenating name and id
                
            }
            else {
                
                #Write-Host "No Match for $nameLower when comparing versus username ----> $username"
                #Write-Host "------"
                continue
            }            
        }
        else {
            
            #Write-Host "Error: Last name is empty for contact --> $name, not comparing skipping. first --> $firstName || last --> $lastName"
            #Write-Host "------"
            continue
        }
        
    }
    
    Write-Host "This is the matched array that is being returned: $matched "
    Write-Host $matched
    
    # Could return more than one match
    return $matched
}

# Call the function
$matchedContacts = Find-MatchingContacts -LoggedUser $username -AllContacts $allContacts

#Write to Console Number of Found matches
$numberFound = $matchedContacts.count
Write-Host "$numberFound matches found"
#Function that assigned an Contact to an Asset
function set-ContactToAsset {

    param (
        [string]$AssetId,        
        [string]$ContactId
    )

    $authorizationToken = "Bearer $apiKey"  # Make sure it's correct and includes "Bearer" prefix

    $apiEndpoint = "https://$subdomain.syncromsp.com/api/v1/customer_assets/$assetId"

    # Define the data to send in the request
    $data = @{
        "contact_id" = $contactId
    }

    # Convert data to JSON format
    $jsonData = $data | ConvertTo-Json

    try {
        # Make the API call
        $response = Invoke-RestMethod -Uri $apiEndpoint -Headers @{
            "Authorization" = $authorizationToken
            "Content-Type" = "application/json"
        } -Body $jsonData -Method Put

        # Output the response
        #$response
    }
    catch {
        Write-Error "Error occurred: $_"
    }

}

# Assign contact to asset if only one match found
if ($numberFound -eq 1) {
    $parts = $matchedContacts.Split(" ")
    $contactId = $parts[-1] # since the Find-MatchingContacts function returns the variable in a format of "first last ID" the [-1] removes all but the ID
    
    write-host "These are the variable passing to set-ContactToAsset Funciton: AssetId $assetId ContactId $contactId"
    set-ContactToAsset -AssetId $assetId -ContactId $contactId 
    Log-Activity -Message "Successful Contact Matched for $loggedUser - $matchedContacts " -EventName "Contact Matched"
   
}
else{
    #If 0 matches or more than 1 match is found, log the activity and error out the script
    if ($numberFound -eq 0){
        
        write-host "No Matches Found"
        Log-Activity -Message " Failed Contact Match for $loggedUser. Nothing Found, or unable to determine contact. Please review. $matchedContacts " -EventName "Failed Contact Match"
        if($RMM_ALERT -eq "yes"){
            Rmm-Alert -Category 'Failed Contact Match' -Body "Failed Contact Match for $loggedUser. Nothing Found, or unable to determine contact. Please review. $matchedContacts"
        }
        exit 1
    } 
    else{
        Write-Host "More than one matched contact found, or unable to determine contact. Please review"
        write-host $matchedContacts
        Log-Activity -Message "Failed Contact Match for $loggedUser. More than one matched contact found, or unable to determine contact. Please review. $matchedContacts " -EventName "Failed Contact Match"
        
        if($RMM_ALERT -eq "yes"){
            Rmm-Alert -Category 'Failed Contact Match' -Body "Failed Contact Match for $loggedUser. More than one matched contact found, or unable to determine contact. Please review. $matchedContacts"
        
        }
        exit 1
    }    

}
