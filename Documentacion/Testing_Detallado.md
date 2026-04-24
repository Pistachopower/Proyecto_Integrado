# Documento tecnico del area de testing

## 1. Objetivo del documento
Este documento explica las decisiones de testing del proyecto, con foco en:
- Por que se centralizan las pruebas en proyecto/tests.py.
- Que librerias y utilidades se usan.
- Por que existen las funciones helper, clases y metodos.
- Que recibe y que devuelve cada bloque importante.
- Como ejecutar y depurar las pruebas.

## 2. Por que usar proyecto/tests.py
Se eligio centralizar las pruebas en un unico modulo por estas razones:
- Simplicidad de mantenimiento: toda la suite principal esta en un lugar unico.
- Trazabilidad: es facil relacionar cada test con permisos, endpoints y reglas de negocio.
- Ejecucion directa: Django detecta automaticamente TestCase y metodos test_ en ese archivo.
- Curva de aprendizaje: para una fase academica o de proyecto integrado, reduce friccion al revisar.

Tambien hay una razon practica: en la configuracion de depuracion de VS Code ya se apunta a clases de este archivo, por ejemplo UsuarioAutenticacionIntegracionTests.

## 3. Librerias y framework usados
### 3.1 Django TestCase
- Import: django.test.TestCase.
- Uso: aislar cada prueba en base de datos temporal y limpia.
- Ventaja: cada test corre con transaccion controlada y sin contaminar datos de otros tests.

### 3.2 Django REST Framework testing
- Import: rest_framework.test.APIRequestFactory.
- Uso: pruebas unitarias de permisos sin levantar todo el flujo HTTP real.
- Import: rest_framework.test.APIClient.
- Uso: pruebas de integracion con endpoints reales (/api/v1/...).

### 3.3 HTTP status de DRF
- Import: rest_framework.status.
- Uso: comparar codigos HTTP con constantes legibles (HTTP_200_OK, HTTP_401_UNAUTHORIZED, etc).

### 3.4 Utilidades de autenticacion y dominio
- get_user_model: para crear usuarios segun el modelo real configurado.
- AnonymousUser: para validar reglas con usuarios no autenticados.
- date y Decimal: para crear datos realistas de pedidos, vendedores y piezas.
- SimpleNamespace: para simular objetos vista con action en pruebas unitarias de permisos.

## 4. Estructura general de la suite
La suite combina dos niveles de prueba:
- Pruebas unitarias: validan reglas puntuales de permisos (has_permission) aisladas.
- Pruebas de integracion: validan endpoints completos, autenticacion y respuestas reales.

Esta estrategia reduce falsos positivos: primero se valida la regla aislada y despues el comportamiento final en API.

## 5. Funciones helper: diseno, entrada y salida
### 5.1 crear_usuario_cliente
Firma:
- crear_usuario_cliente(username='cliente_test', email='cliente_test@example.com', telefono='600123123', direccion='Calle Falsa 123')

Motivo de diseno:
- Evitar duplicar codigo de creacion de usuarios cliente en cada setUp.
- Estandarizar password y rol para todos los escenarios de cliente.

Recibe:
- username (str)
- email (str)
- telefono (str)
- direccion (str)

Devuelve:
- Instancia de usuario persistida en BD con rol CLIENTE.

### 5.2 crear_usuario_empleado
Firma:
- crear_usuario_empleado(username='empleado_test', email='empleado_test@example.com', telefono='600123123', direccion='Calle Falsa 123')

Motivo de diseno:
- Reutilizacion para pruebas donde se necesita rol EMPLEADO.

Recibe:
- username (str)
- email (str)
- telefono (str)
- direccion (str)

Devuelve:
- Instancia de usuario persistida en BD con rol EMPLEADO.

### 5.3 crear_usuario_administrador
Firma:
- crear_usuario_administrador(username='admin_test', email='admin_test@example.com', telefono='600123123', direccion='Calle Falsa 123')

Motivo de diseno:
- Reutilizacion para pruebas de permisos de alto privilegio.

Recibe:
- username (str)
- email (str)
- telefono (str)
- direccion (str)

Devuelve:
- Instancia de usuario persistida en BD con rol ADMINISTRADOR.

### 5.4 obtener_ids_desde_respuesta
Firma:
- obtener_ids_desde_respuesta(response)

Motivo de diseno:
- En listados API se compara conjunto de IDs esperados contra obtenidos.
- Evita repetir bucles en multiples tests.

Recibe:
- response: respuesta DRF con response.data iterable.

Devuelve:
- set[int] con los IDs detectados en cada elemento de response.data.

## 6. Clases de prueba: por que existen y que validan
## 6.1 EsDuenioUsuarioTests (unitaria)
Motivo:
- Verificar la logica de EsDuenioUsuario sin ruido de ruteo, serializers o middleware.

Como se declara:
- Hereda de TestCase.
- setUp crea APIRequestFactory, instancia de permiso y usuarios de rol cliente/empleado/admin.

Entradas principales:
- request simulado con metodo HTTP y request.user.
- vista simulada con action usando SimpleNamespace.

Salida esperada:
- Booleano de has_permission, validado con assertTrue/assertFalse.

Casos cubiertos:
- Cliente no lista usuarios.
- Empleado si lista usuarios.
- Cliente no crea usuario.
- Empleado no crea usuario.
- Administrador si crea usuario.
- Anonimo no crea usuario.

## 6.2 DescuentoPermisosTests (unitaria)
Motivo:
- Probar la regla SoloAdminOEmpleado aplicada a DescuentoViewSet.

Como se declara:
- Hereda de TestCase.
- setUp con APIRequestFactory, permiso y usuarios de todos los roles.

Entradas principales:
- request con GET/POST.
- vista.action en list o create.

Salida esperada:
- Booleano de has_permission.

Casos cubiertos:
- Cliente no puede listar ni crear.
- Empleado si puede listar y crear.
- Administrador si puede listar y crear.
- Anonimo no puede listar.

## 6.3 PedidoPermisosIntegracionTests (integracion)
Motivo:
- Confirmar que la seguridad real del endpoint Pedido coincide con la regla funcional.

Como se declara:
- Hereda de TestCase.
- setUp crea APIClient, dos clientes, un vendedor y dos pedidos.

Entradas principales:
- Peticiones reales a /api/v1/pedido/ y acciones custom de filtrado.
- Usuario autenticado con force_authenticate o usuario anonimo.

Salida esperada:
- status_code correcto.
- Conjunto de IDs visible segun rol y ownership.

Casos cubiertos:
- Cliente solo ve sus pedidos en list.
- Cliente no ve detalle de pedido ajeno (404).
- Empleado y admin ven todos.
- Anonimo recibe 401 o 403.
- Filtros de cliente y vendedor no rompen la regla de seguridad.

## 6.4 ListaDeseosIntegracionTests (integracion)
Motivo:
- Verificar aislamiento de datos: cada cliente solo debe ver su lista.

Como se declara:
- setUp crea dos clientes y dos listas.

Entradas principales:
- GET a /api/v1/lista_deseo/mi_lista/ con distintos usuarios.

Salida esperada:
- status_code 200 para autenticados.
- lista_id y nombre coherentes con el cliente autenticado.
- anonimo bloqueado (401/403).

## 6.5 ListaDeseosOperacionesTests (integracion)
Motivo:
- Validar operaciones de negocio sobre la lista de deseos (agregar/eliminar/no duplicar).

Como se declara:
- setUp crea cliente, lista y pieza de prueba.

Entradas principales:
- POST /api/v1/lista_deseo/agregar_pieza/
- DELETE /api/v1/lista_deseo/eliminar_pieza/

Salida esperada:
- 201 al agregar.
- 400 al repetir la misma pieza.
- 200 al eliminar.
- Comprobacion en BD con exists() para confirmar persistencia real.
- anonimo bloqueado (401/403).

## 6.6 UsuarioAutenticacionIntegracionTests (integracion)
Motivo:
- Probar flujo completo de registro/login y errores frecuentes de autenticacion.

Como se declara:
- setUp prepara APIClient, payload cliente y usuario empleado precreado.

Entradas principales:
- POST /api/v1/registro_cliente/ con user_data.
- POST /api/v1/login/ con credenciales validas e invalidas.
- GET /api/v1/mi-perfil/ para control anonimo.

Salida esperada:
- Registro exitoso: 201 con user_data.
- Login exitoso: 200 con access, refresh e is_authenticated.
- Errores de login: 401 con campo error.
- Registro incompleto: 400 con detalle de campo faltante.
- Anonimo en endpoint protegido: 401 o 403.

## 6.7 EventoClienteIntegracionTests (integracion)
Motivo:
- Verificar tracking de eventos y metricas del dashboard vendedor.

Como se declara:
- setUp crea cliente, vendedor y APIClient.

Entradas principales:
- POST /api/v1/eventos/track/ con payload valido e incompleto.
- GET /api/v1/dashboard-vendedor/ autenticado como vendedor.

Salida esperada:
- Evento valido: 201 y evento persistido.
- Payload incompleto: 400 con detalle en propiedades.
- Dashboard: 200 y campos agregados esperados.

## 6.8 PiezaSerializerTests (unitaria)
Motivo:
- Asegurar contrato del serializer de Pieza, en particular categoria_id.

Como se declara:
- setUp crea categoria y pieza asociada.

Entradas principales:
- Instancia de Pieza serializada por PiezaSerializer.

Salida esperada:
- serializer.data incluye categoria_id correcto.

## 7. Metodologia de declaracion de metodos test_
Las pruebas siguen patron AAA (Arrange, Act, Assert):
- Arrange: crear datos y autenticar rol.
- Act: ejecutar request o metodo de permiso.
- Assert: validar status, payload y/o estado en BD.

Cada metodo test_ esta nombrado por comportamiento esperado, por ejemplo:
- test_cliente_no_puede_crear_usuario
- test_login_fallido_password_incorrecta

Esto mejora lectura del reporte de test y reduce ambiguedad.

## 8. Relacion entre pruebas y endpoints
Cobertura principal actual:
- Permisos de usuarios y descuentos.
- Pedidos y filtros por rol.
- Lista de deseos (visibilidad y operaciones).
- Registro/login y errores comunes.
- Tracking de eventos y dashboard vendedor.
- Contrato del serializer de pieza.

Endpoints relevantes ejercitados:
- /api/v1/usuario/
- /api/v1/descuento/
- /api/v1/pedido/
- /api/v1/pedido/filtrar_pedidosCliente/
- /api/v1/pedido/filtrar_pedidosVendedor/
- /api/v1/lista_deseo/mi_lista/
- /api/v1/lista_deseo/agregar_pieza/
- /api/v1/lista_deseo/eliminar_pieza/
- /api/v1/registro_cliente/
- /api/v1/login/
- /api/v1/mi-perfil/
- /api/v1/eventos/track/
- /api/v1/dashboard-vendedor/

## 9. Proceso de implementacion (redaccion sugerida para tu memoria)
1. Defini reglas criticas de negocio y seguridad por rol (cliente, empleado, admin, anonimo).
2. Cree funciones helper para generar usuarios de prueba y evitar duplicidad.
3. Implemente pruebas unitarias de permisos con APIRequestFactory para validar la regla pura.
4. Implemente pruebas de integracion con APIClient para validar endpoints reales y respuestas HTTP.
5. Agregue validaciones de errores esperados (401, 403, 404, 400) para escenarios negativos.
6. Verifique efectos en base de datos cuando aplica (altas/bajas en lista de deseos y eventos).
7. Ajuste la ejecucion con configuracion de depuracion en VS Code para aislar clases concretas.
8. Mantengo nombres de tests orientados a comportamiento para facilitar revision y evidencia academica.

## 10. Ejecucion y depuracion
Ejecucion completa:
- /home/nelson/Documentos/Proyecto_Integrado/.venv/bin/python manage.py test proyecto.tests --verbosity 2

Ejecucion por clase (ejemplo autenticacion):
- /home/nelson/Documentos/Proyecto_Integrado/.venv/bin/python manage.py test proyecto.tests.UsuarioAutenticacionIntegracionTests --verbosity 2

Depuracion en VS Code:
- En launch.json existe una configuracion debugpy para lanzar manage.py test con una clase objetivo.

## 11. Limitaciones actuales y mejora continua
- Falta separar la suite en multiples modulos por dominio cuando el archivo crezca mas.
- Conviene agregar pruebas parametrizadas o factories para reducir repeticion en setUp.
- Se puede ampliar cobertura a mas serializers, validaciones de negocio y casos de concurrencia.

## 12. Conclusiones
La estrategia actual combina pruebas unitarias e integracion con foco en seguridad y reglas de negocio. El archivo proyecto/tests.py permite una evidencia clara y centralizada para justificar tecnicamente el area de testing: que se probo, por que se probo y como se valida cada comportamiento esperado.
