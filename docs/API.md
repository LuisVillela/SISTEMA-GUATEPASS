# Documentación de Endpoints — GuatePass API

## 1. POST `/webhook/toll`

**Descripción:**
Endpoint principal que recibe las transacciones de peajes.

### Request

```json
{
    "placa": "P-123ABC",
    "peaje_id": "PEAJE_ZONA10",
    "tag_id": "TAG-001",
    "timestamp": "2025-01-20T10:30:00Z"
}
```

### Campos

* **placa** *(string, requerido)* — Placa del vehículo en formato guatemalteco.
* **peaje_id** *(string, requerido)* — Identificador del peaje (`PEAJE_ZONA10`, `PEAJE_ZONA11`, `PEAJE_ZONA12`, `PEAJE_ZONA13`).
* **tag_id** *(string, opcional)* — ID del tag físico asociado.
* **timestamp** *(string, requerido)* — Fecha y hora en formato ISO 8601.

### Response (200 OK)

```json
{
    "status": "processing",
    "message": "Transaction received and queued for processing",
    "user_type": "registrado",
    "has_active_tag": true,
    "message_id": "6f100e4c-d659-4eb7-8f3c-63ff285d34b3"
}
```

### Response (400 Bad Request)

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid placa format. Expected: P-123ABC",
        "timestamp": null
    }
}
```

---

## 2. GET `/history/payments/{placa}`

**Descripción:**
Obtiene el historial de pagos procesados de un vehículo.

### Path Parameters

* **placa** *(string)* — Placa del vehículo.

### Response (200 OK)

```json
{
    "placa": "P-123ABC",
    "total_payments": 3,
    "payments": [
        {
            "transaction_id": "TXN-A1B2C3D4",
            "peaje_id": "PEAJE_ZONA10",
            "timestamp": "2025-01-20T10:30:00Z",
            "monto": 22.5,
            "user_type": "registrado",
            "tipo_escenario": "tag_express",
            "fecha_procesado": "2025-01-20T10:30:05Z"
        }
    ]
}
```

### Response (404 Not Found)

```json
{
    "error": {
        "code": "USER_NOT_FOUND",
        "message": "No se encontraron pagos para la placa especificada"
    }
}
```

---

## 3. GET `/history/invoices/{placa}`

**Descripción:**
Obtiene el historial de facturas generadas para vehículos no registrados.

### Path Parameters

* **placa** *(string)* — Placa del vehículo.

### Response (200 OK)

```json
{
    "placa": "P-789GHI",
    "total_invoices": 2,
    "invoices": [
        {
            "factura_id": "FACT-123456",
            "peaje_id": "PEAJE_ZONA12",
            "timestamp": "2025-01-20T10:33:00Z",
            "monto": 52.5,
            "fecha_emision": "2025-01-20T10:33:05Z",
            "concepto": "Cobro de peaje PEAJE_ZONA12 - Usuario no registrado",
            "cargo_premium": "50%",
            "multa_tardia": "Q15.00",
            "estado": "pendiente"
        }
    ]
}
```

### Response (404 Not Found)

```json
{
    "error": {
        "code": "NO_INVOICES_FOUND",
        "message": "No se encontraron facturas para la placa especificada"
    }
}
```

---

# Endpoints de Gestión de Tags

## 4. POST `/users/{placa}/tag`

**Descripción:**
Asocia un tag físico a un vehículo registrado.

### Path Parameters

* **placa** *(string)*

### Request

```json
{
    "tag_id": "TAG-003",
    "metodo_pago": "tarjeta_credito",
    "configuracion": {
        "notificaciones": true,
        "cobro_automatico": true
    }
}
```

### Campos

* **tag_id** *(string, requerido)*
* **metodo_pago** *(string, opcional)* — `tarjeta_credito`, `tarjeta_debito`
* **configuracion** *(object, opcional)*

### Response (200 OK)

```json
{
    "message": "Tag asociado exitosamente",
    "tag": {
        "tag_id": "TAG-003",
        "placa": "P-123ABC",
        "estado": "activo",
        "fecha_activacion": "2025-01-20T10:35:00Z",
        "metodo_pago": "tarjeta_credito",
        "configuracion": {
            "notificaciones": true,
            "cobro_automatico": true
        }
    }
}
```

### Response (400 Bad Request)

```json
{
    "error": {
        "code": "TAG_IN_USE",
        "message": "Tag ID already in use"
    }
}
```

---

## 5. GET `/users/{placa}/tag`

**Descripción:**
Consulta la información del tag asociado a un vehículo.

### Response (200 OK)

```json
{
    "placa": "P-456DEF",
    "tag_info": {
        "tag_id": "TAG-001",
        "placa": "P-456DEF",
        "estado": "activo",
        "fecha_activacion": "2025-01-15T00:00:00Z",
        "metodo_pago": "tarjeta_debito",
        "configuracion": {
            "notificaciones": true,
            "cobro_automatico": true
        }
    }
}
```

### Response (200 OK - Usuario sin tag)

```json
{
    "placa": "P-123ABC",
    "tiene_tag": false,
    "message": "El usuario no tiene tag asociado"
}
```

---

## 6. PUT `/users/{placa}/tag`

**Descripción:**
Actualiza la configuración del tag asociado.

### Request

```json
{
    "configuracion": {
        "notificaciones": false,
        "cobro_automatico": true
    },
    "metodo_pago": "tarjeta_debito"
}
```

### Response (200 OK)

```json
{
    "message": "Tag actualizado exitosamente",
    "tag": {
        "tag_id": "TAG-001",
        "placa": "P-456DEF",
        "configuracion": {
            "notificaciones": false,
            "cobro_automatico": true
        },
        "metodo_pago": "tarjeta_debito"
    }
}
```

### Response (400 Bad Request)

```json
{
    "error": {
        "code": "NO_TAG_ASSOCIATED",
        "message": "El usuario no tiene tag asociado"
    }
}
```

---

## 7. DELETE `/users/{placa}/tag`

**Descripción:**
Desasocia un tag de un vehículo.

### Request

```json
{
    "razon": "Cambio de vehiculo"
}
```

### Response (200 OK)

```json
{
    "message": "Tag desasociado exitosamente",
    "placa": "P-456DEF",
    "tag_id": "TAG-001",
    "razon": "Cambio de vehiculo"
}
```

### Response (400 Bad Request)

```json
{
    "error": {
        "code": "NO_TAG_ASSOCIATED",
        "message": "El usuario no tiene tag asociado"
    }
}
```

---

# Códigos de Error Comunes

| Código                | HTTP Status | Descripción                      |
| --------------------- | ----------- | -------------------------------- |
| **VALIDATION_ERROR**  | 400         | Error en validación de datos     |
| **MISSING_PLACA**     | 400         | Parámetro `placa` requerido      |
| **INVALID_PLACA**     | 400         | Formato de placa inválido        |
| **TAG_IN_USE**        | 400         | El tag ya está en uso            |
| **USER_NOT_FOUND**    | 404         | Usuario no encontrado            |
| **TAG_NOT_FOUND**     | 404         | Tag no encontrado                |
| **NO_TAG_ASSOCIATED** | 400         | El usuario no tiene tag asociado |
| **INTERNAL_ERROR**    | 500         | Error interno del servidor       |

---