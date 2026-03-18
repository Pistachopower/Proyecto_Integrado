from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient , APIRequestFactory #sirve mejor para unitarias (probar métodos concretos y permisos aislados)
from .models import Cliente, Pedido, Usuario, Vendedor
from .permissions import EsDuenioUsuario, SoloAdminOEmpleado


def crear_usuario_cliente( #función que encapsula la lógica (parámetros por defecto, rol específico, etc.)
    username="cliente_test",
    email="cliente_test@example.com",
    telefono="600123123",
    direccion="Calle Falsa 123",
):
    """Crea un usuario de prueba con rol cliente."""
    user_model = get_user_model() #→ retorna la clase Usuario
    return user_model.objects.create_user(
        username=username,
        email=email,
        password="Pass123456!",
        rol=Usuario.CLIENTE,
        telefono=telefono,
        direccion=direccion,
    )


def crear_usuario_empleado(
    username="empleado_test",
    email="empleado_test@example.com",
    telefono="600123123",
    direccion="Calle Falsa 123",
):
    """Crea un usuario de prueba con rol empleado."""
    user_model = get_user_model()
    return user_model.objects.create_user(
        username=username,
        email=email,
        password="Pass123456!",
        rol=Usuario.EMPLEADO,
        telefono=telefono,
        direccion=direccion,
    )


def crear_usuario_administrador(
    username="admin_test",
    email="admin_test@example.com",
    telefono="600123123",
    direccion="Calle Falsa 123",
):
    """Crea un usuario de prueba con rol administrador."""
    user_model = get_user_model()
    return user_model.objects.create_user(
        username=username,
        email=email,
        password="Pass123456!",
        rol=Usuario.ADMINISTRADOR,
        telefono=telefono,
        direccion=direccion,
    )


def obtener_ids_desde_respuesta(response):
    """Devuelve un conjunto con los IDs de una respuesta tipo lista."""
    ids = set()
    for item in response.data:
        ids.add(item["id"])
    return ids

class EsDuenioUsuarioTests(TestCase):
    """Pruebas para el permiso EsDuenioUsuario."""

    def setUp(self):
        # Se ejecuta antes de cada test.
        self.factory = APIRequestFactory() # Para crear peticiones simuladas y pruebas unitarias.
        self.permiso = EsDuenioUsuario() # El permiso que queremos probar.
        self.cliente = crear_usuario_cliente()
        self.empleado = crear_usuario_empleado()
        self.administrador = crear_usuario_administrador()

    #Test para probar que el cliente no puede ver la lista de usuarios, lo cual es correcto porque solo los jefes (empleados y administradores) pueden verla.
    def test_cliente_no_puede_ver_lista(self):
        # 1) Crear una peticion GET simulada.
        request = self.factory.get("/api/v1/usuario/")

        # 2) Decir que quien hace la peticion es el cliente.
        request.user = self.cliente

        # 3) Simular la vista con la accion que queremos probar.
        vista = SimpleNamespace(action="list")

        # 4) Ejecutar la regla de permisos.
        tiene_permiso = self.permiso.has_permission(request, vista)

        # 5) Comprobar el resultado esperado.
        self.assertFalse(tiene_permiso, "Un cliente no debe ver la lista de usuarios")

    # Test para comprobar que un empleado puede listar los usuarios.
    def test_empleado_puede_ver_lista(self):
        # 1) Crear una peticion GET simulada.
        request = self.factory.get("/api/v1/usuario/")

        # 2) Decir que quien hace la peticion es el empleado.
        request.user = self.empleado

        # 3) Simular la vista con la accion que queremos probar.
        vista = SimpleNamespace(action="list")

        # 4) Ejecutar la regla de permisos.
        tiene_permiso = self.permiso.has_permission(request, vista)

        # 5) Comprobar el resultado esperado.
        self.assertTrue(tiene_permiso, "Un empleado si debe poder ver la lista de usuarios")

    # Test para comprobar que un cliente no puede crear usuarios.
    def test_cliente_no_puede_crear_usuario(self):
        # 1) Crear una peticion POST simulada.
        request = self.factory.post("/api/v1/usuario/")

        # 2) Decir que quien hace la peticion es el cliente.
        request.user = self.cliente

        # 3) Simular la vista con la accion que queremos probar.
        vista = SimpleNamespace(action="create")

        # 4) Ejecutar la regla de permisos.
        tiene_permiso = self.permiso.has_permission(request, vista)

        # 5) Comprobar el resultado esperado.
        self.assertFalse(tiene_permiso, "Un cliente no debe poder crear usuarios")

    # Test para comprobar que un empleado NO puede crear usuarios (solo el administrador puede).
    def test_empleado_no_puede_crear_usuario(self):
        # 1) Crear una peticion POST simulada.
        request = self.factory.post("/api/v1/usuario/")

        # 2) Decir que quien hace la peticion es el empleado.
        request.user = self.empleado

        # 3) Simular la vista con la accion que queremos probar.
        vista = SimpleNamespace(action="create")

        # 4) Ejecutar la regla de permisos.
        tiene_permiso = self.permiso.has_permission(request, vista)

        # 5) Comprobar el resultado esperado.
        self.assertFalse(tiene_permiso, "Un empleado no debe poder crear usuarios")

    # Test para comprobar que solo el administrador puede crear usuarios.
    def test_administrador_puede_crear_usuario(self):
        # 1) Crear una peticion POST simulada.
        request = self.factory.post("/api/v1/usuario/")

        # 2) Decir que quien hace la peticion es el administrador.
        request.user = self.administrador

        # 3) Simular la vista con la accion que queremos probar.
        vista = SimpleNamespace(action="create")

        # 4) Ejecutar la regla de permisos.
        tiene_permiso = self.permiso.has_permission(request, vista)

        # 5) Comprobar el resultado esperado.
        self.assertTrue(tiene_permiso, "Solo el administrador debe poder crear usuarios")

    # Test para comprobar que un usuario anonimo no puede crear usuarios.
    def test_anonimo_no_puede_crear_usuario(self):
        # 1) Crear una peticion POST simulada.
        request = self.factory.post("/api/v1/usuario/")

        # 2) Asignar un usuario anonimo (sin login) a la peticion.
        request.user = AnonymousUser()

        # 3) Simular la vista con la accion que queremos probar.
        vista = SimpleNamespace(action="create")

        # 4) Ejecutar la regla de permisos.
        tiene_permiso = self.permiso.has_permission(request, vista)

        # 5) Comprobar el resultado esperado.
        self.assertFalse(tiene_permiso, "Un usuario anonimo no debe poder crear usuarios")


class DescuentoPermisosTests(TestCase):
    """
    Pruebas para verificar que solo empleados y administradores pueden acceder a DescuentoViewSet.
    
    DescuentoViewSet usa:
    - permission_classes = [IsAuthenticated, SoloAdminOEmpleado]
    
    Esto significa que:
    - Clientes: NO pueden acceder
    - Empleados: SÍ pueden acceder (list, create, retrieve, update, delete)
    - Administradores: SÍ pueden acceder (list, create, retrieve, update, delete)
    - Anónimos: NO pueden acceder
    """

    def setUp(self):
        # Se ejecuta antes de cada test.
        self.factory = APIRequestFactory() # Para crear peticiones simuladas.
        self.permiso = SoloAdminOEmpleado() # El permiso que usa DescuentoViewSet.
        self.cliente = crear_usuario_cliente()
        self.empleado = crear_usuario_empleado()
        self.administrador = crear_usuario_administrador()

    # ========== PRUEBAS PARA LISTAR DESCUENTOS (LIST) ==========

    def test_cliente_no_puede_listar_descuentos(self):
        """Verifica que un cliente NO puede listar descuentos."""
        # 1) Crear una peticion GET simulada.
        request = self.factory.get("/api/v1/descuento/")

        # 2) Asignar el usuario cliente.
        request.user = self.cliente

        # 3) Simular la vista con la accion 'list'.
        vista = SimpleNamespace(action="list")

        # 4) Ejecutar el permiso.
        tiene_permiso = self.permiso.has_permission(request, vista)

        # 5) El cliente NO debe poder listar.
        self.assertFalse(tiene_permiso, "Un cliente no debe poder listar descuentos")

    def test_empleado_puede_listar_descuentos(self):
        """Verifica que un empleado SÍ puede listar descuentos."""
        # 1) Crear una peticion GET simulada.
        request = self.factory.get("/api/v1/descuento/")

        # 2) Asignar el usuario empleado.
        request.user = self.empleado

        # 3) Simular la vista con la accion 'list'.
        vista = SimpleNamespace(action="list")

        # 4) Ejecutar el permiso.
        tiene_permiso = self.permiso.has_permission(request, vista)

        # 5) El empleado SÍ debe poder listar.
        self.assertTrue(tiene_permiso, "Un empleado debe poder listar descuentos")

    def test_administrador_puede_listar_descuentos(self):
        """Verifica que un administrador SÍ puede listar descuentos."""
        # 1) Crear una peticion GET simulada.
        request = self.factory.get("/api/v1/descuento/")

        # 2) Asignar el usuario admin.
        request.user = self.administrador

        # 3) Simular la vista con la accion 'list'.
        vista = SimpleNamespace(action="list")

        # 4) Ejecutar el permiso.
        tiene_permiso = self.permiso.has_permission(request, vista)

        # 5) El admin SÍ debe poder listar.
        self.assertTrue(tiene_permiso, "Un administrador debe poder listar descuentos")

    def test_anonimo_no_puede_listar_descuentos(self):
        """Verifica que un usuario anónimo NO puede listar descuentos."""
        # 1) Crear una peticion GET simulada.
        request = self.factory.get("/api/v1/descuento/")

        # 2) Asignar un usuario anonimo.
        request.user = AnonymousUser()

        # 3) Simular la vista con la accion 'list'.
        vista = SimpleNamespace(action="list")

        # 4) Ejecutar el permiso.
        tiene_permiso = self.permiso.has_permission(request, vista)

        # 5) El anonimo NO debe poder listar.
        self.assertFalse(tiene_permiso, "Un usuario anonimo no debe poder listar descuentos")

    # ========== PRUEBAS PARA CREAR DESCUENTOS (CREATE) ==========

    def test_cliente_no_puede_crear_descuento(self):
        """Verifica que un cliente NO puede crear descuentos."""
        # 1) Crear una peticion POST simulada.
        request = self.factory.post("/api/v1/descuento/")

        # 2) Asignar el usuario cliente.
        request.user = self.cliente

        # 3) Simular la vista con la accion 'create'.
        vista = SimpleNamespace(action="create")

        # 4) Ejecutar el permiso.
        tiene_permiso = self.permiso.has_permission(request, vista)

        # 5) El cliente NO debe poder crear.
        self.assertFalse(tiene_permiso, "Un cliente no debe poder crear descuentos")

    def test_empleado_puede_crear_descuento(self):
        """Verifica que un empleado SÍ puede crear descuentos."""
        # 1) Crear una peticion POST simulada.
        request = self.factory.post("/api/v1/descuento/")

        # 2) Asignar el usuario empleado.
        request.user = self.empleado

        # 3) Simular la vista con la accion 'create'.
        vista = SimpleNamespace(action="create")

        # 4) Ejecutar el permiso.
        tiene_permiso = self.permiso.has_permission(request, vista)

        # 5) El empleado SÍ debe poder crear.
        self.assertTrue(tiene_permiso, "Un empleado debe poder crear descuentos")

    def test_administrador_puede_crear_descuento(self):
        """Verifica que un administrador SÍ puede crear descuentos."""
        # 1) Crear una peticion POST simulada.
        request = self.factory.post("/api/v1/descuento/")

        # 2) Asignar el usuario admin.
        request.user = self.administrador

        # 3) Simular la vista con la accion 'create'.
        vista = SimpleNamespace(action="create")

        # 4) Ejecutar el permiso.
        tiene_permiso = self.permiso.has_permission(request, vista)

        # 5) El admin SÍ debe poder crear.
        self.assertTrue(tiene_permiso, "Un administrador debe poder crear descuentos")


class PedidoPermisosIntegracionTests(TestCase):
    """Pruebas de integración para verificar permisos reales en PedidoViewSet."""

    def setUp(self):
        # 1) Cliente HTTP para llamar endpoints reales de la API.
        self.api_client = APIClient() #APIClient (de rest_framework.test) es una clase para hacer peticiones HTTP en tests de integracion


        # 2) Crear usuarios de cada rol que vamos a probar.
        self.usuario_cliente_1 = crear_usuario_cliente()
        self.usuario_cliente_2 = crear_usuario_cliente(
            username="cliente_test_2",
            email="cliente_test_2@example.com",
            telefono="600123124",
            direccion="Calle Falsa 124",
        )
        self.usuario_empleado = crear_usuario_empleado()
        self.usuario_admin = crear_usuario_administrador()

        # 3) Crear perfiles de dominio (Cliente/Vendedor) necesarios para Pedido.
        self.cliente_1 = Cliente.objects.create(usuario=self.usuario_cliente_1)
        self.cliente_2 = Cliente.objects.create(usuario=self.usuario_cliente_2)
        self.vendedor = Vendedor.objects.create(
            usuario=self.usuario_empleado,
            fecha_contratacion=date.today(),
            comision_porcentaje=Decimal("10.00"),
        )

        # 4) Crear dos pedidos, uno para cada cliente.
        self.pedido_cliente_1 = Pedido.objects.create(
            estado=Pedido.PENDIENTE,
            cliente=self.cliente_1,
            vendedor=self.vendedor,
            fecha_pedido=date.today(),
            direccion_envio="Direccion cliente 1",
            total=Decimal("100.00"),
        )
        self.pedido_cliente_2 = Pedido.objects.create(
            estado=Pedido.PAGADO,
            cliente=self.cliente_2,
            vendedor=self.vendedor,
            fecha_pedido=date.today(),
            direccion_envio="Direccion cliente 2",
            total=Decimal("150.00"),
        )

    def test_cliente_solo_ve_sus_pedidos_en_list(self):
        """
        force_authenticate: es para simular la autenticación de un usuario en las pruebas
        y enfocarse en probar la lógica de permisos y vistas sin preocuparse por el proceso de login real.
        """
        # 1) Autenticar como cliente 1.
        self.api_client.force_authenticate(user=self.usuario_cliente_1)

        # 2) Pedir listado real de pedidos.
        response = self.api_client.get("/api/v1/pedido/")

        # 3) Debe responder OK y solo incluir el pedido propio.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = obtener_ids_desde_respuesta(response)
        self.assertEqual(ids, {self.pedido_cliente_1.id}) #self.pedido_cliente_1.id viene de setUp

    def test_cliente_no_puede_ver_detalle_de_otro_cliente(self):
        # 1) Autenticar como cliente 1.
        self.api_client.force_authenticate(user=self.usuario_cliente_1)

        # 2) Intentar abrir el detalle de un pedido ajeno.
        response = self.api_client.get(f"/api/v1/pedido/{self.pedido_cliente_2.id}/")

        # 3) Esperamos 404 porque get_queryset no le expone ese pedido.
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_empleado_puede_ver_todos_los_pedidos(self):
        # 1) Autenticar como empleado.
        self.api_client.force_authenticate(user=self.usuario_empleado)

        # 2) Pedir listado.
        response = self.api_client.get("/api/v1/pedido/")

        # 3) El empleado (jefe/ o no) debe ver los dos pedidos.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = obtener_ids_desde_respuesta(response)
        self.assertEqual(ids, {self.pedido_cliente_1.id, self.pedido_cliente_2.id})

    def test_admin_puede_ver_todos_los_pedidos(self):
        # 1) Autenticar como administrador.
        self.api_client.force_authenticate(user=self.usuario_admin)

        # 2) Pedir listado.
        response = self.api_client.get("/api/v1/pedido/")

        # 3) El admin también debe ver todos.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = obtener_ids_desde_respuesta(response)
        self.assertEqual(ids, {self.pedido_cliente_1.id, self.pedido_cliente_2.id})

    def test_anonimo_no_puede_listar_pedidos(self):
        # 1) Sin autenticación, llamar a listado.
        response = self.api_client.get("/api/v1/pedido/")

        # 2) Debe ser no autorizado o prohibido según configuración de autenticación.
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_filtrar_pedidos_cliente_respeta_regla_de_seguridad(self):
        # 1) Autenticar como cliente 1.
        self.api_client.force_authenticate(user=self.usuario_cliente_1)

        # 2) Llamar acción personalizada de filtrado para cliente.
        response = self.api_client.get("/api/v1/pedido/filtrar_pedidosCliente/")

        # 3) Debe devolver solo los pedidos del cliente autenticado.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = obtener_ids_desde_respuesta(response)
        self.assertEqual(ids, {self.pedido_cliente_1.id})

    def test_filtrar_pedidos_vendedor_respeta_regla_de_seguridad(self):
        # 1) Autenticar como cliente 1.
        self.api_client.force_authenticate(user=self.usuario_cliente_1)

        # 2) Llamar acción personalizada de filtrado para vendedor.
        response = self.api_client.get("/api/v1/pedido/filtrar_pedidosVendedor/")

        # 3) Aunque el endpoint sea de vendedor, un cliente no debe ver pedidos ajenos.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = obtener_ids_desde_respuesta(response)
        self.assertEqual(ids, {self.pedido_cliente_1.id})

#test pendientes por hacer EsDuenioDeObjeto, EsDuenioDirecto, 
#EsDuenioPorMetodoPago, EsDuenioPorPedido, SoloVerPiezasLineaPedido
#PermisoGestionInventario, PuedeEditarValoracion

