from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient , APIRequestFactory #sirve mejor para unitarias (probar métodos concretos y permisos aislados)
from .models import Cliente, Pedido, Usuario, Vendedor, ListaDeseos, Pieza, ListaDeseosPieza, EventoCliente, CategoriaPieza
from .serializers import PiezaSerializer
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
        """
        El método self.assertIn verifica que un elemento esté presente dentro de una colección (lista, string, diccionario, etc.) durante un test.

        Si el elemento está dentro de la colección, el test pasa. Si no está, el test falla.

        Por ejemplo:

        self.assertIn("a", ["a", "b", "c"]) pasa.
        self.assertIn(401, [401, 403]) pasa si el valor es 401 o 403.
        self.assertIn("clave", diccionario) pasa si "clave" es una key del diccionario.
        Se usa para comprobar que un valor esperado está incluido en un conjunto de posibles valores.
        """
        # 1) Sin autenticación, llamar a listado.
        response = self.api_client.get("/api/v1/pedido/")

        # 2) Debe ser no autorizado o prohibido según configuración de autenticación.
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )


    def test_filtrar_pedidos_cliente_respeta_regla_de_seguridad(self): #Mirar otros filtros en api_views.py
        # 1) Autenticar como cliente 1.
        self.api_client.force_authenticate(user=self.usuario_cliente_1)

        # 2) Llamar acción personalizada de filtrado para cliente.
        response = self.api_client.get("/api/v1/pedido/filtrar_pedidosCliente/") #Recuerda que esta en las accion 

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

class ListaDeseosIntegracionTests(TestCase):
    """Pruebas de integración para la lista de deseos: cada cliente solo ve su propia lista."""

    def setUp(self):
        self.api_client = APIClient()
        # Crear dos usuarios y clientes
        self.usuario_cliente_1 = crear_usuario_cliente(
            username="cliente_test_1",
            email="cliente_test_1@example.com",
        )
        self.usuario_cliente_2 = crear_usuario_cliente(
            username="cliente_test_2",
            email="cliente_test_2@example.com",
        )
        self.cliente_1 = Cliente.objects.create(usuario=self.usuario_cliente_1)
        self.cliente_2 = Cliente.objects.create(usuario=self.usuario_cliente_2)
        # Crear listas de deseos para cada cliente
        self.lista_1 = ListaDeseos.objects.create(
            cliente=self.cliente_1,
            nombre="Lista de cliente 1",
            fecha_creacion=date.today(),
        )
        self.lista_2 = ListaDeseos.objects.create(
            cliente=self.cliente_2,
            nombre="Lista de cliente 2",
            fecha_creacion=date.today(),
        )

    def test_cliente_ve_solo_su_lista(self):
        """El cliente autenticado solo ve su propia lista de deseos."""
        self.api_client.force_authenticate(user=self.usuario_cliente_1)
        response = self.api_client.get("/api/v1/lista_deseo/mi_lista/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["lista_id"], self.lista_1.id)
        self.assertEqual(response.data["nombre"], self.lista_1.nombre)
        # No debe ver la lista del otro cliente
        self.assertNotEqual(response.data["lista_id"], self.lista_2.id)

    def test_cliente_2_ve_solo_su_lista(self):
        """El segundo cliente solo ve su propia lista de deseos."""
        self.api_client.force_authenticate(user=self.usuario_cliente_2)
        response = self.api_client.get("/api/v1/lista_deseo/mi_lista/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["lista_id"], self.lista_2.id)
        self.assertEqual(response.data["nombre"], self.lista_2.nombre)
        self.assertNotEqual(response.data["lista_id"], self.lista_1.id)

    def test_anonimo_no_puede_ver_lista(self):
        """Un usuario no autenticado no puede acceder a la lista de deseos."""
        response = self.api_client.get("/api/v1/lista_deseo/mi_lista/")
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

class ListaDeseosOperacionesTests(TestCase):
    """Pruebas de integración para operaciones (CRUD) sobre la lista de deseos."""

    def setUp(self):
        self.api_client = APIClient()
        self.usuario_cliente = crear_usuario_cliente(
            username="cliente_test",
            email="cliente_test@example.com",
        )
        self.cliente = Cliente.objects.create(usuario=self.usuario_cliente)
        self.lista = ListaDeseos.objects.create(
            cliente=self.cliente,
            nombre="Lista de cliente",
            fecha_creacion=date.today(),
        )
        self.pieza = Pieza.objects.create(
            estado=Pieza.NUEVO,
            nombre="Pieza Test",
            referencia="REF123",
            version="V1",
            marca="MarcaTest",
            anio=2022,
            precio_base=Decimal("50.00"),
            descripcion="Pieza de prueba",
            stock=10,
            categoria=None,
        )

    def test_agregar_pieza_a_lista(self):
        """El cliente puede agregar una pieza a su lista de deseos."""
        self.api_client.force_authenticate(user=self.usuario_cliente)
        response = self.api_client.post(
            "/api/v1/lista_deseo/agregar_pieza/",
            {"pieza_id": self.pieza.id},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ListaDeseosPieza.objects.filter(lista_deseos=self.lista, pieza=self.pieza).exists())

    def test_no_agrega_pieza_repetida(self):
        """No se puede agregar la misma pieza dos veces a la lista de deseos."""
        self.api_client.force_authenticate(user=self.usuario_cliente)
        # Agregar la pieza una vez
        self.api_client.post(
            "/api/v1/lista_deseo/agregar_pieza/",
            {"pieza_id": self.pieza.id},
            format="json"
        )
        # Intentar agregarla de nuevo
        response = self.api_client.post(
            "/api/v1/lista_deseo/agregar_pieza/",
            {"pieza_id": self.pieza.id},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("ya_existe", response.data)

    def test_eliminar_pieza_de_lista(self):
        """El cliente puede eliminar una pieza de su lista de deseos."""
        self.api_client.force_authenticate(user=self.usuario_cliente)
        # Agregar la pieza
        self.api_client.post(
            "/api/v1/lista_deseo/agregar_pieza/",
            {"pieza_id": self.pieza.id},
            format="json"
        )
        # Eliminar la pieza
        response = self.api_client.delete(
            "/api/v1/lista_deseo/eliminar_pieza/",
            {"pieza_id": self.pieza.id},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(ListaDeseosPieza.objects.filter(lista_deseos=self.lista, pieza=self.pieza).exists())

    def test_anonimo_no_puede_agregar(self):
        """Un usuario no autenticado no puede agregar piezas a la lista de deseos."""
        response = self.api_client.post(
            "/api/v1/lista_deseo/agregar_pieza/",
            {"pieza_id": self.pieza.id},
            format="json"
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_anonimo_no_puede_eliminar(self):
        """Un usuario no autenticado no puede eliminar piezas de la lista de deseos."""
        response = self.api_client.delete(
            "/api/v1/lista_deseo/eliminar_pieza/",
            {"pieza_id": self.pieza.id},
            format="json"
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

class UsuarioAutenticacionIntegracionTests(TestCase):
    """
    Pruebas de integración para registro y login de usuarios (cliente, empleado, anónimo).
    Incluye:
    - Registro de cliente
    - Login de cliente
    - Login de empleado
    - Casos de login fallido
    - Acceso restringido para usuario anónimo
    """

    def setUp(self):
        self.api_client = APIClient()
        # Datos de prueba para cliente
        self.cliente_data = {
            "username": "cliente_test",
            "email": "cliente_test@example.com",
            "first_name": "Juan",
            "last_name": "Perez",
            "telefono": "600123123",
            "fecha_nacimiento": "1990-01-01",
            "direccion": "Calle Falsa 123",
            "password": "Pass123456!"
        }
        # Datos de prueba para empleado (creado por admin)
        self.empleado_username = "empleado_test"
        self.empleado_password = "Pass123456!"
        user_model = get_user_model()
        # Crear empleado directamente en la base de datos
        self.empleado = user_model.objects.create_user(
            username=self.empleado_username,
            email="empleado_test@example.com",
            password=self.empleado_password,
            rol=Usuario.EMPLEADO,
            telefono="600123124",
            direccion="Calle Verdadera 456",
        )

    def test_registro_cliente_exitoso(self):
        """
        Registro exitoso de un cliente.
        Verifica que el endpoint de registro crea correctamente el usuario y devuelve los datos esperados.
        """
        # Enviar los datos bajo la clave 'user_data' como espera el serializer
        response = self.api_client.post(
            "/api/v1/registro_cliente/",
            {"user_data": self.cliente_data},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user_data", response.data)
        self.assertEqual(response.data["user_data"]["username"], self.cliente_data["username"])

    def test_login_cliente_exitoso(self):
        """
        Login exitoso de un cliente recién registrado.
        Primero registra el cliente, luego prueba el login y verifica los tokens y datos devueltos.
        """
        # Registrar cliente
        self.api_client.post(
            "/api/v1/registro_cliente/",
            {"user_data": self.cliente_data},
            format="json"
        )
        # Login
        response = self.api_client.post(
            "/api/v1/login/",
            {
                "username": self.cliente_data["username"],
                "password": self.cliente_data["password"]
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(response.data["is_authenticated"])
        self.assertEqual(response.data["user"]["username"], self.cliente_data["username"])

    def test_login_empleado_exitoso(self):
        """
        Login exitoso de un empleado creado por admin.
        Verifica que el empleado puede autenticarse y recibe los tokens y datos correctos.
        """
        response = self.api_client.post(
            "/api/v1/login/",
            {
                "username": self.empleado_username,
                "password": self.empleado_password
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertTrue(response.data["is_authenticated"])
        self.assertEqual(response.data["user"]["username"], self.empleado_username)
        self.assertEqual(response.data["user"]["rol"], Usuario.EMPLEADO)

    def test_login_fallido_usuario_inexistente(self):
        """
        Login fallido con usuario inexistente.
        Verifica que el sistema responde con error y status adecuado.
        """
        response = self.api_client.post(
            "/api/v1/login/",
            {
                "username": "no_existe",
                "password": "incorrecta"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

    def test_login_fallido_password_incorrecta(self):
        """
        Login fallido con password incorrecta.
        Primero registra el cliente, luego intenta login con password incorrecta y verifica el error.
        """
        # Registrar cliente
        self.api_client.post(
            "/api/v1/registro_cliente/",
            {"user_data": self.cliente_data},
            format="json"
        )
        # Intentar login con password incorrecta
        response = self.api_client.post(
            "/api/v1/login/",
            {
                "username": self.cliente_data["username"],
                "password": "incorrecta"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

    def test_registro_cliente_fallido_faltan_campos(self):
        """
        Registro fallido por campos obligatorios faltantes.
        Prueba que el sistema devuelve error si falta un campo requerido.
        """
        data_incompleta = self.cliente_data.copy()
        del data_incompleta["password"] # El password es obligatorio, así que lo eliminamos para probar el error
        response = self.api_client.post(
            "/api/v1/registro_cliente/",
            {"user_data": data_incompleta},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data["user_data"])

    def test_login_anonimo_acceso_restringido(self):
        """
        Usuario anónimo no puede acceder a endpoints protegidos.
        Verifica que el sistema restringe el acceso a usuarios no autenticados.
        """
        response = self.api_client.get("/api/v1/mi-perfil/")
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class EventoClienteIntegracionTests(TestCase):
    """Pruebas de integración para tracking de eventos estandarizados."""

    def setUp(self):
        self.api_client = APIClient()

        self.usuario_cliente = crear_usuario_cliente(
            username="cliente_eventos",
            email="cliente_eventos@example.com",
        )
        self.cliente = Cliente.objects.create(usuario=self.usuario_cliente)

        self.usuario_vendedor = crear_usuario_empleado(
            username="vendedor_dashboard",
            email="vendedor_dashboard@example.com",
        )
        self.vendedor = Vendedor.objects.create(
            usuario=self.usuario_vendedor,
            fecha_contratacion=date.today(),
            comision_porcentaje=Decimal("8.00"),
        )

    def test_track_producto_visto_crea_evento(self):
        payload = {
            'nombre_evento': EventoCliente.PRODUCTO_VISTO,
            'sesion_id': 'sesion-test-001',
            'propiedades': {
                'pieza_id': 10,
                'referencia': 'REF-10',
                'categoria_id': 2,
                'precio': '49.90',
            },
        }

        response = self.api_client.post('/api/v1/eventos/track/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(EventoCliente.objects.count(), 1)
        self.assertEqual(EventoCliente.objects.first().nombre_evento, EventoCliente.PRODUCTO_VISTO)

    def test_track_rechaza_payload_incompleto(self):
        payload = {
            'nombre_evento': EventoCliente.PRODUCTO_VISTO,
            'sesion_id': 'sesion-test-002',
            'propiedades': {
                'pieza_id': 10,
                'categoria_id': 2,
                'precio': '49.90',
            },
        }

        response = self.api_client.post('/api/v1/eventos/track/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('propiedades', response.data)

    def test_dashboard_vendedor_muestra_metricas_eventos(self):
        EventoCliente.objects.create(
            nombre_evento=EventoCliente.PRODUCTO_VISTO,
            sesion_id='s1',
            cliente=self.cliente,
            propiedades={
                'pieza_id': 99,
                'referencia': 'REF-99',
                'categoria_id': 4,
                'precio': '80.00',
            },
        )
        EventoCliente.objects.create(
            nombre_evento=EventoCliente.PRODUCTO_VISTO,
            sesion_id='s2',
            cliente=self.cliente,
            propiedades={
                'pieza_id': 99,
                'referencia': 'REF-99',
                'categoria_id': 4,
                'precio': '80.00',
            },
        )
        EventoCliente.objects.create(
            nombre_evento=EventoCliente.BUSQUEDA_REALIZADA,
            sesion_id='s3',
            propiedades={'query': 'filtro aceite', 'total_resultados': 12},
        )
        EventoCliente.objects.create(
            nombre_evento=EventoCliente.AGREGADO_CARRITO,
            sesion_id='s4',
            propiedades={'pieza_id': 99, 'cantidad': 1, 'precio_unitario': '80.00'},
        )

        self.api_client.force_authenticate(user=self.usuario_vendedor)
        response = self.api_client.get('/api/v1/dashboard-vendedor/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('producto_mas_visto_global', response.data)
        self.assertIn('busqueda_mas_frecuente_global', response.data)
        self.assertIn('pieza_mas_agregada_carrito_global', response.data)
        self.assertEqual(response.data['producto_mas_visto_global']['propiedades__pieza_id'], 99)


class PiezaSerializerTests(TestCase): #Pruebas unitarias para el serializer de Pieza, enfocándonos en que incluya el campo categoria_id correctamente.
    def setUp(self):
        self.categoria = CategoriaPieza.objects.create(
            nombre='Motor',
            descripcion='Categoria de prueba',
        )
        self.pieza = Pieza.objects.create(
            estado=Pieza.NUEVO,
            nombre='Pieza Serializer Test',
            referencia='REF-SER-001',
            version='V1',
            marca='MarcaTest',
            anio=2024,
            precio_base=Decimal('120.00'),
            descripcion='Pieza para probar el serializer',
            stock=5,
            categoria=self.categoria,
        )

    def test_incluye_categoria_id(self):
        serializer = PiezaSerializer(self.pieza)

        self.assertEqual(serializer.data['categoria_id'], self.categoria.id)



