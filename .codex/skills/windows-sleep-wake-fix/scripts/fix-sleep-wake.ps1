#Requires -RunAsAdministrator
<#
.SYNOPSIS
  절전 모드에서 깨어난 뒤 잠금/로그인 화면이 멈추는 문제를 예방하는 설정을 적용합니다.

.DESCRIPTION
  1. 빠른 시작(Fast Startup) 끄기
  2. USB 선택적 절전 끄기 (전원 연결/배터리 모두)
  3. PCI Express 링크 상태 전원 관리 끄기
  4. 그래픽 카드 정보와 최근 7일간 디스플레이 드라이버 오류(이벤트 4101) 보고

  변경 전 현재 전원 관리 옵션을 %ProgramData%\SleepWakeFix 에 백업합니다.

.PARAMETER Undo
  이 스크립트가 바꾼 설정을 Windows 기본값으로 되돌립니다.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\fix-sleep-wake.ps1
  powershell -ExecutionPolicy Bypass -File .\fix-sleep-wake.ps1 -Undo
#>
param([switch]$Undo)

$ErrorActionPreference = 'Stop'

$BackupDir    = Join-Path $env:ProgramData 'SleepWakeFix'
$StateFile    = Join-Path $BackupDir 'state.json'
$PowerKey     = 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Power'
$UsbSubgroup  = '2a737441-1930-4402-8d77-b2bebba308a3'
$UsbSuspend   = '48e6b7a6-50f5-4782-a5d4-53bb8f07e226'

function Invoke-PowerCfg {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & powercfg.exe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "powercfg $($Arguments -join ' ') 실패 (종료 코드 $LASTEXITCODE)"
    }
}

function Get-ActiveSchemeGuid {
    $line = (& powercfg.exe /getactivescheme) -join ' '
    if ($line -match '([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})') {
        return $Matches[1]
    }
    throw '현재 전원 관리 옵션을 찾지 못했습니다.'
}

function Set-PowerValue {
    param([string]$Subgroup, [string]$Setting, [int]$Ac, [int]$Dc)
    Invoke-PowerCfg /setacvalueindex SCHEME_CURRENT $Subgroup $Setting $Ac
    Invoke-PowerCfg /setdcvalueindex SCHEME_CURRENT $Subgroup $Setting $Dc
}

function Write-Step([string]$Message) { Write-Host "  [OK] $Message" -ForegroundColor Green }

if ($Undo) {
    Write-Host '설정을 Windows 기본값으로 되돌립니다...' -ForegroundColor Cyan
    $hiberboot = 1
    if (Test-Path $StateFile) {
        $state = Get-Content $StateFile -Raw | ConvertFrom-Json
        if ($null -ne $state.HiberbootEnabled) { $hiberboot = [int]$state.HiberbootEnabled }
    }
    Set-ItemProperty -Path $PowerKey -Name HiberbootEnabled -Value $hiberboot -Type DWord
    Write-Step "빠른 시작 복원 (HiberbootEnabled = $hiberboot)"
    Set-PowerValue $UsbSubgroup $UsbSuspend 1 1
    Write-Step 'USB 선택적 절전 다시 켜기'
    Set-PowerValue SUB_PCIEXPRESS ASPM 0 1
    Write-Step 'PCI Express 링크 상태 전원 관리 기본값 (AC 끔 / 배터리 보통)'
    Invoke-PowerCfg /setactive SCHEME_CURRENT
    Write-Host "`n완료. 백업 파일은 $BackupDir 에 남아 있습니다." -ForegroundColor Cyan
    return
}

Write-Host '절전 후 화면 멈춤 예방 설정을 적용합니다...' -ForegroundColor Cyan

# 0. 백업
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
$scheme   = Get-ActiveSchemeGuid
$stamp    = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup   = Join-Path $BackupDir "power-scheme-$stamp.pow"
Invoke-PowerCfg /export $backup $scheme
$current  = (Get-ItemProperty -Path $PowerKey -Name HiberbootEnabled -ErrorAction SilentlyContinue).HiberbootEnabled
if (-not (Test-Path $StateFile)) {
    # 최초 실행 시의 원래 값만 기록합니다 (여러 번 실행해도 원래 값 유지).
    @{ HiberbootEnabled = $current; Scheme = $scheme; Backup = $backup } |
        ConvertTo-Json | Set-Content -Path $StateFile -Encoding UTF8
}
Write-Step "전원 관리 옵션 백업: $backup"

# 1. 빠른 시작 끄기
Set-ItemProperty -Path $PowerKey -Name HiberbootEnabled -Value 0 -Type DWord
Write-Step '빠른 시작 끄기'

# 2. USB 선택적 절전 끄기 (키보드/마우스가 늦게 깨어나는 문제 예방)
Set-PowerValue $UsbSubgroup $UsbSuspend 0 0
Write-Step 'USB 선택적 절전 끄기'

# 3. PCI Express 링크 상태 전원 관리 끄기 (그래픽 카드가 깨어나지 못하는 문제 예방)
Set-PowerValue SUB_PCIEXPRESS ASPM 0 0
Write-Step 'PCI Express 링크 상태 전원 관리 끄기'

Invoke-PowerCfg /setactive SCHEME_CURRENT
Write-Step '전원 관리 옵션 다시 적용'

# 4. 진단 정보
Write-Host "`n[그래픽 카드]" -ForegroundColor Cyan
Get-CimInstance Win32_VideoController |
    Select-Object Name, DriverVersion, @{ n = 'DriverDate'; e = { $_.DriverDate.ToString('yyyy-MM-dd') } } |
    Format-Table -AutoSize | Out-String | Write-Host

Write-Host '[최근 7일 디스플레이 드라이버 오류 (이벤트 4101)]' -ForegroundColor Cyan
$events = Get-WinEvent -FilterHashtable @{ LogName = 'System'; Id = 4101; StartTime = (Get-Date).AddDays(-7) } -ErrorAction SilentlyContinue
if ($events) {
    Write-Host "  $($events.Count)건 발견 - 그래픽 드라이버를 최신 버전으로 업데이트하세요." -ForegroundColor Yellow
    $events | Select-Object -First 5 TimeCreated, ProviderName | Format-Table -AutoSize | Out-String | Write-Host
} else {
    Write-Host '  없음'
}

Write-Host "`n완료! 재부팅하면 빠른 시작 끄기까지 모두 적용됩니다." -ForegroundColor Cyan
Write-Host '되돌리려면: powershell -ExecutionPolicy Bypass -File .\fix-sleep-wake.ps1 -Undo'
