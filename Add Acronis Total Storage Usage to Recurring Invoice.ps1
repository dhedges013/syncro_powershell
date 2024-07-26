# Generate API tokens from your Acronis Portal
$clientId = "47888e9f-6c871fc00de4834" #Created in Acronis' Portal, linked to the api secret, but I do not think it changes
$clientSecret = "xuwqxqtuqblluny4tlg6vhzbzxmtyiiwm" # Created in Acronis Portal, use a password script variable if running from Syncro
$tenantID = "b40397d1-657-72c4e48b9daa" #different per customer in Acronis Portal this, you can use Customer custom fields and platform variabels if you want to run the code from syncro

# Construct Basic Authentication Header
$authValue = "Basic " + [System.Convert]::ToBase64String([System.Text.Encoding]::ASCII.GetBytes("${clientId}:${clientSecret}"))
$headers = @{ "Authorization" = $authValue }

# Request access token
$token = Invoke-RestMethod -Method Post -Uri "https://us5-cloud.acronis.com/api/2/idp/token" -Headers $headers -Body @{ grant_type = "client_credentials" }

# Build API call
$baseUri = "https://us5-cloud.acronis.com/"
$endpoint = "api/2/tenants/usages"
$params = @{ "tenants" = "$tenantID" }
$queryString = [System.Web.HttpUtility]::ParseQueryString("")
$params.GetEnumerator() | ForEach-Object { $queryString.Add($_.Key, $_.Value) }
$fullUrl = $baseUri + $endpoint + "?" + $queryString.ToString()

# Add authorization header with access token
$headers["Authorization"] = "Bearer " + $token.access_token

# Make the API call
$usageResponse = Invoke-RestMethod -Method Get -Uri $fullUrl -Headers $headers

# Get total storage usage
$totalStorageUsage = $usageResponse.items[0].usages | Where-Object { $_.name -eq "total_storage" }
$totalGB = [Math]::Round($totalStorageUsage.value / 1GB, 2)
# Output the result
Write-Host "Total amount of GB used for Workstations: $totalGB"

#************************************Syncro Recurring Invoice Add************************************
#****************************************************************************************************

#Uses two platform Variables
# $custNo for customer id
# $subdomain for the syncro subdomain

# Set the Variable for the API Call
write-host "Platform Variable: syncro customer id $custNo" #this can be a platform variable

#Add your subdomain instead of 'hedgesmsp'
$url = "https://"+$subdomain+".syncromsp.com/api/v1/customers"
$recurringURL = "https://"+$subdomain+".syncromsp.com/api/v1/schedules?customer_id="+$custNo

# Add you Syncro API Token Here || Can also be a Script Password Variable
$access_token = "T29514d29d4cd-e378748232c08f83e0f868"

# Creates Header for API Call
$Header = @{'Authorization' =" bearer $access_token"}
$data = Invoke-RestMethod -Method 'GET' -Header $Header -ContentType "application/json"  -Uri $recurringURL

# Create Variable to hold Schedule Data
$scheduleList = $data.schedules

# function to add the total qty of the one time charge

function add-LineItem($qty){    
    $qty = $totalGB

    write-host "running function add-lineItem"
    write-host "this is the qty variable $qty"
    
    #Variable to build description line
    $description = "Total Usage "+ $qty+" GB of Data"

    if($qty){
        $line = '{ "description": "'+$description+'","name": "Backup Data","position": 0,"quantity": "'+$qty+'","retail_cents": 100,"schedule_id": '+$scheduleid+',"one_time_charge": true,"taxable": true}'
        $request = Invoke-RestMethod -Method 'POST' -Header $Header -ContentType "application/json"  -Uri $scheduleURL -Body $line
    }
}


if($scheduleList.count -gt 1){
    #If more than one recurring Schedule for Customer, do not try to add a line
    write-host "more than 1 Recurring invoice found"
}
#Add One time line item to the recurring invoice
else{
    $scheduleid = $scheduleList[0].id
    write-host "id is $scheduleid"
    $scheduleURL = "https://"+$subdomain+".syncromsp.com/api/v1/schedules/"+$scheduleid+"/add_line_item"
    add-LineItem($qty)
}