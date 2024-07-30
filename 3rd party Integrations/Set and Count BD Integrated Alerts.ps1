Import-Module $env:SyncroModule
<#

the $api should be a syncro api key with view rmm alert


#>

$currentComputerName = hostname

# Define the API endpoint and headers
$headers = @{
    "accept" = "application/json"
    "Authorization" = "Bearer $api"
}

# Initialize variables
$page = 1
$cutOffDate = (Get-Date).AddDays(-60)
$allFilteredAlerts = @()

# Loop to retrieve data from multiple pages
while ($true) {
    $url = "https://hedgesmsp.syncromsp.com/api/v1/rmm_alerts?status=all&page=$page"

    # Make the API request and store the response
    $response = Invoke-RestMethod -Uri $url -Headers $headers -Method Get

    # Check if the response contains any items
    if ($response.rmm_alerts.Count -eq 0) {
        # No more items in the response, exit the loop
        break
    }

    # Create an array to store items with 'updated_at' in the last 60 days for this page
    $filteredAlerts = @()

    # Loop through each item in the response
    foreach ($item in $response.rmm_alerts) {
        # Parse the 'updated_at' date from the item
        $updatedAt = [DateTime]::Parse($item.updated_at)

        # Check if 'updated_at' is within the last 60 days
        if ($updatedAt -ge $cutOffDate) {
            # Add the item to the filtered array for this page
            $filteredAlerts += $item
        } else {
            # If 'updated_at' is older than 60 days, break the loop
            $page = -1
            break
        }
    }

    # Add the filtered items from this page to the overall filtered alerts
    $allFilteredAlerts += $filteredAlerts

    # Check if we need to break the loop
    if ($page -eq -1) {
        break
    }

    # Increment the page number for the next request
    $page++
}

# Now, $allFilteredAlerts contains items with 'updated_at' in the last 60 days from all pages
# Get the current computer name


$bitdefenderAlerts = @()

# Iterate through each item in $allFilteredAlerts and check for "bitdefender" in the description
foreach ($item in $allFilteredAlerts) {
    $description = $item.description

    # Check if the description contains the word "bitdefender" (case-insensitive)
    if ($description -like "*bitdefender*") {
        # Add the item to the $bitdefenderAlerts array
        $bitdefenderAlerts += $item
    }
}

# Create an array to store Bitdefender alerts with matching computer_name
$matchingBitdefenderAlerts = @()

# Iterate through each item in $bitdefenderAlerts and check for a matching computer_name
foreach ($item in $bitdefenderAlerts) {
    $computerNameInAlert = $item.computer_name

    # Check if the computer_name in the alert matches the current computer name
    if ($computerNameInAlert -eq $currentComputerName) {
        # Add the item to the $matchingBitdefenderAlerts array
        $matchingBitdefenderAlerts += $item
    }
}

#Bitdefender Alerts last 60 days

$count = $matchingBitdefenderAlerts.Count

write-host $count

Set-Asset-Field -Name "Last 60 Days BD Alerts" -Value $count


