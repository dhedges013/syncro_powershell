Import-Module $env:SyncroModule
<#
v1.01 - added check for c:\temp folder, and script will create the folder if missing. Cleaned up how the TTL column looks
in the table.

This powershell script will create a HTML doc and using a Syncro API call to create a Wiki-Doc under that customer's 
Documentation. When running the script it will delete any previous network scan Wiki-Docs under that customer to prevent clutter. Scan will show on the lefthand side of the Asset, or in the Documentation center. The scan will attempt to report back on device type (windows or Linux/MacOs) as well as open ports. By default, the script only checks the following ports: 20,21,22,23,25,80,443,3389,5900. 

You will need to add the following:
Add additional subnet(s) to the subnet dropdown variable if needed.
Add your Syncro API key into the password variable field. 
The Syncro API key will need permissions to documents (Select All Documentation)

#>

# If you wish to manually Set Variables for the API Calls you can uncomment here
# $customerID = "232518"
# $CustomerName = "Cyncro City"
# $SyncroAPIkey = "API Key"
# $subdomain = "yourSyncroSubdomain"
# $subnet = "192.168.1"


<# Name of used Functions
    - findAndRemoveOldScans -------> deletes any previous scan to prevent clutter of Wiki-Docs
    - update-ArpTable($subnet)  -------> Function to clear and update the ARP table with online Endpoints, takes the $subnet platform dropdown value
    - portChecker($ipaddress)  -------> System.Net.Sockets.TcpClient Object and its BeginConnect() method to attempt a connection to a predefined list of ports
    - ttlCheck($ipaddress)  -------> Checks the TTL Value returned by a Ping Check to hel1p determine Device Type
    - createNetworkTable  -------> Function that gathers all the Network scan data to hold for creating a HTML file
    - createHTML  -------> Function that using the SyncroAPI to create a wiki document with the results from the Network Scan
#>


[string]$today = get-date -format MM/dd/yyyy
# Creates Title for Document Name for Wiki
$name = "Syncro - $CustomerName - Network Scan - $today"


# deletes any previous scan to prevent clutter of Wiki-Docs
Function findAndRemoveOldScans{

    function deleteWikiPage ($wikiID){
        $url = "https://$subdomain.syncromsp.com/api/v1/wiki_pages/$wikiID"
        $reponse = Invoke-RestMethod -Method 'DELETE' -Header $Header -ContentType "application/json"  -Uri $url 
    }

    #Add your subdomain instead of 'hedgesmsp'
    $url = "https://$subdomain.syncromsp.com/api/v1/wiki_pages"

    # Creates Header for API Call
    $Header = @{'Authorization' =" bearer $SyncroAPIkey"}
    $data = Invoke-RestMethod -Method 'GET' -Header $Header -ContentType "application/json"  -Uri $url 
    $x=0
    foreach($page in $data){
        
        write-host "This is the customers name $CustomerName"
        
        $length = $page.wiki_pages.Length
        $search = "$CustomerName - Network Scan"
        
        write-host "this is the search variable $search"

        while($x -lt $length){

            $wikiname = $page.wiki_pages[$x].name
            $wikiID = $page.wiki_pages[$x].id        

            if($wikiname.contains($search)){
                    write-host "$wikiname with id $wikiID contains $search"        
                    write "Deleting Wiki Now"
                    deleteWikiPage ($wikiID)
              }
            $x=$x+1
        } 

    }


}
    
try{findAndRemoveOldScans}
catch{write "no wiki found to delete"} 

# Function to clear and update the ARP table with online Endpoints
function update-ArpTable($subnet) {
    
    # Create UDP Object for Arp Test
    $ASCIIEncoding = New-Object System.Text.ASCIIEncoding
    $Bytes = $ASCIIEncoding.GetBytes("a")
    $UDP = New-Object System.Net.Sockets.Udpclient

    #list of all possible ips on current subnet
    $IPs = 1..254 | % {"$subnet.$_"}
    #$IPs

    if($clearOldConnectionData -eq "yes"){
        #clear old arp table
        arp -d
    }

    # Check for online endpoints
    $IPs | ForEach-Object {    
        #Write-Output "trying $_ "
        $UDP.Connect($_,1)
        [void]$UDP.Send($Bytes,$Bytes.length)
    }

    #display the arp table
    arp -a

    # some reason a 5 to 8 second wait is required for the Get-NetNeighbor to grab the updated info
    Start-Sleep -Seconds 8

    #filter broadcast linklayer address
    $bc = "FF-FF-FF-FF-FF-FF"
    # get subnet neighbors using updated arp table
    $bodyArp = (Get-NetNeighbor -AddressFamily IPv4 -IPAddress *$subnet*  | Where-Object { $_.State -ne "Unreachable"}) | Where-Object { $_.LinkLayerAddress -NotContains $bc } 
    Write-host $bodyArp
    write-host "**********************************************************************************************************************************************"
    return $bodyArp
}

# uses a System.Net.Sockets.TcpClient Object and its BeginConnect() method to attempt a connection to a predefined list of ports found in the 
# variable $portlist. After 100ms if a conneciton was successfull add that port into the Arraylist Object $openList
function portChecker($ipaddress){
    write-host "Starting port check on $ipaddress"
    $portlist = @(20,21,22,23,25,80,443,3389,5900)
          
    $openList = New-Object System.Collections.ArrayList 
    
    foreach($p in $portlist){
        
        $TimeOut = "100"
        $RequestCallback = $State = $Null
        $Client = New-Object System.Net.Sockets.TcpClient
        #Output is avoided
        $Client.BeginConnect($ipaddress,$p,$RequestCallback,$State)|Out-Null

        #Stop the iterative test at 100 ms. 
        Start-Sleep -Milliseconds $TimeOut

        if ($Client.Connected){             
            $openList += $p
            $Client.Close()            
        }
        else{           
            $Client.Close()
        }      
     }     
     
    return $openList
}

# Checks the TTL Value returned by a Ping Check to help determine Device Type
function ttlCheck($ipaddress){
    
    write-host " Trying ttlCheck on ip $ipaddress"
    $ip = $ipaddress

    $TTLtest = (Test-Connection -Count 1 $ip).ResponseTimeToLive

    if($TTLtest -eq "128"){
        $deviceType = "Windows"
    }
    elseif($TTLtest -eq "64"){
        $deviceType = "Linux | MacOS"
    }
    else {
        $deviceType = "Unknown"
    } 
    
    return $deviceType
}

function checkDNSName($ipaddress){    
    $checkName = Resolve-DnsName $ipaddress
    $name = $checkName.NameHost
    return $name

}


# Function that gathers all the Network scan data to hold for creating a HTML file
function createNetworkTable {

    write-host " Starting networktable "
    $x = 0
    $networkTable = @{}

    #Updates the ARP Table
    $updatedArp = update-ArpTable($subnet)  
    
    # Loops each Endpoint in the Arp table
    foreach ($arp in $updatedArp){        
        
        $ipaddress = $arp.ipaddress
        #write-host " Trying createNetworkTable for $ipaddress"

        if($ipaddress){
            #Calls the portChecker function to checks for open ports 
            $openPorts = try{portChecker($ipaddress)} catch{write "error checking ports"}        
            
            #Calls function to check the ttl value and compare it against common known device types
            $ttlDeviceType = try{ttlCheck($ipaddress)} catch{write "error checking ttl"}
             
            $entryArray =@($arp.Ipaddress,$arp.LinkLayerAddress,$arp.State,$ttlDeviceType,$openPorts) 
            
            $dnsname = checkDNSName($ipaddress)
    
            if ($dnsname){
                $Hostname = $dnsname
            }
            else{
                $Hostname = [string]$x+" DNS Lookup Failed"
            }
            $networkTable.add($Hostname,$entryArray)
            
            $x=$x+1
        }
        else{write-host "Ip Address variable was null or blank - $arp "}
    }
    #write-host $networkTable
    return $networkTable
    
}

# Creates a HTML file using Hostname, IPAddress, MacAddress, State, Device Type, Open Ports
function createHTML{
    #HTML Table header
    $html="
    <Html>
    <Body>
    <Table border=1 style='border-collapse: collapse;width:50%;text-align:center'>
    <th>Hostname</th> <th>IPaddress</th> <th>LinkLayerAddress</th> <th>State</th> <th>TTL Value</th> <th>Open Ports</th>"

    #adding HTML table row
    $data = createNetworkTable

    $data = $data.GetEnumerator() 
    $data |ForEach-Object{
        $html += "<tr> <td> $($_.key) </td> <td> $($_.value[0]) </td> <td> $($_.value[1]) </td> <td> $($_.value[2]) </td> <td> $($_.value[3]) </td> <td> $($_.value[4]) </td> </tr>"    
    }
    
    # Check to see if c:\temp folder exist, and create it if not.
    if (!(Test-Path "C:\temp" -PathType Container)) {New-Item -ItemType Directory -Path "C:\temp"}

    #Close HTML tags
    $html +="</table></body></html>"
    $html > C:\temp\wikidoc.html
    return $html
}

# Function that using the SyncroAPI to create a wiki document with the results from the Network Scan
# the Wiki will be attached to that Specific Customer
function Create-WikiPage () {

    <#
    .SYNOPSIS
    This function is used to create a document for a customer in Syncro. 
    .DESCRIPTION
    The function connects to your Syncro environment and creates a document for a customer
    .EXAMPLE
    Create-WikiPage -SyncroSubDomain $SyncroSubDomain -SyncroAPIKey $SyncroAPIkey -customerID $customerID -name $name -body $body
    Creates a new document for a customer in Syncro
    .NOTES
    NAME: Create-WikiPage
    #>

    [cmdletbinding()]

    param
    (
        [Parameter(Mandatory=$true)]
        [string]$subdomain,
        [string]$SyncroAPIKey,
        [string]$customerID,
        [string]$name,
        $body
    )

    $CreatePage =@{
        customer_id = $customerID
        name = $name
        body= $body
        api_key=$SyncroAPIKey
    }

    $body = (ConvertTo-Json $CreatePage)
    $url =  "https://$($subdomain).syncromsp.com/api/v1/wiki_pages"
    $response = Invoke-RestMethod -Uri $url -Method Post -Body $body -ContentType 'application/json'
    $response

}

$html = createHTML

Create-WikiPage -subdomain $subdomain -SyncroAPIKey $SyncroAPIkey -customerID $customerID -name $name -body $html