<#

This Powershell does not use the built-in Syncro Cmdlets and you do not need to import the syncro module

Following Variables can be used as Platform Variables

Platform Variables:
$subdomain
$cust_id

Password Variable:
$access_token

There are 3 main functions
Get-SyncroContacts 
    - Querys a contact list via customer id from Syncro Open-API
    - Takes into account multiple pages
    - returns all contacts in an array object

New-SyncroContact
    - Creates a new syncro contact via the open API using a POST call
    - takes user data from AD as input argument to build the JSON for the POST Call

Compare-Contacts
    - compares a list of AD Users versus the contact list returned by the Get-SyncroContacts function
    - takes AD User List and Syncro's API Contact list and compares
    - the AD User's UserPrincipalName is compared againt the list of Syncro Contact's Email field. If no match found, calls the New-SyncroContact function and passes all the AD user data

#>

# Set your subdomain for API calls
$subdomain = "hedgesmsp"
# Set the access token for API calls
$access_token = "T29514d29d4cd-094e378748232c08f83e0f868"
$Header = @{ 'Authorization' = "Bearer $access_token" }

# Customer ID and name
$cust_id = "31278773"

# Function to gather Syncro contacts
function Get-SyncroContacts {
    $urlContact = "https://$subdomain.syncromsp.com/api/v1/contacts?customer_id=$cust_id"
    $contactList = @()

    $contactData = Invoke-RestMethod -Method 'GET' -Uri $urlContact -Headers $Header -ContentType "application/json"
    $totalPages = $contactData.meta.total_pages

    for ($x = 1; $x -le $totalPages; $x++) {
        $currentPageUrl = "$urlContact&page=$x"
        $contactData = Invoke-RestMethod -Method 'GET' -Uri $currentPageUrl -Headers $Header -ContentType "application/json"
        $contactList += $contactData.contacts
    }
    
    return $contactList
}

# Function to create contact in Syncro
function New-SyncroContact($user) {
    $dnParts = $user.DistinguishedName -split ","
    $ou = $dnParts[1].Trim().Substring(3)

    $notes = "Office: $($user.Office), Department: $($user.Department), OU: $ou"

    $body = @{
        "customer_id" = $cust_id
        "name" = $user.Name
        "address1" = $user.StreetAddress
        "city" = $user.City
        "state" = $user.State
        "zip" = $user.PostalCode
        "email" = $user.UserPrincipalName
        "phone" = $user.TelephoneNumber
        "notes" = $notes
    } | ConvertTo-Json

    Invoke-WebRequest -Method 'POST' -Uri $urlContact -Headers $Header -ContentType "application/json" -Body $body -UseBasicParsing
    Write-Host $body
}

# Function to compare Syncro contacts with AD users
function Compare-Contacts($users, $contactList) {
    if (-not $contactList) { # Powershell's recommeded syntax for checking for null 
        Write-Host "The contact list is null."
        return
    }
    
    foreach ($user in $users) {
        $adEmail = $user.UserPrincipalName
        if ([string]::IsNullOrWhiteSpace($adEmail)) {
            Write-Host "Blank or null UPN for user $($user.Name), skipping"
            continue
        }

        $emailFound = $false
        foreach ($syncroContact in $contactList) {
            if ($syncroContact.email -eq $adEmail) {
                $emailFound = $true
                Write-Host "Matching Email in Syncro $($syncroContact.email) found!"
                break
            }
        }

        if (-not $emailFound) {
            Write-Host "Email not found for $($user.Name), creating new contact now"
            New-SyncroContact $user
        }

        Write-Host "-----------------------------------------------------------------------------------------------------------"
    }
}

# Gather Syncro contacts
$contactList = Get-SyncroContacts

# Gather AD users
$users = Get-ADUser -Filter * -Properties TelephoneNumber, StreetAddress, City, State, PostalCode, Office, Department | Select-Object Name, UserPrincipalName, DistinguishedName, TelephoneNumber, StreetAddress, City, State, PostalCode, Office, Department

# Compare contacts
Compare-Contacts $users $contactList
