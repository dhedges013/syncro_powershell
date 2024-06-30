<#
To test outside of your Syncro account please declare the platform variables 

Platform Variables:
$cpu_name - {{asset_custom_field_cpu_name}}

#>

Import-Module $env:SyncroModule

# Define the base URL and the CPU name
$baseURL = "https://www.cpubenchmark.net/cpu.php?cpu="
# URL-encode the CPU name
$encodedCpuName = [uri]::EscapeDataString($cpu_name)
# Fetch the webpage content
$response = Invoke-WebRequest -Uri ($baseURL + $encodedCpuName) -UseBasicParsing

# Check if the request was successful
if ($response.StatusCode -eq 200) {
    # Decode the HTML content
    $decodedHtml = [System.Net.WebUtility]::HtmlDecode($response.Content)

    # Parse the HTML content
    $htmlDocument = New-Object -ComObject "HTMLFile"
    #$htmlDocument.IHTMLDocument2_write($decodedHtml)  
    
    try {
        # This works in PowerShell with Office installed
        $htmlDocument.IHTMLDocument2_write($decodedHtml)
    }
    catch {
        # This works when Office is not installed    
        $src = [System.Text.Encoding]::Unicode.GetBytes($decodedHtml)
        $htmlDocument.write($src)
    }

    # Get all <p> elements
    $paragraphs = $htmlDocument.getElementsByTagName("p")

    # Output the content of each <p> element
    if ($paragraphs) {
        foreach ($paragraph in $paragraphs) {
            #Write-Output $paragraph.innerText
            $text = $paragraph.innerText
            if ($text -match "Charts:") {
                # Extract text after "Charts:" and remove leading space
                $releaseDate = $text -replace ".*Charts:\s*(.*)", '$1'
                write-host $releaseDate                
            }
        }
    } else {
        Write-Output "No <p> elements found."
    }
} else {
    Write-Output "Failed to fetch webpage. Status code: $($response.StatusCode)"
}

# Function to calculate CPU age
$quarterToMonth = @{
    "Q1" = 1   # January
    "Q2" = 4   # April
    "Q3" = 7   # July
    "Q4" = 10  # October
}

$quarter, $year = $releaseDate -split " "
$month = $quarterToMonth[$quarter]
$year = [int]$year

$launchDateTime = Get-Date -Year $year -Month $month -Day 1
$currentDateTime = Get-Date

$totalMonths = (($currentDateTime.Year - $launchDateTime.Year) * 12) + ($currentDateTime.Month - $launchDateTime.Month)
$totalYears = [math]::Round($totalMonths / 12, 1)

write-host $totalYears

Set-Asset-Field -Name "CPU Age Years" -Value "$totalYears"
Log-Activity -Message "The CPU Age is estimated at $totalYears years" -EventName "CPU Age"
