# Set your subdomain for API calls
$subdomain = "hedgesmsp"
# Set the access token for API calls
$access_token = "T29514d29d4cd02f-e094e378748232c08f83e0f868"
$Header = @{ 'Authorization' = "Bearer $access_token" }

# Customer ID and name
$cust_id = "31278773"
$cust_name = "Dental Dan Dentistry"

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

# Function to find duplicate contact names
function Find-DuplicateContactNames {
    param (
        [array]$Contacts
    )

    $duplicateInfo = @()

    # Create a hashtable to store encountered names
    $namesHashTable = @{}

    foreach ($contact in $Contacts) {
        $name = $contact.name

        # Check if the name already exists in the hashtable
        if ($namesHashTable.ContainsKey($name)) {
            # If it exists, add it to the duplicate names list
            $duplicateInfo += @{
                Name = $name
                ID = $contact.id
            }
        } else {
            # If it doesn't exist, add it to the hashtable
            $namesHashTable[$name] = $true
        }
    }

    return $duplicateInfo
}

# Function to create HTML table with duplicate contact names
function Create-HTMLTableForDuplicates {
    param (
        [array]$DuplicateInfo
    )

    # HTML Table header
    $html = @"
    <Html>
    <Body>
    <Table border=1 style='border-collapse: collapse;width:50%;text-align:center'>
    <th>Contact ID</th>
    <th>Contact Name</th>
"@

    # Adding HTML table rows for duplicate names
    foreach ($info in $DuplicateInfo) {
        $html += "<tr><td>$($info.ID)</td><td>$($info.Name)</td></tr>"
    }

    # Close HTML tags
    $html += "</table></body></html>"

    return $html
}

# Function to create wiki page with the HTML content
function Create-WikiPage {
    param (
        [string]$subdomain,
        [string]$SyncroAPIKey,
        [string]$customerID,
        [string]$name,
        [string]$body
    )

    $CreatePage = @{
        customer_id = $customerID
        name = $name
        body = $body
        api_key = $SyncroAPIKey
    }

    $jsonBody = ConvertTo-Json $CreatePage
    $url = "https://$subdomain.syncromsp.com/api/v1/wiki_pages"
    Invoke-RestMethod -Uri $url -Method Post -Body $jsonBody -ContentType 'application/json'
}

# Get Syncro contacts
$contactList = Get-SyncroContacts

# Find duplicate contact names and IDs
$duplicateInfo = Find-DuplicateContactNames -Contacts $contactList

# Create HTML table for duplicate contact names and IDs
$htmlTable = Create-HTMLTableForDuplicates -DuplicateInfo $duplicateInfo

# Create wiki page with the HTML table
Create-WikiPage -subdomain $subdomain -SyncroAPIKey $access_token -customerID $cust_id -name "Duplicate Contacts Report" -body $htmlTable
