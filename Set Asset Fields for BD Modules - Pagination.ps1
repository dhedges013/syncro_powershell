Import-Module $env:SyncroModule
<#
This powershell script will query the Bitdefender Public API and look for enabled / installed GravityZone modules on the 
endppoints. It will write the results of the module lookup to custom asset fields in syncro. Default asset field names that
you will need to create are: hyperdetect, edr, encryption

To get a return of the modules installed on an endpoint you have to get the endpoints GravityZone ID. So far the only way
I have found how to get this ID is to query the Bitdefender API directly to get a list of all the endpoint ID and look for
a matching name. This code should loop through multiple pages of endpoints.

Once you have the ID then it is easy to lookup modules installed. The data looked stored in a nosql database, for example 
if EDR is not installed on the endpoint, the modules installed does not include edr, it is just missing. But if EDR is 
installed, it returns "edr:true"

I look up the computers hostname directly in the powershell, so if the hostname and the name in GravityZone do not match,
the script will not work correctly.

I used the following platform variables:

companyName - {{customer_business_name}}
api_key - runtime password type

Scripting Platform Variables
#companyName = "John Smith Smithing"
$api_key
#>


$computerName = hostname



function Get-BDAPICall($EndpointURL, $method, $parameters){

    $api_key = '655be28afb41d21ade62203f824fab7bf44cdf4a8f411ff506f8175ec52aea54'

    # Build the login string (pass is an empty string)
    $user = $api_key
    $pass = ""
    $login = $user + ":" + $pass

    # Encode the login string to base64
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($login)
    $encodedLogin = [Convert]::ToBase64String($bytes)

    # Prepend "Basic " to the encoded login string to obtain the auth header
    $authHeader = "Basic " + $encodedLogin

    $Headers = @{
        'Authorization' = $authHeader
        'Content-Type' = 'application/json'
    }
  
   $Guid = New-Guid

   $BaseURL = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/$EndpointURL"
   

   $Body = @{'params' = $parameters
       'jsonrpc' = '2.0'
       'method' = $method
       'id' = $Guid.Guid

   } | ConvertTo-Json -Depth 4;
   $Body
   $results = (Invoke-RestMethod -Uri $BaseURL -Method Post -Body $Body -Headers $Headers)
   Write-Host $results
   return $results
}




function Get-Company($companyName){
    #Search Company name in BD
    $inputPackage = 'companies'
    $inputMethod = 'findCompaniesByName'
    $inputParameters = @{'nameFilter' = "$companyName"}


    $CallCompanyResults = Get-BDAPICall $inputPackage $inputMethod $inputParameters
    $result = $CallCompanyResults.result.id
    return $result
}

function Get-EndpointID($companyID){
    
   $companyID = Get-Company($companyName)
   
   $inputPackage = 'network'
   $inputMethod = 'getEndpointsList'
   $inputParameters = @{
      'parentId' = $companyID
   }
   
   $results = @()

   do {
       # Make the API call to get the endpoint list
       $GetEndpointListResults = Get-BDAPICall $inputPackage $inputMethod $inputParameters
       $currentPageResults = $GetEndpointListResults.result.items
       $results += $currentPageResults

       # Check if there are more pages
       $totalPages = $GetEndpointListResults.result.pagesCount
       $currentPage = $GetEndpointListResults.result.page

       if ($currentPage -lt $totalPages) {
           # If there are more pages, update the page parameter for the next call
           $inputParameters['page'] = $currentPage + 1
       }
       else {
           # No more pages, exit the loop
           break
       }
   } while ($true)

   foreach ($item in $results) {
       if ($item.name -eq $computerName) {
           $endpointid = $item.id
           Write-Host "Found Matching Host name in GravityZone, Returning endpoint ID $endpointid"
           return $item.id
       }
   }
   
   # No matching host name found, return the entire list of results
   return $results
}



function Get-EndpointModules($endpointid){#, $computerName){
   
   $inputPackage = 'network'
   $inputMethod = 'getManagedEndpointDetails'
   $inputParameters = @{
        'endpointId' = $endpointid
   }

   $GetEndpointDetails= Get-BDAPICall $inputPackage $inputMethod $inputParameters
   
   
   $modules = $GetEndpointDetails.result.modules
   write-host "Here are the modules installed on this endpoint"
   return $modules
   
}

$companyID = Get-Company($companyName)
$endpointid = Get-EndpointID($companyID)
$modules = Get-EndpointModules($endpointid)

write-host $companyID
write-host $endpointid

write-host"****************************Modules****************************"
write-host $modules

$hyperdetect = $modules.hyperdetect
$encryption = $modules.encryption
$edr = $modules.edrSensor

Set-Asset-Field -Name "hyperdetect" -Value $hyperdetect
Set-Asset-Field -Name "encryption" -Value $encryption
Set-Asset-Field -Name "edr" -Value $edr

