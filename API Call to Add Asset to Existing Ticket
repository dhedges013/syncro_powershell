# Generate a random number between 5 and 10
$waitTime = Get-Random -Minimum 1 -Maximum 30
# Wait for the random amount of time
Start-Sleep -Seconds $waitTime

#Hardcode Variables
#$ticketNo = "5018"
#$assetID = "7421775"
#$subdomain = "hedgesmsp"
# Add you API Token Here
#$syncroAPI = "Tf84dbd83909aef914-5366297e13f5830b80063b6abd9d62ef"

#Add your subdomain instead of 'hedgesmsp'
#$url = "https://hedgesmsp.syncromsp.com/api/v1/customers"
$ticketURL = "https://"+$subdomain+".syncromsp.com/api/v1/tickets?number="+$ticketNo

# Creates Header for API Call
$Header = @{'Authorization' =" bearer $syncroAPI"}
#To get Ticket ID with out ticket number
$ticketData = Invoke-RestMethod -Method 'GET' -Header $Header -ContentType "application/json"  -Uri $ticketURL 
# Create Variable to hold Schedule Data
$ticketid = $ticketData.tickets.id
write-host $ticketid



$ticketURLID = "https://"+$subdomain+".syncromsp.com/api/v1/tickets/"+$ticketid
#Get Ticket Data by ID
$ticketData = Invoke-RestMethod -Method 'GET' -Header $Header -ContentType "application/json"  -Uri $ticketURLID

# Generate a random number between 5 and 10
$waitTime = Get-Random -Minimum 1 -Maximum 5
# Wait for the random amount of time
Start-Sleep -Seconds $waitTime

# Check if assets already exist on the ticket
if ($ticketData.ticket.asset_ids) {
    # Assets already exist, add the new asset ID to the list
    $existingAssetIds = $ticketData.ticket.asset_ids
    
    
    if ($existingAssetIds -notcontains $assetID) {
        # Add the new asset ID to the list
        $existingAssetIds += $assetID
    }
    else
    {
        write-host "Asset is already added to ticket"
        exit 0
    }


    # Update the assets on the ticket
    $updatedTicketData = @{
        asset_ids = $existingAssetIds
    } | ConvertTo-Json

    $updatedTicketURL = "https://"+$subdomain+".syncromsp.com/api/v1/tickets/$ticketId"

    Invoke-RestMethod -Method 'PUT' -Header $Header -ContentType "application/json" -Uri $updatedTicketURL -Body $updatedTicketData
}
else {
    # No assets exist on the ticket, create a new asset list with the new asset ID
    $newAssetIds = @($assetID)

    # Update the assets on the ticket
    $updatedTicketData = @{
        asset_ids = $newAssetIds
    } | ConvertTo-Json
    
    $updatedTicketURL = "https://"+$subdomain+".syncromsp.com/api/v1/tickets/$ticketId"
    Invoke-RestMethod -Method 'PUT' -Header $Header -ContentType "application/json" -Uri $updatedTicketURL -Body $updatedTicketData
}

