# Script para depurar la inicialización de la base de datos del microservicio de Roles

Write-Host "Obteniendo token de autenticación..." -ForegroundColor Yellow
try {
    $loginData = @{
        email = "admin@sgsi.com"
        password = "Admin123!"
    } | ConvertTo-Json
    
    $loginResponse = Invoke-WebRequest -Uri "http://localhost:5001/login" -Method POST -Body $loginData -ContentType "application/json" -ErrorAction Stop
    $token = ($loginResponse.Content | ConvertFrom-Json).token
    
    if (-not $token) {
        throw "No se pudo obtener el token"
    }
    
    Write-Host "Token de autenticación obtenido correctamente" -ForegroundColor Green
    Write-Host "Token: $($token.Substring(0, 20))..." -ForegroundColor Gray
} catch {
    Write-Host "Error al obtener token de autenticación: $_" -ForegroundColor Red
    exit
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

Write-Host "Inicializando base de datos de Roles en puerto 5007..." -ForegroundColor Yellow
try {
    # Hacemos una llamada con mayor detalle de error
    $response = Invoke-WebRequest -Uri "http://localhost:5007/inicializar_db" -Method POST -Headers $headers -ErrorAction Stop
    Write-Host "Éxito: Base de datos de Roles inicializada correctamente: $($response.StatusCode) $($response.StatusDescription)" -ForegroundColor Green
} catch {
    Write-Host "Error al inicializar la base de datos de Roles:" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    
    try {
        # Intentamos obtener el mensaje de error detallado
        $errorDetails = $_.ErrorDetails.Message
        if ($errorDetails) {
            Write-Host "Error Details: $errorDetails" -ForegroundColor Red
        } else {
            Write-Host "Response: $($_.Exception.Message)" -ForegroundColor Red
        }
    } catch {
        Write-Host "No se pudo obtener detalles del error: $_" -ForegroundColor Red
    }
}
