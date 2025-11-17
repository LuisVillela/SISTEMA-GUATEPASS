# GuatePass

## Descripción General del Proyecto
GuatePass es un sistema serverless para automatizar el cobro de peajes en Guatemala. Recibe eventos desde los peajes (webhooks), valida y categoriza la transacción según el tipo de usuario (no registrado, registrado, con Tag), calcula montos, procesa pagos o genera facturas, envía notificaciones simuladas y registra el historial en DynamoDB.

## Objetivo
- Procesar transacciones en tiempo real.
- Aplicar reglas de cobro y descuentos.
- Generar facturas para no registrados.
- Enviar notificaciones (simuladas) y almacenar historial.
- Escalar con AWS Lambda, SQS, SNS y DynamoDB.

---

## Prerrequisitos
- Python 3.12
- AWS CLI configurado (credenciales con permisos para crear recursos IAM, Lambda, SQS, SNS, DynamoDB, CloudWatch)
- SAM CLI (AWS SAM)
- boto3 instalado (se recomienda crear un virtualenv)

Archivos relevantes:
- Plantilla SAM: [template.yaml](template.yaml)
- Dependencias globales: [requirements.txt](requirements.txt)

---

## Despliegue paso a paso

1. Configurar credenciales AWS:
   - aws configure (ingresa Access Key, Secret Key, región us-east-1)

2. Construir con SAM:
   - sam build

3. Desplegar con SAM:
   - sam deploy --guided
     - Stack Name: guatepass-stack
     - Region: us-east-1
     - Environment: dev (por defecto)
   - La plantilla exporta la URL de la API en Outputs (`ApiUrl`, `WebhookUrl`).

Archivo IaC principal: [template.yaml](template.yaml)

Variables de entorno importantes (definidas por la plantilla):
- Nombres de tablas DynamoDB: `guatepass-users-${Environment}`, `guatepass-transactions-${Environment}`, `guatepass-tags-${Environment}`
- Cola SQS: `guatepass-processing-${Environment}`

---

## Estructura de Lambdas y puntos importantes (links)
- Webhook / validación síncrona: [src/functions/webhook/app.py](src/functions/webhook/app.py)  
  - Validación: [`WebhookValidator.validate_complete`](src/functions/webhook/validation.py)
- Processor (SQS -> procesamiento asíncrono): [src/functions/processor/app.py](src/functions/processor/app.py)  
  - Calculadora de pagos: [`PaymentCalculator.calcular_monto`](src/functions/processor/payment_calculator.py)  
  - Generador de facturas: [`InvoiceGenerator.generar_factura`](src/functions/processor/invoice_generator.py)
- Gestión de Tags: [src/functions/tags/app.py](src/functions/tags/app.py)
- Notificador (SNS): [src/functions/notifier/app.py](src/functions/notifier/app.py)
- Historial de pagos y facturas: [src/functions/history/app.py](src/functions/history/app.py), [src/functions/invoices/app.py](src/functions/invoices/app.py)

---

## Carga inicial de datos (CSV)
El CSV con clientes está en: [data/clientes.csv](data/clientes.csv)

Para cargarlo en DynamoDB (tabla `guatepass-users-dev` por defecto):
1. Verificar que la tabla existe (se crea con el despliegue SAM).
2. Ejecutar:
   - python scripts/load_initial_data.py
   - python scripts/populate_tags.py

Scripts relacionados:
- [scripts/load_initial_data.py](scripts/load_initial_data.py)
- [scripts/populate_tags.py](scripts/populate_tags.py)

Notas:
- El script convierte saldos a Decimal para evitar problemas con DynamoDB.
- Revisar el contenido del CSV antes de subirlo.

---

## Cómo probar los endpoints

1. Obtener la URL del API:
   - Output `WebhookUrl` del stack (o usar `ApiUrl` + `/webhook/toll`).
   - Puedes obtenerlo con AWS CLI:
     - ```JSON
       aws cloudformation describe-stacks --stack-name guatepass-stack --query "Stacks[0].Outputs" ```

2. Test rápido con curl (ejemplos):

- Webhook con tag
```https
(POST /webhook/toll)
  curl -X POST "<WEBHOOK_URL>" \
    -H "Content-Type: application/json" \
    -d '{
      "placa": "P-456DEF",
      "peaje_id": "PEAJE_ZONA11",
      "tag_id": "TAG-001",
      "timestamp": "2025-11-14T10:30:00Z"
    }'
  ```
- Webhook sin tag
``` https
(POST /webhook/toll)
  curl -X POST "<WEBHOOK_URL>" \
    -H "Content-Type: application/json" \
    -d '{
      "placa": "P-789GHI",
      "peaje_id": "PEAJE_ZONA10",
      "timestamp": "2025-11-14T10:30:00Z"
    }'
```
- Historial de pagos
``` https
(GET /history/payments/{placa})
  curl -X GET "<API_BASE>/history/payments/P-123ABC"
```

- Historial de facturas
```https
(GET /history/invoices/{placa})
  curl -X GET "<API_BASE>/history/invoices/P-789GHI"
```

Ejemplos automáticos / colecciones:
- Postman collection Transacciones: [tests/Testing Transacciones.postman_collection.json](tests/Testing Transacciones.postman_collection.json)
- Postman collection Tags: [tests/Testing Tags.postman_collection.json](tests/Testing Tags.postman_collection.json)
- Script de pruebas webhook: [scripts/test_webhook.sh](scripts/test_webhook.sh)

---

## Ejecución de pruebas integradas
- Test suite de ejemplo (automatiza envíos y verificaciones): [tests/test_all.py](tests/test_all.py)
  - Este script usa boto3 para obtener ApiUrl desde CloudFormation y valida inserciones en DynamoDB.
- Para simular envío a SQS y ver procesamiento:
  - python scripts/test_processor.py

---

## Flujo interno (resumen)
1. [src/functions/webhook/app.py](src/functions/webhook/app.py) valida y encola el mensaje en SQS.
   - Validación:  [`WebhookValidator.validate_complete`](src/functions/webhook/validation.py)
2. [src/functions/processor/app.py](src/functions/processor/app.py) consume SQS, calcula monto, simula pago y guarda transacción.
   - Lógica de tarifas: [`PaymentCalculator.calcular_monto`](src/functions/processor/payment_calculator.py) y constantes en [src/functions/processor/app.py](src/functions/processor/app.py)
   - Genera factura si es necesario: [`InvoiceGenerator.generar_factura`](src/functions/processor/invoice_generator.py)
3. [src/functions/notifier/app.py](src/functions/notifier/app.py) procesa mensajes SNS y simula envío de email/SMS.

---

## Monitoreo y Logs
- Dashboards y widgets: [scripts/create_dashboard.py](scripts/create_dashboard.py)
- Verificación de monitoreo: [scripts/verify_monitoring.py](scripts/verify_monitoring.py)
- Logs Lambda (CloudWatch log groups) relevantes:
  - /aws/lambda/webhook-validator-dev -> [src/functions/webhook/app.py](src/functions/webhook/app.py)
  - /aws/lambda/transaction-processor-dev -> [src/functions/processor/app.py](src/functions/processor/app.py)
  - /aws/lambda/notification-handler-dev -> [src/functions/notifier/app.py](src/functions/notifier/app.py)
  - /aws/lambda/tags-management-dev -> [src/functions/tags/app.py](src/functions/tags/app.py)
- Scripts para ver logs y estado:
  - [scripts/check_logs_python.py](scripts/check_logs_python.py)
  - [scripts/debug_processor.py](scripts/debug_processor.py)
  - [scripts/verify_data.py](scripts/verify_data.py)
  - [scripts/check_transactions.py](scripts/check_transactions.py)
  - [scripts/verify_processor.sh](scripts/verify_processor.sh)

Recomendaciones:
- Revisar CloudWatch Log Groups para errores o excepciones.
- Configurar alarmas (errores Lambda, latencia, throttles) en CloudWatch.

---

## Buenas prácticas y notas
- Asegúrate de que las funciones Lambda tengan permisos mínimos necesarios (políticas en `template.yaml`).
- Para ambientes de producción cambiar variables y tamaños de memoria/timeout según carga.
- En producción no simular pagos: integrar pasarela real y manejar idempotencia.
- Los scripts de carga (`scripts/load_initial_data.py`) y pruebas (`tests/test_all.py`) usan boto3 y esperan que las tablas/colas/ARNs estén desplegadas.

---

## Recursos y archivos útiles (rápida referencia)
- Template SAM: [template.yaml](template.yaml)  
- Webhook validator: [src/functions/webhook/validation.py](src/functions/webhook/validation.py)  
- Webhook handler: [src/functions/webhook/app.py](src/functions/webhook/app.py)  
- Processor: [src/functions/processor/app.py](src/functions/processor/app.py)  
- Payment calculator: [src/functions/processor/payment_calculator.py](src/functions/processor/payment_calculator.py)  
- Invoice generator: [src/functions/processor/invoice_generator.py](src/functions/processor/invoice_generator.py)  
- Tags management: [src/functions/tags/app.py](src/functions/tags/app.py)  
- Notifier: [src/functions/notifier/app.py](src/functions/notifier/app.py)  
- Data CSV: [data/clientes.csv](data/clientes.csv)  
- Scripts de ayuda: [scripts/](scripts/)  
- Tests: [tests/test_all.py](tests/test_all.py)
