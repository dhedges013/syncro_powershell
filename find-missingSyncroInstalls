Import-Module $env:SyncroModule
<#

**UPDATED** This powershell script will generate alerts inside Syncro, if Windows endpoints potentially do not have Syncro Installed. Script works by comparing MAC addresses of Windows endpoints found on the LAN vs the current list of all assets' MAC addresses listed for customer, as reported by the Syncro API. ICMP needs to be enabled on endpoints. The script can report false positives as well as miss online machines without Syncro. Please follow the directions below:

Add the following:
Add subnets to the dropdown variable. Only Class C addresses will work
Add your Syncro API Key with the following permissions:

Assets - View Details
Assets - List/Search
RMM Alerts - List
RMM Alerts - Create


#>

# This Script uses Test-Connection cmd to gather info about endpoints. If ICMP is not allowed on those endpoints
# the results of this script are limited. If you are unable to enable ICMP, look for the Network Discovery script
# in the community library which works even if ICMP is disabled.

# In the scrips Password and Dropdown Variables please set:
# Syncro API Key for this script to work
# Add the correct subnet

<#
Syncro Script Variables:

************* platform **************
$subdomain -----> Used in Syncro API Call
$SyncroCustomerNumber ----> Used in the Syncro API Call

************* Dropdowns **************
$subnet ----> a dropdown for subnet needs to be used. User will need to add their subnets to the variable if not one of the default ones provided. Only takes a Class C Address 

************* Password **************
$syncroAPIkey ----> a API key that has the following permissions

Assets - View Details
Assets - List/Search
RMM Alerts - List
RMM Alerts - Create

#>

# Set Syncro API Key for API Call
# $syncroAPIkey = " " #Syncro API Key Uncomment to override runtime / platform variable

$Header = @{'Authorization' =" bearer $syncroAPIkey"}

#URL for API Return of All Assets for Customer
$assetUrl = "https://"+$subdomain+".syncromsp.com/api/v1/customer_assets?customer_id=" + $SyncroCustomerNumber

#Asset Data returned by the API
$assetData = Invoke-RestMethod -Method 'GET' -Header $Header -ContentType "application/json"  -Uri $assetUrl

#List of MAC addresses for Current Assets From Customer
$listofMacs = $assetData.assets.properties.kabuto_information.network_adapters.physical_address

#write-host "this is a list of macs in Syncro for $company" #Uncomment For Troubleshooting
#write-host $listofMacs

# region Clearing and updating the ARP Table

# Updating the ARP Table will allow for faster and targeted Test-Connection calls. Test-Connection is to slow if it loops though all possible ip address
# Create Objects for UDP Arp Test
$ASCIIEncoding = New-Object System.Text.ASCIIEncoding
$Bytes = $ASCIIEncoding.GetBytes("a")
$UDP = New-Object System.Net.Sockets.Udpclient

#list of all possible ips on current subnet
$IPs = 1..254 | % {"$subnet.$_"}

#clear old arp table
arp -d

#Write-host "List of IPS" #write-host $IPs # Can uncomment for Troubleshooting 

# Check for online endpoints
$IPs | ForEach-Object {    
    #Write-Output "trying $_ " #Uncomment for console output for troubleshooting
    $UDP.Connect($_,1)
    [void]$UDP.Send($Bytes,$Bytes.length)
}

#Update the arp table
arp -a

# some reason a 5 second wait helps the Get-NetNeighbor to grab the updated info more constantly
Start-Sleep -Seconds 5

# get-Netneighbors will pull the updated ARP endpoints using updated arp table, and filter out any that are Unreachable
$body = (Get-NetNeighbor -AddressFamily IPv4 -IPAddress *$subnet*  | Where-Object { $_.State -ne "Unreachable"})

#endregion

# Function to do a DNS Query for Computers Name to add to the RMM Alert
Function checkDNSName($ip){    
    $checkName = Resolve-DnsName $ip
    $name = $checkName.NameHost
    return $name
}

# Loop and check if current active LAN endpoints that are Windows Machines have their MAC Addresses
# Already in Syncro, If not create Alerts

#Create Arraylist to hold any missing machine data. To be used in RMM Alert
$missingMachines =@()


$body | Foreach-object{   
        
    $ip = $_.IPAddress
    $mac = $_.LinkLayerAddress

    #write-host "Testing IP - "$ip # Can uncomment for Troubleshooting 
    
    # When running a ping test like Test-Connection, a value called TTL is returned, based on industry standards you are
    # able to tell if the endpoint is running a Windows OS vs Linux/Others. TTL value is 128 indicates Windows Device
    $TTLtest = (Test-Connection -Count 1 $ip).ResponseTimeToLive
    if($TTLtest -eq "128"){
        
        #write-host "TTL for $ip is $TTLtest, Windows Machine found. Checking to see if in Syncro "
        #write-host " Checking Syncro list of Macs"
        if( $listofMacs -contains $mac){
            write-host " $mac is in Syncro list of Macs $listofMacs "            
        }
        else{
            #write-host " $mac not found in list of Macs $listofMacs "  #Can uncomment for Troubleshooting 
            
            # Find the DNS Name of the IP address and build a string to add to the missingMachine Array that will be used for the Alert
            $missingComputer = checkDNSName($ip)
            $missingComputer = $missingComputer + " at " + $ip + " | "
            $missingMachines += $missingComputer          
        }
    }
    #write-host ($missingMachines) #Can uncomment for troubleshooting
    
}

# Generate RMM Alert if the $missingMachines variable is not null, else output to console
if($missingMachines){
    Rmm-Alert -Category "Missing Syncro" -Body "$missingMachines are Online Windows Machines that could be missing Syncro"
    Log-Activity -Message "Missing Syncro Windows Machines Found $missingMachines" -EventName "Check Syncro Installs"
}
else{
    Log-Activity -Message "No machine found missing Syncro" -EventName "Check Syncro Installs"
    write-host " No missing Syncro installs detected"    
}