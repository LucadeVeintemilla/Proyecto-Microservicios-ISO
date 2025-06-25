
Write-Host "Inicializando bases de datos de todos los microservicios..." -ForegroundColor Cyan

$servicios = @(
    @{nombre="Autenticacion"; puerto="5001"},
    @{nombre="Riesgos"; puerto="5002"},
    @{nombre="Documentacion"; puerto="5003"},
    @{nombre="Auditorias"; puerto="5004"},
    @{nombre="Incidentes"; puerto="5005"},
    @{nombre="Proveedores"; puerto="5006"},
    @{nombre="Roles"; puerto="5007"}
)

# Inicializar primero la autenticación para obtener el token
$authService = $servicios[0]
Write-Host "Inicializando base de datos de $($authService.nombre) en puerto $($authService.puerto)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$($authService.puerto)/inicializar_db" -Method POST -ErrorAction Stop
    Write-Host "Exito: Base de datos de $($authService.nombre) inicializada correctamente: $($response.StatusCode) $($response.StatusDescription)" -ForegroundColor Green
} catch {
    Write-Host "Error al inicializar la base de datos de $($authService.nombre): $_" -ForegroundColor Red
    exit
}

# Obtener token de autenticación
Write-Host "Obteniendo token de autenticacion..." -ForegroundColor Yellow
try {
    $loginData = @{
        email = "admin@sgsi.com"
        password = "Admin123!"
    } | ConvertTo-Json
    
    $loginResponse = Invoke-WebRequest -Uri "http://localhost:$($authService.puerto)/login" -Method POST -Body $loginData -ContentType "application/json" -ErrorAction Stop
    $token = ($loginResponse.Content | ConvertFrom-Json).token
    
    if (-not $token) {
        throw "No se pudo obtener el token"
    }
    
    Write-Host "Token de autenticacion obtenido correctamente" -ForegroundColor Green
} catch {
    Write-Host "Error al obtener token de autenticacion: $_" -ForegroundColor Red
    exit
}

$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Inicializar el resto de los servicios
for ($i = 1; $i -lt $servicios.Count; $i++) {
    $servicio = $servicios[$i]
    Write-Host "Inicializando base de datos de $($servicio.nombre) en puerto $($servicio.puerto)..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$($servicio.puerto)/inicializar_db" -Method POST -Headers $headers -ErrorAction Stop
        Write-Host "Exito: Base de datos de $($servicio.nombre) inicializada correctamente: $($response.StatusCode) $($response.StatusDescription)" -ForegroundColor Green
    } catch {
        Write-Host "Error al inicializar la base de datos de $($servicio.nombre): $_" -ForegroundColor Red
    }
}

Write-Host "Proceso de inicializacion completado para Autenticacion y todos los microservicios." -ForegroundColor Cyan
