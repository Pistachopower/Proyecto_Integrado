from types import SimpleNamespace
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from .models import Usuario
from .permissions import EsDuenioUsuario, SoloAdminOEmpleado


def crear_usuario_cliente():
    """Crea un usuario de prueba con rol cliente."""
    user_model = get_user_model()
    return user_model.objects.create_user(
        username="cliente_test",
        email="cliente_test@example.com",
        password="Pass123456!",
        rol=Usuario.CLIENTE,
        telefono="600123123",
        direccion="Calle Falsa 123",
    )


def crear_usuario_empleado():
    """Crea un usuario de prueba con rol empleado."""
    user_model = get_user_model()
    return user_model.objects.create_user(
        username="empleado_test",
        email="empleado_test@example.com",
        password="Pass123456!",
        rol=Usuario.EMPLEADO,
        telefono="600123123",
        direccion="Calle Falsa 123",
    )


def crear_usuario_administrador():
    """Crea un usuario de prueba con rol administrador."""
    user_model = get_user_model()
    return user_model.objects.create_user(
        username="admin_test",
        email="admin_test@example.com",
        password="Pass123456!",
        rol=Usuario.ADMINISTRADOR,
        telefono="600123123",
        direccion="Calle Falsa 123",
    )

class EsDuenioUsuarioTests(TestCase):
    """Pruebas para el permiso EsDuenioUsuario."""

    def setUp(self):
        # Se ejecuta antes de cada test.
        self.factory = APIRequestFactory() # Para crear peticiones simuladas.
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

#test pendientes por hacer EsDuenioDeObjeto, EsDuenioDirecto, 
#EsDuenioPorMetodoPago, EsDuenioPorPedido, SoloVerPiezasLineaPedido
#PermisoGestionInventario, PuedeEditarValoracion