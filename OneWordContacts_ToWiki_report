# Set your subdomain for API calls
$subdomain = "hedgesmsp"
# Set the access token for API calls
$access_token = "T29514d29d4cd0-e094e378748232c08f83e0f868"
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

# Function to filter contacts with one-word names
function Filter-OneWordContacts($contacts) {
    $oneWordContacts = @()

    foreach ($contact in $contacts) {
        $nameWords = $contact.name -split "\s+"
        if ($nameWords.Count -eq 1) {
            $oneWordContacts += $contact
        }
    }

    return $oneWordContacts
}

# Gather Syncro contacts
$contactList = Get-SyncroContacts

# Filter contacts with one-word names
$oneWordContacts = Filter-OneWordContacts $contactList

# Output the list of contacts with one-word names
$oneWordContacts

# Function to create HTML table for one-word contact names
function Create-HTMLTableForOneWordContacts {
    param (
        [array]$OneWordContacts
    )

    # HTML Table header
    $html = @"
    <Html>
    <Body>
    <Table border=1 style='border-collapse: collapse;width:50%;text-align:center'>
    <th>Contact Name</th>
    <th>Contact ID</th>
"@

    # Adding HTML table rows for one-word names
    foreach ($contact in $OneWordContacts) {
        $html += "<tr><td>$($contact.name)</td><td>$($contact.id)</td></tr>"
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

# Gather Syncro contacts
$contactList = Get-SyncroContacts

# Filter contacts with one-word names
$oneWordContacts = Filter-OneWordContacts $contactList

# Create HTML table for one-word contact names
$htmlTable = Create-HTMLTableForOneWordContacts -OneWordContacts $oneWordContacts

# Create wiki page with the HTML table
Create-WikiPage -subdomain $subdomain -SyncroAPIKey $access_token -customerID $cust_id -name "One-Word Contacts Report" -body $htmlTable
