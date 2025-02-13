# 生成类似 macMachineId 的格式
function New-MacMachineId {
    $template = "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx"
    $result = ""
    $random = [Random]::new()
    
    foreach ($char in $template.ToCharArray()) {
        if ($char -eq 'x' -or $char -eq 'y') {
            $r = $random.Next(16)
            $v = if ($char -eq "x") { $r } else { ($r -band 0x3) -bor 0x8 }
            $result += $v.ToString("x")
        } else {
            $result += $char
        }
    }
    return $result
}

# 生成64位随机ID
function New-RandomId {
    $uuid1 = [guid]::NewGuid().ToString("N")
    $uuid2 = [guid]::NewGuid().ToString("N")
    return $uuid1 + $uuid2
}

# 等待 Cursor 进程退出
$cursorProcesses = Get-Process "cursor" -ErrorAction SilentlyContinue
if ($cursorProcesses) {
    Write-Host "检测到 Cursor 正在运行。请关闭 Cursor 后继续..."
    Write-Host "正在等待 Cursor 进程退出..."
    
    while ($true) {
        $cursorProcesses = Get-Process "cursor" -ErrorAction SilentlyContinue
        if (-not $cursorProcesses) {
            Write-Host "Cursor 已关闭，继续执行..."
            break
        }
        Start-Sleep -Seconds 1
    }
}

# 备份 MachineGuid
$backupDir = Join-Path $HOME "MachineGuid_Backups"
if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

$currentValue = Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Cryptography" -Name MachineGuid
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = Join-Path $backupDir "MachineGuid_$timestamp.txt"
$counter = 0

while (Test-Path $backupFile) {
    $counter++
    $backupFile = Join-Path $backupDir "MachineGuid_${timestamp}_$counter.txt"
}

$currentValue.MachineGuid | Out-File $backupFile

# 使用环境变量构建 storage.json 路径
$storageJsonPath = Join-Path $env:APPDATA "Cursor\User\globalStorage\storage.json"
$newMachineId = New-RandomId
$newMacMachineId = New-MacMachineId
$newDevDeviceId = [guid]::NewGuid().ToString()
$newSqmId = "{$([guid]::NewGuid().ToString().ToUpper())}"

if (Test-Path $storageJsonPath) {
    # 保存原始文件属性
    $originalAttributes = (Get-ItemProperty $storageJsonPath).Attributes
    
    # 移除只读属性
    Set-ItemProperty $storageJsonPath -Name IsReadOnly -Value $false
    
    # 更新文件内容
    $jsonContent = Get-Content $storageJsonPath -Raw -Encoding UTF8
    $data = $jsonContent | ConvertFrom-Json
    
    # 检查并更新或添加属性
    $properties = @{
        "telemetry.machineId" = $newMachineId
        "telemetry.macMachineId" = $newMacMachineId
        "telemetry.devDeviceId" = $newDevDeviceId
        "telemetry.sqmId" = $newSqmId
    }

    foreach ($prop in $properties.Keys) {
        if (-not (Get-Member -InputObject $data -Name $prop -MemberType Properties)) {
            $data | Add-Member -NotePropertyName $prop -NotePropertyValue $properties[$prop]
        } else {
            $data.$prop = $properties[$prop]
        }
    }
    
    $newJson = $data | ConvertTo-Json -Depth 100
    
    # 使用 StreamWriter 保存文件，确保 UTF-8 无 BOM 且使用 LF 换行符
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($storageJsonPath, $newJson.Replace("`r`n", "`n"), $utf8NoBom)
    
    # 恢复原始文件属性
    Set-ItemProperty $storageJsonPath -Name Attributes -Value $originalAttributes
}

# 更新注册表 MachineGuid
$newMachineGuid = [guid]::NewGuid().ToString()
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Cryptography" -Name "MachineGuid" -Value $newMachineGuid

Write-Host "Successfully updated all IDs:"
Write-Host "Backup file created at: $backupFile"
Write-Host "New MachineGuid: $newMachineGuid"
Write-Host "New telemetry.machineId: $newMachineId"
Write-Host "New telemetry.macMachineId: $newMacMachineId"
Write-Host "New telemetry.devDeviceId: $newDevDeviceId"
Write-Host "New telemetry.sqmId: $newSqmId"
