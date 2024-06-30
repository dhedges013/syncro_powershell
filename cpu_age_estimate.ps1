<#

CPU Age Estimate with Error Catching


This script requires a Custom Asset Field called "CPU Age Years". You can Add this field in the Admin Section of your Syncro Account

A good estimate for the age of a business computer is the release date of the installed CPU, since the computer cannot be older than this date.
This is especially useful knowledge if computer's warranty information or actual purchase date is not available.
This powershell script uses cpubenchmark.net and the CPU's name to estimate the computer's age based off the CPU Model's release date.
You can offset the calculated Estimated Age from the Model's release date using the $date_adjustment variable.

Example of using $date_adjustment variable:

The CPU model was released in 2020 Q1, but purchase date of the computer was sometime in 2021. Use the 12 month dropdown value
to start counting CPU_Age from 2021 Q1 which should be much closer to actual purchase date than 2020 Q1.

To test outside of your Syncro account please declare the platform variables 

Platform Variables:
$cpu_name - {{asset_custom_field_cpu_name}}

Dropdown Variables:
$date_adjustment -
    6 Months - Default value
    12 Months
    18 Months
    0 Months

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
            $text = $paragraph.innerText
            if ($text -match "Charts:") {
                # Extract text after "Charts:" and remove leading space
                $releaseDate = $text -replace ".*Charts:\s*(.*)", '$1'
                Write-Host $releaseDate
            }
        }
    } else {
        Write-Output "No <p> elements found."
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

    try {
        $totalMonths = (($currentDateTime.Year - $launchDateTime.Year) * 12) + ($currentDateTime.Month - $launchDateTime.Month)
        $totalYears = [math]::Round($totalMonths / 12, 1)
    }
    catch {
        $totalYears = "unknown"
    }

    if ($totalYears -eq "unknown" -or $totalYears -gt 20) {
        $totalYears = "unknown"
    }

    Write-Host "Maximum Age of Computer estimated to be $totalYears years"
    
    if($date_adjustment -eq "0 Months"){
        Write-Host "Age Adjustment of $date_adjustment factored in"
        $totalYears = $totalYears 
        
    }
    elseif($date_adjustment -eq "6 Months"){
        Write-Host "Age Adjustment of $date_adjustment factored in"
        $totalYears = $totalYears - .5
        
    }
    elseif($date_adjustment -eq "12 Months"){
        Write-Host "Age Adjustment of $date_adjustment factored in"
        $totalYears = $totalYears - 1
        
    }
    else{
        Write-Host "Age Adjustment of $date_adjustment factored in"
        $totalYears = $totalYears - 1.5
        
    }

    Set-Asset-Field -Name "CPU Age Years" -Value "$totalYears"
    Log-Activity -Message "The CPU Age is estimated at $totalYears years. Adjustment of $date_adjustment was factored in" -EventName "CPU Age"

} else {
    Write-Output "Failed to fetch webpage. Status code: $($response.StatusCode)"
    Log-Activity -Message "Error Checking CPU Age" -EventName "CPU Age"
}
