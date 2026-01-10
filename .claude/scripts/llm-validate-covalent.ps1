#!/usr/bin/env pwsh

param(
    [string]$JsonFile
)

function Validate-Cochart {
    param([string]$JsonFilePath)

    if (-not (Test-Path $JsonFilePath)) {
        Write-Host "Error: File not found: $JsonFilePath"
        exit 1
    }

    try {
        $json = Get-Content $JsonFilePath -Raw | ConvertFrom-Json

        if ($json -isnot [System.Collections.IEnumerable]) {
            Write-Host "Error: JSON root must be an array"
            exit 1
        }

        $errors = 0
        $totalNodes = $json.Count

        Write-Host "======================================"
        Write-Host "COCHART VALIDATION REPORT"
        Write-Host "======================================"
        Write-Host "File: $JsonFilePath"
        Write-Host ""

        # First pass: Schema validation
        Write-Host "--- SCHEMA VALIDATION ---"
        foreach ($node in $json) {
            $id = $node.id
            $nodeType = $node.type

            # Check required label field
            if (-not ($node | Get-Member -Name "label" -ErrorAction SilentlyContinue)) {
                $errors++
                Write-Host "[ERROR] Node $id`: Missing required label"
            }

            if ($nodeType -eq "todo") {
                # TODO node validation
                if ($node | Get-Member -Name "lineNumber" -ErrorAction SilentlyContinue) {
                    $errors++
                    Write-Host "[ERROR] Node $id`: TODO node should not have lineNumber"
                }
                if ($node | Get-Member -Name "filePath" -ErrorAction SilentlyContinue) {
                    $errors++
                    Write-Host "[ERROR] Node $id`: TODO node should not have filePath"
                }
            } elseif ($nodeType -and $nodeType -ne "todo") {
                # Invalid type
                $errors++
                Write-Host "[ERROR] Node $id`: Invalid type '$nodeType' (only 'todo' allowed)"
            } else {
                # CODE node validation
                if (-not ($node | Get-Member -Name "lineNumber" -ErrorAction SilentlyContinue)) {
                    $errors++
                    Write-Host "[ERROR] Node $id`: CODE node missing lineNumber"
                }
                if (-not ($node | Get-Member -Name "filePath" -ErrorAction SilentlyContinue)) {
                    $errors++
                    Write-Host "[ERROR] Node $id`: CODE node missing filePath"
                }
            }
        }

        # Second pass: Content validation
        Write-Host ""
        Write-Host "--- CONTENT VALIDATION ---"
        $codeNodes = $json | Where-Object { $_.type -ne "todo" }

        foreach ($node in $codeNodes) {
            $id = $node.id
            $label = $node.label
            $filePath = $node.filePath
            $lineNumber = $node.lineNumber
            $lineContent = $node.lineContent

            $baseDir = Split-Path -Parent $JsonFilePath
            $fullPath = [System.IO.Path]::Combine($baseDir, "..", "..", $filePath)
            $fullPath = [System.IO.Path]::GetFullPath($fullPath)

            $checked++

            if (-not (Test-Path $fullPath)) {
                $errors++
                Write-Host "[ERROR] Node $id`: File not found at $fullPath"
            } else {
                $fileContent = Get-Content $fullPath -Raw
                $lines = $fileContent -split "`n"
                $lineNum = [int]$lineNumber

                if ($lineNum -lt 1 -or $lineNum -gt $lines.Length) {
                    $errors++
                    Write-Host "[ERROR] Node $id`: Line $lineNum out of range (file has $($lines.Length) lines)"
                } else {
                    $actualLine = $lines[$lineNum - 1].Trim()
                    $expectedLine = $lineContent.Trim()

                    if ($actualLine -ne $expectedLine) {
                        $errors++
                        Write-Host "[ERROR] Node $id`: Line content mismatch"
                        Write-Host "  Expected: `"$expectedLine`""
                        Write-Host "  Actual:   `"$actualLine`""
                    }
                }
            }
        }

        Write-Host ""
        Write-Host "======================================"
        Write-Host "Checked: $checked CODE nodes"
        Write-Host "Errors: $errors"
        Write-Host "======================================"

        return ($errors -eq 0)
    } catch {
        Write-Host "Error reading/parsing JSON: $_"
        exit 1
    }
}

if (-not $JsonFile) {
    Write-Host "Usage: pwsh -ExecutionPolicy Bypass -File validate-covalent.ps1 <cochart-file.json>"
    exit 1
}

Validate-Cochart -JsonFilePath $JsonFile
