# Monitoreo y Logs en CloudWatch

Esta sección explica cómo revisar los registros del sistema en AWS para validar el procesamiento de transacciones, pagos, facturas y notificaciones.

---

## 1. Acceder a CloudWatch Logs

1. Entrar a **AWS Console**
2. Abrir el servicio **CloudWatch**
3. Ir a **Log groups**
4. Buscar los grupos de logs de las Lambdas del sistema, por ejemplo:

```
/aws/lambda/toll-webhook-handler-dev
/aws/lambda/transaction-processor-dev
/aws/lambda/pago-handler-dev
/aws/lambda/factura-generator-dev
/aws/lambda/notification-handler-dev
```

Cada uno representa una etapa del flujo.

---

## 2. Logs de Notificaciones

El grupo principal es:

```
/aws/lambda/notification-handler-dev
```

Aquí se registran:

* Envío de correos (simulados)
* Envío de SMS (simulados)
* Notificaciones de pagos exitosos o fallidos
* Notificaciones por facturas
* Errores al notificar

Para ver los registros:

1. Abrir el grupo
2. Seleccionar el **Log Stream** más reciente
3. Revisar las líneas generadas por el Lambda

---

## 3. Logs del Flujo de Transacciones

Para seguir una transacción completa, revisar en este orden:

1. **Webhook**

   ```
   /aws/lambda/toll-webhook-handler-dev
   ```

   Registra la entrada del POST `/webhook/toll`.

2. **Procesamiento**

   ```
   /aws/lambda/transaction-processor-dev
   ```

   Detecta el escenario (tradicional, digital o tag).

3. **Pago o Factura**

   * Pago:

     ```
     /aws/lambda/pago-handler-dev
     ```
   * Factura:

     ```
     /aws/lambda/factura-generator-dev
     ```

4. **Notificación**

   ```
   /aws/lambda/notification-handler-dev
   ```
