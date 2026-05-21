$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RootDir

function ConvertTo-Pem {
    param(
        [string]$Label,
        [byte[]]$Bytes
    )

    $base64 = [System.Convert]::ToBase64String($Bytes)
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("-----BEGIN $Label-----")
    for ($i = 0; $i -lt $base64.Length; $i += 64) {
        $length = [Math]::Min(64, $base64.Length - $i)
        $lines.Add($base64.Substring($i, $length))
    }
    $lines.Add("-----END $Label-----")
    return ($lines -join "`n") + "`n"
}

function New-DerLength {
    param([int]$Length)

    if ($Length -lt 128) {
        return ,[byte[]]@([byte]$Length)
    }

    $bytes = New-Object System.Collections.Generic.List[byte]
    $value = $Length
    while ($value -gt 0) {
        $bytes.Insert(0, [byte]($value -band 0xff))
        $value = $value -shr 8
    }
    $result = New-Object System.Collections.Generic.List[byte]
    $result.Add([byte](0x80 -bor $bytes.Count))
    $result.AddRange($bytes)
    return ,$result.ToArray()
}

function New-DerInteger {
    param([byte[]]$Value)

    $start = 0
    while ($start -lt ($Value.Length - 1) -and $Value[$start] -eq 0) {
        $start++
    }
    $clean = [byte[]]($Value[$start..($Value.Length - 1)])
    if (($clean[0] -band 0x80) -ne 0) {
        $clean = [byte[]]([byte[]]@(0) + $clean)
    }

    $result = New-Object System.Collections.Generic.List[byte]
    $result.Add(0x02)
    $result.AddRange((New-DerLength $clean.Length))
    $result.AddRange($clean)
    return ,$result.ToArray()
}

function New-DerSequence {
    param([byte[]]$Content)

    $result = New-Object System.Collections.Generic.List[byte]
    $result.Add(0x30)
    $result.AddRange((New-DerLength $Content.Length))
    $result.AddRange($Content)
    return ,$result.ToArray()
}

function Export-RsaPrivateKeyPkcs1 {
    param([System.Security.Cryptography.RSA]$Rsa)

    $p = $Rsa.ExportParameters($true)
    $content = New-Object System.Collections.Generic.List[byte]
    $content.AddRange((New-DerInteger ([byte[]]@(0))))
    $content.AddRange((New-DerInteger $p.Modulus))
    $content.AddRange((New-DerInteger $p.Exponent))
    $content.AddRange((New-DerInteger $p.D))
    $content.AddRange((New-DerInteger $p.P))
    $content.AddRange((New-DerInteger $p.Q))
    $content.AddRange((New-DerInteger $p.DP))
    $content.AddRange((New-DerInteger $p.DQ))
    $content.AddRange((New-DerInteger $p.InverseQ))

    return ,(New-DerSequence $content.ToArray())
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example. Review secrets before production."
}

$envValues = @{}
Get-Content ".env" | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
        $key, $value = $line.Split("=", 2)
        $envValues[$key] = $value
    }
}

$domain = "localhost"
if ($envValues.ContainsKey("DOMAIN_NAME") -and $envValues["DOMAIN_NAME"]) {
    $domain = $envValues["DOMAIN_NAME"]
}

New-Item -ItemType Directory -Force -Path "nginx/certs" | Out-Null

$certPath = "nginx/certs/fullchain.pem"
$keyPath = "nginx/certs/privkey.pem"

if (-not (Test-Path $certPath) -or -not (Test-Path $keyPath)) {
    Write-Host "Generating self-signed certificate for $domain."

    if (Get-Command openssl -ErrorAction SilentlyContinue) {
        openssl req -x509 -nodes -days 30 -newkey rsa:2048 `
            -keyout $keyPath `
            -out $certPath `
            -subj "/CN=$domain"
    }
    else {
        Write-Host "OpenSSL was not found locally. Generating the certificate with .NET."
        $rsa = [System.Security.Cryptography.RSA]::Create(2048)
        $subject = [System.Security.Cryptography.X509Certificates.X500DistinguishedName]::new("CN=$domain")
        $request = [System.Security.Cryptography.X509Certificates.CertificateRequest]::new(
            $subject,
            $rsa,
            [System.Security.Cryptography.HashAlgorithmName]::SHA256,
            [System.Security.Cryptography.RSASignaturePadding]::Pkcs1
        )
        $request.CertificateExtensions.Add(
            [System.Security.Cryptography.X509Certificates.X509BasicConstraintsExtension]::new($false, $false, 0, $true)
        )
        $request.CertificateExtensions.Add(
            [System.Security.Cryptography.X509Certificates.X509KeyUsageExtension]::new(
                [System.Security.Cryptography.X509Certificates.X509KeyUsageFlags]::DigitalSignature -bor
                [System.Security.Cryptography.X509Certificates.X509KeyUsageFlags]::KeyEncipherment,
                $true
            )
        )

        $sanBuilder = [System.Security.Cryptography.X509Certificates.SubjectAlternativeNameBuilder]::new()
        if ($domain -eq "localhost") {
            $sanBuilder.AddDnsName("localhost")
        }
        else {
            $sanBuilder.AddDnsName($domain)
        }
        $request.CertificateExtensions.Add($sanBuilder.Build())

        $notBefore = [System.DateTimeOffset]::Now.AddMinutes(-5)
        $notAfter = $notBefore.AddDays(30)
        $cert = $request.CreateSelfSigned($notBefore, $notAfter)

        $certPem = ConvertTo-Pem "CERTIFICATE" $cert.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
        $keyPem = ConvertTo-Pem "RSA PRIVATE KEY" (Export-RsaPrivateKeyPkcs1 $rsa)

        Set-Content -Path $certPath -Value $certPem -Encoding ascii
        Set-Content -Path $keyPath -Value $keyPem -Encoding ascii
    }
}

try {
    docker info *> $null
}
catch {
    Write-Host ""
    Write-Host "Docker is not running or Docker Desktop is not available." -ForegroundColor Red
    Write-Host "Open Docker Desktop, wait until it finishes starting, and run this script again."
    Write-Host "You can verify it with: docker info"
    exit 1
}

docker compose up -d --build
docker compose ps
