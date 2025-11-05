<#
.SYNOPSIS
  Comprehensive Test Suite for ZeroUI Folder Structure Scripts

.DESCRIPTION
  Tests all create and delete scripts for each environment:
  - create-folder-structure-development.ps1
  - create-folder-structure-integration.ps1
  - create-folder-structure-staging.ps1
  - create-folder-structure-production.ps1
  - delete-folder-structure-development.ps1
  - delete-folder-structure-integration.ps1
  - delete-folder-structure-staging.ps1
  - delete-folder-structure-production.ps1
  - delete-folder-structure.ps1

.PARAMETER TestRoot
  Root directory for test execution. Default: "D:\ZeroUI-Test"

.PARAMETER SkipCleanup
  If specified, does not clean up test directories after execution.

.EXAMPLE
  .\test-all-scripts.ps1
  .\test-all-scripts.ps1 -TestRoot "E:\Test-ZeroUI"
  .\test-all-scripts.ps1 -SkipCleanup
  .\test-all-scripts.ps1 -Verbose

.NOTES
  Version: 2.0
  Based on: folder-business-rules.md
#>

[CmdletBinding()]
param(
    [string]$TestRoot = "D:\ZeroUI-Test",
    [switch]$SkipCleanup
)

$ErrorActionPreference = "Stop"

# Script paths
$parentDir = Split-Path $PSScriptRoot -Parent
$scriptRoot = Join-Path $parentDir "tools"
if(-not (Test-Path $scriptRoot)) {
    Write-Error "Script root not found: $scriptRoot"
    exit 1
}
$scriptRoot = (Resolve-Path $scriptRoot).Path

# Test results
$testResults = @()
$totalTests = 0
$passedTests = 0
$failedTests = 0

# Helper function to record test result
function Record-TestResult {
    param(
        [string]$TestName,
        [bool]$Passed,
        [string]$Message = "",
        [string]$ErrorDetails = ""
    )
    
    $script:totalTests++
    if($Passed) {
        $script:passedTests++
        Write-Host "[PASS] $TestName" -ForegroundColor Green
        if($Message) {
            Write-Host "      $Message" -ForegroundColor Gray
        }
    } else {
        $script:failedTests++
        Write-Host "[FAIL] $TestName" -ForegroundColor Red
        if($Message) {
            Write-Host "      $Message" -ForegroundColor Yellow
        }
        if($ErrorDetails) {
            Write-Host "      Error: $ErrorDetails" -ForegroundColor Red
        }
    }
    
    $script:testResults += @{
        TestName = $TestName
        Passed = $Passed
        Message = $Message
        ErrorDetails = $ErrorDetails
        Timestamp = Get-Date
    }
}

# Helper function to test if folder structure exists
function Test-EnvironmentStructure {
    param(
        [string]$BasePath,
        [string]$Environment,
        [bool]$IncludeIDE = $false
    )
    
    $envPath = Join-Path $BasePath $Environment
    if(-not (Test-Path $envPath)) {
        return $false
    }
    
    # Test tenant plane
    $tenantPath = Join-Path $envPath "tenant"
    if(-not (Test-Path $tenantPath)) {
        return $false
    }
    
    # Test product plane
    $productPath = Join-Path $envPath "product"
    if(-not (Test-Path $productPath)) {
        return $false
    }
    
    # Test shared plane
    $sharedPath = Join-Path $envPath "shared"
    if(-not (Test-Path $sharedPath)) {
        return $false
    }
    
    # Test IDE plane if required
    if($IncludeIDE) {
        $idePath = Join-Path $envPath "ide"
        if(-not (Test-Path $idePath)) {
            return $false
        }
    }
    
    return $true
}

# Helper function to test if folder structure is deleted
function Test-EnvironmentDeleted {
    param(
        [string]$BasePath,
        [string]$Environment
    )
    
    $envPath = Join-Path $BasePath $Environment
    return -not (Test-Path $envPath)
}

# Helper function to run script and capture output
function Invoke-TestScript {
    param(
        [string]$ScriptPath,
        [hashtable]$Parameters = @{},
        [bool]$ExpectSuccess = $true
    )
    
    try {
        # Build parameter hashtable for splatting
        $splatParams = @{}
        foreach($key in $Parameters.Keys) {
            $value = $Parameters[$key]
            if($value -is [switch]) {
                if($value.IsPresent) {
                    $splatParams[$key] = $true
                }
            } elseif($value -is [bool] -and $value) {
                # Handle boolean as switch
                $splatParams[$key] = $true
            } elseif($value -is [string] -and $value) {
                $splatParams[$key] = $value
            }
        }
        
        if($VerbosePreference -eq 'Continue') {
            $paramDisplay = ($splatParams.Keys | ForEach-Object { "-$_" + $(if($splatParams[$_] -is [string]) { " `"$($splatParams[$_])`"" } else { "" }) }) -join " "
            Write-Host "      Executing: & `"$ScriptPath`" $paramDisplay" -ForegroundColor Gray
        }
        
        $output = & $ScriptPath @splatParams 2>&1
        $exitCode = $LASTEXITCODE
        
        if($ExpectSuccess -and $exitCode -eq 0) {
            return @{Success = $true; Output = $output; ExitCode = $exitCode}
        } elseif(-not $ExpectSuccess -and $exitCode -ne 0) {
            return @{Success = $true; Output = $output; ExitCode = $exitCode}
        } else {
            return @{Success = $false; Output = $output; ExitCode = $exitCode}
        }
    } catch {
        return @{Success = $false; Output = $_.Exception.Message; ExitCode = -1}
    }
}

# Cleanup function
function Clear-TestDirectory {
    param(
        [string]$Path
    )
    
    if(Test-Path $Path) {
        try {
            Remove-Item -Path $Path -Recurse -Force -ErrorAction Stop
            return $true
        } catch {
            return $false
        }
    }
    return $true
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "ZeroUI Folder Structure Scripts Test Suite" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan
Write-Host "Test Root: $TestRoot" -ForegroundColor Cyan
Write-Host "Script Root: $scriptRoot`n" -ForegroundColor Cyan

# ============================================================================
# Test 1: Create Development Environment
# ============================================================================
Write-Host "`n[TEST GROUP 1] Development Environment Creation" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Yellow

$testPath = Join-Path $TestRoot "dev-test"
Clear-TestDirectory -Path $testPath | Out-Null

$scriptPath = Join-Path $scriptRoot "create-folder-structure-development.ps1"
if(Test-Path $scriptPath) {
    $result = Invoke-TestScript -ScriptPath $scriptPath -Parameters @{
        ZuRoot = $testPath
    }
    
    if($result.Success) {
        $structureExists = Test-EnvironmentStructure -BasePath $testPath -Environment "development" -IncludeIDE $true
        Record-TestResult -TestName "Create Development Environment" -Passed $structureExists `
            -Message "Created development environment with IDE, tenant, product, and shared planes"
    } else {
        Record-TestResult -TestName "Create Development Environment" -Passed $false `
            -ErrorDetails "Script execution failed: $($result.Output)"
    }
} else {
    Record-TestResult -TestName "Create Development Environment Script Exists" -Passed $false `
        -ErrorDetails "Script not found: $scriptPath"
}

# Test with parameters
$testPath2 = Join-Path $TestRoot "dev-test-params"
Clear-TestDirectory -Path $testPath2 | Out-Null

if(Test-Path $scriptPath) {
    $result = Invoke-TestScript -ScriptPath $scriptPath -Parameters @{
        Drive = "D"
        ProductName = "TestProduct"
        ZuRoot = $testPath2
    }
    
    if($result.Success) {
        $structureExists = Test-EnvironmentStructure -BasePath $testPath2 -Environment "development" -IncludeIDE $true
        Record-TestResult -TestName "Create Development with Parameters" -Passed $structureExists `
            -Message "Created with Drive and ProductName parameters"
    } else {
        Record-TestResult -TestName "Create Development with Parameters" -Passed $false `
            -ErrorDetails "Script execution failed: $($result.Output)"
    }
}

# ============================================================================
# Test 2: Create Integration Environment
# ============================================================================
Write-Host "`n[TEST GROUP 2] Integration Environment Creation" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Yellow

$testPath = Join-Path $TestRoot "int-test"
Clear-TestDirectory -Path $testPath | Out-Null

$scriptPath = Join-Path $scriptRoot "create-folder-structure-integration.ps1"
if(Test-Path $scriptPath) {
    $result = Invoke-TestScript -ScriptPath $scriptPath -Parameters @{
        ZuRoot = $testPath
    }
    
    if($result.Success) {
        $structureExists = Test-EnvironmentStructure -BasePath $testPath -Environment "integration" -IncludeIDE $false
        Record-TestResult -TestName "Create Integration Environment" -Passed $structureExists `
            -Message "Created integration environment with tenant, product, and shared planes (no IDE)"
    } else {
        Record-TestResult -TestName "Create Integration Environment" -Passed $false `
            -ErrorDetails "Script execution failed: $($result.Output)"
    }
} else {
    Record-TestResult -TestName "Create Integration Environment Script Exists" -Passed $false `
        -ErrorDetails "Script not found: $scriptPath"
}

# ============================================================================
# Test 3: Create Staging Environment
# ============================================================================
Write-Host "`n[TEST GROUP 3] Staging Environment Creation" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Yellow

$testPath = Join-Path $TestRoot "staging-test"
Clear-TestDirectory -Path $testPath | Out-Null

$scriptPath = Join-Path $scriptRoot "create-folder-structure-staging.ps1"
if(Test-Path $scriptPath) {
    $result = Invoke-TestScript -ScriptPath $scriptPath -Parameters @{
        ZuRoot = $testPath
    }
    
    if($result.Success) {
        $structureExists = Test-EnvironmentStructure -BasePath $testPath -Environment "staging" -IncludeIDE $false
        Record-TestResult -TestName "Create Staging Environment" -Passed $structureExists `
            -Message "Created staging environment with tenant, product, and shared planes (no IDE)"
    } else {
        Record-TestResult -TestName "Create Staging Environment" -Passed $false `
            -ErrorDetails "Script execution failed: $($result.Output)"
    }
} else {
    Record-TestResult -TestName "Create Staging Environment Script Exists" -Passed $false `
        -ErrorDetails "Script not found: $scriptPath"
}

# ============================================================================
# Test 4: Create Production Environment
# ============================================================================
Write-Host "`n[TEST GROUP 4] Production Environment Creation" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Yellow

$testPath = Join-Path $TestRoot "prod-test"
Clear-TestDirectory -Path $testPath | Out-Null

$scriptPath = Join-Path $scriptRoot "create-folder-structure-production.ps1"
if(Test-Path $scriptPath) {
    $result = Invoke-TestScript -ScriptPath $scriptPath -Parameters @{
        ZuRoot = $testPath
    }
    
    if($result.Success) {
        $structureExists = Test-EnvironmentStructure -BasePath $testPath -Environment "production" -IncludeIDE $false
        Record-TestResult -TestName "Create Production Environment" -Passed $structureExists `
            -Message "Created production environment with tenant, product, and shared planes (no IDE)"
    } else {
        Record-TestResult -TestName "Create Production Environment" -Passed $false `
            -ErrorDetails "Script execution failed: $($result.Output)"
    }
} else {
    Record-TestResult -TestName "Create Production Environment Script Exists" -Passed $false `
        -ErrorDetails "Script not found: $scriptPath"
}

# ============================================================================
# Test 5: Delete Development Environment
# ============================================================================
Write-Host "`n[TEST GROUP 5] Development Environment Deletion" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Yellow

# First create it
$testPath = Join-Path $TestRoot "dev-delete-test"
Clear-TestDirectory -Path $testPath | Out-Null

$createScript = Join-Path $scriptRoot "create-folder-structure-development.ps1"
if(Test-Path $createScript) {
    Invoke-TestScript -ScriptPath $createScript -Parameters @{ZuRoot = $testPath} | Out-Null
    
    # Now delete it
    $deleteScript = Join-Path $scriptRoot "delete-folder-structure-development.ps1"
    if(Test-Path $deleteScript) {
        $result = Invoke-TestScript -ScriptPath $deleteScript -Parameters @{
            ZuRoot = $testPath
            Force = $true
        }
        
        if($result.Success) {
            $isDeleted = Test-EnvironmentDeleted -BasePath $testPath -Environment "development"
            Record-TestResult -TestName "Delete Development Environment" -Passed $isDeleted `
                -Message "Deleted development environment successfully"
        } else {
            Record-TestResult -TestName "Delete Development Environment" -Passed $false `
                -ErrorDetails "Script execution failed: $($result.Output)"
        }
    } else {
        Record-TestResult -TestName "Delete Development Environment Script Exists" -Passed $false `
            -ErrorDetails "Script not found: $deleteScript"
    }
}

# Test WhatIf mode
$testPath2 = Join-Path $TestRoot "dev-delete-whatif"
Clear-TestDirectory -Path $testPath2 | Out-Null

if(Test-Path $createScript) {
    Invoke-TestScript -ScriptPath $createScript -Parameters @{ZuRoot = $testPath2} | Out-Null
    
    if(Test-Path $deleteScript) {
        $result = Invoke-TestScript -ScriptPath $deleteScript -Parameters @{
            ZuRoot = $testPath2
            WhatIf = $true
        }
        
        if($result.Success) {
            # Structure should still exist after WhatIf
            $stillExists = Test-EnvironmentStructure -BasePath $testPath2 -Environment "development" -IncludeIDE $true
            Record-TestResult -TestName "Delete Development WhatIf Mode" -Passed $stillExists `
                -Message "WhatIf mode did not delete structure (as expected)"
        } else {
            Record-TestResult -TestName "Delete Development WhatIf Mode" -Passed $false `
                -ErrorDetails "Script execution failed: $($result.Output)"
        }
    }
}

# ============================================================================
# Test 6: Delete Integration Environment
# ============================================================================
Write-Host "`n[TEST GROUP 6] Integration Environment Deletion" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Yellow

$testPath = Join-Path $TestRoot "int-delete-test"
Clear-TestDirectory -Path $testPath | Out-Null

$createScript = Join-Path $scriptRoot "create-folder-structure-integration.ps1"
if(Test-Path $createScript) {
    Invoke-TestScript -ScriptPath $createScript -Parameters @{ZuRoot = $testPath} | Out-Null
    
    $deleteScript = Join-Path $scriptRoot "delete-folder-structure-integration.ps1"
    if(Test-Path $deleteScript) {
        $result = Invoke-TestScript -ScriptPath $deleteScript -Parameters @{
            ZuRoot = $testPath
            Force = $true
        }
        
        if($result.Success) {
            $isDeleted = Test-EnvironmentDeleted -BasePath $testPath -Environment "integration"
            Record-TestResult -TestName "Delete Integration Environment" -Passed $isDeleted `
                -Message "Deleted integration environment successfully"
        } else {
            Record-TestResult -TestName "Delete Integration Environment" -Passed $false `
                -ErrorDetails "Script execution failed: $($result.Output)"
        }
    } else {
        Record-TestResult -TestName "Delete Integration Environment Script Exists" -Passed $false `
            -ErrorDetails "Script not found: $deleteScript"
    }
}

# ============================================================================
# Test 7: Delete Staging Environment
# ============================================================================
Write-Host "`n[TEST GROUP 7] Staging Environment Deletion" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Yellow

$testPath = Join-Path $TestRoot "staging-delete-test"
Clear-TestDirectory -Path $testPath | Out-Null

$createScript = Join-Path $scriptRoot "create-folder-structure-staging.ps1"
if(Test-Path $createScript) {
    Invoke-TestScript -ScriptPath $createScript -Parameters @{ZuRoot = $testPath} | Out-Null
    
    $deleteScript = Join-Path $scriptRoot "delete-folder-structure-staging.ps1"
    if(Test-Path $deleteScript) {
        $result = Invoke-TestScript -ScriptPath $deleteScript -Parameters @{
            ZuRoot = $testPath
            Force = $true
        }
        
        if($result.Success) {
            $isDeleted = Test-EnvironmentDeleted -BasePath $testPath -Environment "staging"
            Record-TestResult -TestName "Delete Staging Environment" -Passed $isDeleted `
                -Message "Deleted staging environment successfully"
        } else {
            Record-TestResult -TestName "Delete Staging Environment" -Passed $false `
                -ErrorDetails "Script execution failed: $($result.Output)"
        }
    } else {
        Record-TestResult -TestName "Delete Staging Environment Script Exists" -Passed $false `
            -ErrorDetails "Script not found: $deleteScript"
    }
}

# ============================================================================
# Test 8: Delete Production Environment
# ============================================================================
Write-Host "`n[TEST GROUP 8] Production Environment Deletion" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Yellow

$testPath = Join-Path $TestRoot "prod-delete-test"
Clear-TestDirectory -Path $testPath | Out-Null

$createScript = Join-Path $scriptRoot "create-folder-structure-production.ps1"
if(Test-Path $createScript) {
    Invoke-TestScript -ScriptPath $createScript -Parameters @{ZuRoot = $testPath} | Out-Null
    
    $deleteScript = Join-Path $scriptRoot "delete-folder-structure-production.ps1"
    if(Test-Path $deleteScript) {
        $result = Invoke-TestScript -ScriptPath $deleteScript -Parameters @{
            ZuRoot = $testPath
            Force = $true
        }
        
        if($result.Success) {
            $isDeleted = Test-EnvironmentDeleted -BasePath $testPath -Environment "production"
            Record-TestResult -TestName "Delete Production Environment" -Passed $isDeleted `
                -Message "Deleted production environment successfully"
        } else {
            Record-TestResult -TestName "Delete Production Environment" -Passed $false `
                -ErrorDetails "Script execution failed: $($result.Output)"
        }
    } else {
        Record-TestResult -TestName "Delete Production Environment Script Exists" -Passed $false `
            -ErrorDetails "Script not found: $deleteScript"
    }
}

# ============================================================================
# Test 9: Main Delete Script (All Environments)
# ============================================================================
Write-Host "`n[TEST GROUP 9] Main Delete Script (All Environments)" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Yellow

$testPath = Join-Path $TestRoot "main-delete-test"
Clear-TestDirectory -Path $testPath | Out-Null

# Create all environments first
$createScripts = @(
    @{Script = "create-folder-structure-development.ps1"; Env = "development"},
    @{Script = "create-folder-structure-integration.ps1"; Env = "integration"},
    @{Script = "create-folder-structure-staging.ps1"; Env = "staging"},
    @{Script = "create-folder-structure-production.ps1"; Env = "production"}
)

foreach($createInfo in $createScripts) {
    $scriptPath = Join-Path $scriptRoot $createInfo.Script
    if(Test-Path $scriptPath) {
        Invoke-TestScript -ScriptPath $scriptPath -Parameters @{ZuRoot = $testPath} | Out-Null
    }
}

# Test main delete script
$deleteScript = Join-Path $scriptRoot "delete-folder-structure.ps1"
if(Test-Path $deleteScript) {
    $result = Invoke-TestScript -ScriptPath $deleteScript -Parameters @{
        ZuRoot = $testPath
        Force = $true
    }
    
    if($result.Success) {
        $allDeleted = $true
        foreach($env in @("development", "integration", "staging", "production")) {
            if(-not (Test-EnvironmentDeleted -BasePath $testPath -Environment $env)) {
                $allDeleted = $false
                break
            }
        }
        
        Record-TestResult -TestName "Delete All Environments (Main Script)" -Passed $allDeleted `
            -Message "Deleted all four environments using main delete script"
    } else {
        Record-TestResult -TestName "Delete All Environments (Main Script)" -Passed $false `
            -ErrorDetails "Script execution failed: $($result.Output)"
    }
} else {
    Record-TestResult -TestName "Main Delete Script Exists" -Passed $false `
        -ErrorDetails "Script not found: $deleteScript"
}

# ============================================================================
# Test 10: Parameter Validation
# ============================================================================
Write-Host "`n[TEST GROUP 10] Parameter Validation" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Yellow

$testPath = Join-Path $TestRoot "param-test"
Clear-TestDirectory -Path $testPath | Out-Null

# Test with Drive and ProductName parameters
$scriptPath = Join-Path $scriptRoot "create-folder-structure-development.ps1"
if(Test-Path $scriptPath) {
    $result = Invoke-TestScript -ScriptPath $scriptPath -Parameters @{
        Drive = "D"
        ProductName = "ParamTest"
        ZuRoot = $testPath
    }
    
    Record-TestResult -TestName "Parameter Validation (Drive/ProductName)" -Passed $result.Success `
        -Message "Script accepts Drive and ProductName parameters"
}

# Test with ZuRoot parameter
$testPath2 = Join-Path $TestRoot "param-test-zuroot"
Clear-TestDirectory -Path $testPath2 | Out-Null

if(Test-Path $scriptPath) {
    $result = Invoke-TestScript -ScriptPath $scriptPath -Parameters @{
        ZuRoot = $testPath2
    }
    
    Record-TestResult -TestName "Parameter Validation (ZuRoot)" -Passed $result.Success `
        -Message "Script accepts ZuRoot parameter"
}

# ============================================================================
# Test 11: Error Handling
# ============================================================================
Write-Host "`n[TEST GROUP 11] Error Handling" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Yellow

# Test delete on non-existent path
$nonExistentPath = Join-Path $TestRoot "non-existent"
$deleteScript = Join-Path $scriptRoot "delete-folder-structure-development.ps1"
if(Test-Path $deleteScript) {
    $result = Invoke-TestScript -ScriptPath $deleteScript -Parameters @{
        ZuRoot = $nonExistentPath
        Force = $true
    } -ExpectSuccess $true  # Should handle gracefully
    
    Record-TestResult -TestName "Error Handling (Non-existent Path)" -Passed $result.Success `
        -Message "Script handles non-existent path gracefully"
}

# ============================================================================
# Test Summary
# ============================================================================
Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $failedTests" -ForegroundColor $(if($failedTests -eq 0) { "Green" } else { "Red" })
Write-Host "Success Rate: $([math]::Round(($passedTests / $totalTests) * 100, 2))%" -ForegroundColor $(if($failedTests -eq 0) { "Green" } else { "Yellow" })

if($failedTests -gt 0) {
    Write-Host "`nFailed Tests:" -ForegroundColor Red
    $testResults | Where-Object { -not $_.Passed } | ForEach-Object {
        Write-Host "  - $($_.TestName)" -ForegroundColor Red
        if($_.ErrorDetails) {
            Write-Host "    $($_.ErrorDetails)" -ForegroundColor Yellow
        }
    }
}

# Cleanup
if(-not $SkipCleanup) {
    Write-Host "`nCleaning up test directories..." -ForegroundColor Cyan
    if(Test-Path $TestRoot) {
        Clear-TestDirectory -Path $TestRoot
        Write-Host "Test directories cleaned up." -ForegroundColor Green
    }
}

if($failedTests -eq 0) {
    Write-Host "`nAll tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`nSome tests failed. Please review the output above." -ForegroundColor Red
    exit 1
}

