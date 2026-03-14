#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

python -m pip install -U pip
pip install -e .[dev]

Write-Host "Environment bootstrapped."
