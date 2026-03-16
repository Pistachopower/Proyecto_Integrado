from types import SimpleNamespace
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from .models import Usuario
from .permissions import EsDuenioUsuario


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

class EsDuenioUsuarioTests(TestCase):
    """Pruebas para el permiso EsDuenioUsuario."""

    def setUp(self):
        # Se ejecuta antes de cada test.
        self.factory = APIRequestFactory() # Para crear peticiones simuladas.
        self.permiso = EsDuenioUsuario() # El permiso que queremos probar.
        self.cliente = crear_usuario_cliente()

    #Test para probar que el cliente no puede ver la lista de usuarios, lo cual es correcto porque solo los jefes (empleados y administradores) pueden verla.
    def test_cliente_no_puede_ver_lista(self):
        breakpoint() 
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


