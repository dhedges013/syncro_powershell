<#

This would be used for a Connectwise Import of a Board, and tagging the Tickets with the right flag.

#>

#Auth Header for API Calls
$headers = @{
    "accept" = "application/json"
    "Authorization" = "T29514d29d4c-78748232c08f83e0f868"
}
$subdomain = "yourSubDomain"
#Grab the List of Newly Imported TIckets via the ticket search that will look for resolved tickets untagged
$urlBase = "https://$subdomain.syncromsp.com/api/v1/tickets?ticket_search_id=130383"
$response = Invoke-RestMethod -Uri $urlBase -Method Get -Headers $headers
# Find to Total pages
$total_pages = $response.meta.total_pages

#variable to hold all ticket data
$allResponses = @()

#loop through each page and add ticket data to $allresponses variable
for ($page = 1; $page -le $total_pages; $page++) {
    $url = "$urlBase&page=$page"
    Write-Host "Fetching page $page..."
    $response = Invoke-RestMethod -Uri $url -Method Get -Headers $headers
    Start-Sleep -Seconds .5
    $allResponses += $response.data | ConvertFrom-Json
}

#assign tickets data to powershell variable
$tickets = $allResponses.tickets

#Loop through tickets and change the status to other
foreach ($ticket in $tickets) {
    $ticketId = $ticket.id
    $ticketUrl = "https://$subdomain.syncromsp.com/api/v1/tickets/$ticketId"
    $body = @{
        status = "Other"
    } | ConvertTo-Json

    Write-Host "Updating ticket $ticketId..."
    Invoke-RestMethod -Uri $ticketUrl -Method Put -Headers $headers -ContentType "application/json" -Body $body
    Start-Sleep -Seconds .5

}
