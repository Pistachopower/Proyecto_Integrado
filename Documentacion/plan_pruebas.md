# Plan de Pruebas - Proyecto Integrado

Fecha: 12-03-2026  
Version: 1.0

## 1. Objetivo
Validar que las funcionalidades clave para usuarios anonimos, clientes y empleados funcionan de forma correcta y sin errores criticos.

## 2. Alcance
Incluye pruebas funcionales de:
- Catalogo y navegacion publica
- Registro y recuperacion de contrasena
- Compra, pagos y pedidos
- Lista de deseos
- Devoluciones
- Gestion de inventario y comentarios por empleados

## 3. Fuera de alcance (por ahora)
- Pruebas de carga masiva de usuarios concurrentes
- Pentesting avanzado
- Pruebas E2E en multiples navegadores en paralelo

## 4. Entorno de prueba
- Backend: Django + DRF
- Base de datos: entorno de desarrollo
- API base: `/api/v1/`
- Cuentas de prueba:
  - Usuario anonimo (sin login)
  - Cliente
  - Empleado
  - Administrador

## 5. Paso a paso de ejecucion

### Paso 1: Preparar datos
1. Crear al menos 3 categorias.
2. Crear al menos 10 piezas con stock variado.
3. Crear 1 cliente con metodos de pago.
4. Crear 1 empleado y 1 administrador.
5. Crear pedidos en estados: `PENDIENTE`, `PAGADO`, `ENVIADO`, `ENTREGADO`.

### Paso 2: Definir prioridad
1. Alta: login/registro, compra, pago, devoluciones, cambio de estado pedido.
2. Media: filtros, favoritos, valoraciones, aprobaciones.
3. Baja: cambios de perfil y funciones cosmeticas.

### Paso 3: Ejecutar casos criticos (smoke)
1. Registro de cliente.
2. Login.
3. Compra y pago.
4. Cambio de estado a enviado.
5. Solicitud/aprobacion de devolucion.

### Paso 4: Ejecutar resto de casos por rol
1. Usuarios anonimos.
2. Clientes.
3. Empleados.

### Paso 5: Registrar evidencia
1. Marcar cada caso como `PASS` o `FAIL`.
2. Guardar evidencia (respuesta API, captura o log).
3. Crear ticket de bug por cada `FAIL`.

### Paso 6: Cierre
1. Verificar criterios de salida.
2. Publicar reporte final con resumen de cobertura y defectos.

## 6. Casos de prueba

| ID | Rol | Que probar | Como probar (pasos) | Resultado esperado | Prioridad |
|---|---|---|---|---|---|
| A01 | Anonimo | Ver categorias | GET `/api/v1/categoria_pieza/` | 200 y lista de categorias | Alta |
| A02 | Anonimo | Interactuar formulario contacto | POST `/api/v1/contacto-vendedor/` con datos validos | 200 y mensaje de envio correcto | Media |
| A03 | Anonimo | Interactuar chatbot | POST `/api/v1/chatbot/` con pregunta FAQ | 200 y respuesta util | Media |
| A04 | Anonimo | Ver productos | GET `/api/v1/pieza/` | 200 y lista de piezas | Alta |
| A05 | Anonimo | Filtros de productos | GET `/api/v1/pieza/?categoria=<id>` | 200 y piezas filtradas | Alta |
| A06 | Anonimo | Ver detalle producto | GET `/api/v1/pieza/<id>/` | 200 y detalle correcto | Alta |
| A07 | Anonimo | Ver relacionados | GET `/api/v1/pieza/por_marca/?pieza_id=<id>` | 200 y lista de relacionados | Media |
| A08 | Anonimo | Registro cliente | POST `/api/v1/registro_cliente/` | 201 y cliente creado | Alta |
| A09 | Anonimo | Recuperar contrasena | POST `/api/v1/password-reset/` con email valido | 200 y correo enviado | Alta |
| C01 | Cliente | Comprar piezas | Flujo carrito + finalizar compra | Pedido creado en estado esperado | Alta |
| C02 | Cliente | Lista de favoritos | POST `/api/v1/lista_deseo/agregar_pieza/` | 201 y pieza agregada | Media |
| C03 | Cliente | Pago PayPal | POST crear orden + capturar pago | Pago completado y pedido actualizado | Alta |
| C04 | Cliente | Pago por cuenta | Crear metodo cuenta y pagar pedido | Pago registrado | Alta |
| C05 | Cliente | Editar perfil | PUT `/api/v1/mi-perfil/` | 200 y datos actualizados | Media |
| C06 | Cliente | Valorar pieza comprada | POST `/api/v1/valoracion/` con pieza comprada | 201 y valoracion creada | Media |
| C07 | Cliente | Solicitar devolucion | POST `/api/v1/mis-devoluciones/` en pedido entregado | 201 y devolucion pendiente | Alta |
| C08 | Cliente | CRUD metodos de pago | GET/POST/PATCH/DELETE en `/api/v1/metodo_pago_cliente/` | Operaciones correctas | Media |
| C09 | Cliente | Filtrar pedidos | GET `/api/v1/pedido/filtrar_pedidosCliente/` | 200 y resultados correctos | Media |
| C10 | Cliente | Pasar deseos a carrito | POST `/api/v1/lista_deseo/pasar_al_carrito/` | Piezas agregadas al carrito | Media |
| C11 | Cliente | Imprimir factura PDF | GET `/api/v1/pedido/<id>/factura_cliente/` con pedido pagado | 200 y PDF generado | Alta |
| C12 | Cliente | Email de pedido enviado | Cambiar pedido a ENVIADO desde vendedor | Cliente recibe notificacion | Alta |
| E01 | Empleado | Cambiar foto perfil | POST `/api/v1/vendedor/<id>/subir_foto_perfil/` | 200 y foto actualizada | Baja |
| E02 | Empleado | Editar perfil | PUT `/api/v1/mi-perfil/` | 200 y datos actualizados | Baja |
| E03 | Empleado | Cambiar estado pedido | PATCH `/api/v1/pedido/<id>/cambiar_estado_vendedor/` | 200 y estado actualizado | Alta |
| E04 | Empleado | Filtrar pedidos vendedor | GET `/api/v1/pedido/filtrar_pedidosVendedor/` | 200 y filtros aplicados | Media |
| E05 | Empleado | Agregar pieza con imagen | POST `/api/v1/pieza/` con imagen | 201 y pieza creada | Alta |
| E06 | Empleado | CRUD pieza | GET/POST/PATCH/DELETE en `/api/v1/pieza/` | Operaciones permitidas segun rol | Alta |
| E07 | Empleado | Carga CSV | POST `/api/v1/pieza/bulk_upload/` con CSV valido | 201 y piezas creadas | Media |
| E08 | Empleado | Carga XLSX | POST `/api/v1/pieza/bulk_upload/` con XLSX valido | 201 y piezas creadas | Media |
| E09 | Empleado | Carga ODS | POST `/api/v1/pieza/bulk_upload/` con ODS valido | 201 y piezas creadas | Media |
| E10 | Empleado | Aprobar devolucion | POST `/api/v1/devoluciones/<id>/aprobar/` | 200, devolucion aprobada, stock restaurado | Alta |
| E11 | Empleado | Rechazar devolucion | POST `/api/v1/devoluciones/<id>/rechazar/` | 200, devolucion rechazada | Alta |
| E12 | Empleado | Aprobar comentarios | POST `/api/v1/valoracion/<id>/aprobar/` | 200 y comentario aprobado | Media |

## 7. Criterios de salida
- 100% de casos `Alta` en `PASS`.
- 0 bugs criticos abiertos.
- Bugs `Media/Baja` documentados y priorizados.

## 8. Evidencia minima por caso
- ID del caso
- Fecha
- Ejecutado por
- Resultado (`PASS` o `FAIL`)
- Evidencia (captura, log o respuesta API)

## 9. Automatizacion
Comando base de pruebas automaticas:

```bash
python manage.py test proyecto
```

## 9.1. Tipos de test y frameworks utilizados

- **Tipos de test implementados:**
  - Test unitarios (con `TestCase` y `APIRequestFactory`): validan lógica y permisos de clases o funciones aisladas.
  - Test de integración (con `TestCase` y `APIClient`): validan flujos completos y endpoints reales de la API.

- **Frameworks/librerías utilizadas:**
  - Django TestCase (`django.test.TestCase`)
  - Django REST Framework: `APIClient`, `APIRequestFactory`, `status`
  - Modelos y utilidades de Django para crear datos de prueba

Estos frameworks permiten simular peticiones HTTP, autenticación, y verificar respuestas y reglas de negocio en endpoints REST.


## 10. Resumen de cobertura de pruebas automatizadas

### Tabla 1: Funcionalidades con tests implementados

| Area / Endpoint | Tipo de test | Descripcion | Casos cubiertos |
|---|---|---|---|
| Registro cliente | Integracion | POST `/api/v1/registro_cliente/` | Exitoso, error por campos, login correcto/incorrecto |
| Login cliente/empleado | Integracion | POST `/api/v1/login/` | Login correcto, error usuario/pass |
| Permisos usuario | Unitario | Permisos sobre usuarios (listar, crear) | Cliente, empleado, admin, anonimo |
| Permisos descuento | Unitario | Permisos sobre descuentos | Cliente, empleado, admin, anonimo |
| Permisos pedidos | Integracion | GET/POST `/api/v1/pedido/` y filtros | Cliente ve solo sus pedidos, empleados/admin todos |
| Lista de deseos | Integracion | CRUD y acceso a lista | Solo propia, agregar/eliminar, no duplicados, anonimo restringido |
| Filtros pedidos | Integracion | Filtros por cliente/vendedor | Seguridad y visibilidad |
| Registro/login errores | Integracion | Casos de error en registro/login | Usuario inexistente, password incorrecta, campos faltantes |

### Tabla 2: Funcionalidades pendientes de automatizar/testear

| Area / Endpoint | Prioridad | Descripcion | Casos faltantes |
|---|---|---|---|
| Formulario contacto vendedor | Media | POST `/api/v1/contacto-vendedor/` | Envio exitoso, validaciones, errores |
| Chatbot/FAQ | Media | POST `/api/v1/chatbot/` | Pregunta/Respuesta, errores |
| Carga masiva piezas | Media | POST `/api/v1/pieza/bulk_upload/` | CSV/XLSX/ODS, validaciones |
| Recuperacion de contraseña | Alta | POST `/api/v1/password-reset/` | Flujo completo, confirmacion |
| Pagos y metodos de pago | Alta | CRUD y validaciones de metodos | Tarjeta, cuenta, billetera, pago pedido |
| Carrito de compras | Alta | Flujo de compra y finalizar | Agregar, quitar, finalizar compra |
| Valoraciones y devoluciones | Alta | POST `/api/v1/valoracion/`, `/api/v1/mis-devoluciones/` | Crear, aprobar, rechazar, restricciones |
| Facturacion y notificaciones | Alta | GET `/api/v1/pedido/<id>/factura_cliente/` | PDF generado, email enviado |
| Marketing/descuentos | Media | CRUD descuentos | Crear, editar, eliminar, no solo permisos |
| Operaciones empleado | Baja/Media | Subir foto, editar perfil, inventario | Imagen, datos, inventario avanzado |
