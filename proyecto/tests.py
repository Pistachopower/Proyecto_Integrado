
#/home/nelson/Documentos/Proyecto_Integrado/.venv/bin/python manage.py test proyecto.tests --verbosity 2
#	breakpoint()
#

"""
Libreria utilizada:
Django Test Framework

unittest




p username
p email
p rol
p user_model
n (next linea)
s (step into)
c (continue)
q (salir)
Despues de crear el usuario, revisa:
p user.id
p user.email
p user.rol
p user.check_password("Pass123456!")
"""


from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIRequestFactory, APITestCase

from .models import (
	CategoriaPieza,
	Cliente,
	Devolucion,
	LineaPedido,
	ListaDeseos,
	Pedido,
	Pieza,
	Usuario,
	Vendedor,
)
from .permissions import PermisoGestionInventario

#/home/nelson/Documentos/Proyecto_Integrado/.venv/bin/python manage.py test proyecto.tests.RegistroClienteAPITests.test_registro_cliente_rechaza_email_repetido --verbosity 2

#funcion auxiliar para crear usuarios en los tests, evitando repetir código y asegurando que se cumplen los campos obligatorios del modelo custom de usuario.
def crear_usuario(username, email, rol, password="Pass123456!"):
	"""Helper para crear usuarios con los campos obligatorios del modelo custom."""
	user_model = get_user_model()
	#breakpoint()
	return user_model.objects.create_user(
		username=username,
		email=email,
		password=password,
		rol=rol,
		telefono="600123123",
		direccion="Calle Falsa 123",
	)


class PermisoGestionInventarioTests(TestCase):
	def setUp(self):
		#APIRequestFactory: para fabricar requests "en bruto" (sin pasar por URLs reales). 
		# Asigna manualmente request.user con diferentes roles (anónimo, empleado, admin).
		self.factory = APIRequestFactory()
		self.permiso = PermisoGestionInventario()
		self.admin = crear_usuario(
			username="admin_test",
			email="admin_test@example.com",
			rol=Usuario.ADMINISTRADOR,
		)
		self.empleado = crear_usuario(
			username="empleado_test",
			email="empleado_test@example.com",
			rol=Usuario.EMPLEADO,
		)

	#genera peticiones HTTP con el método y usuario indicados.
	def _request(self, method, user=None):
		request = getattr(self.factory, method.lower())("/api/v1/pieza/")
		request.user = user if user is not None else AnonymousUser()
		breakpoint()
		return request

	def test_safe_method_anonimo_permitido(self):
		request = self._request("GET")
		self.assertTrue(self.permiso.has_permission(request, view=None))

	def test_post_anonimo_denegado(self):
		request = self._request("POST")
		self.assertFalse(self.permiso.has_permission(request, view=None))

	def test_post_empleado_denegado(self):
		request = self._request("POST", user=self.empleado)
		self.assertFalse(self.permiso.has_permission(request, view=None))

	def test_patch_empleado_permitido(self):
		request = self._request("PATCH", user=self.empleado)
		self.assertTrue(self.permiso.has_permission(request, view=None))

	def test_delete_admin_permitido(self):
		request = self._request("DELETE", user=self.admin)
		self.assertTrue(self.permiso.has_permission(request, view=None))


class RegistroClienteAPITests(APITestCase):
	def setUp(self):
		self.url = reverse("registro_cliente")

	def test_registro_cliente_crea_cliente_y_lista_deseos(self):
		payload = {
			"user_data": {
				"username": "cliente_nuevo",
				"first_name": "Ana",
				"last_name": "Lopez",
				"email": "ana.lopez@example.com",
				"telefono": "600000001",
				"direccion": "Av. Principal 12",
				"fecha_nacimiento": "1990-05-10",
				"password": "Pass123456!",
			}
		}

		response = self.client.post(self.url, payload, format="json")
		self.assertEqual(response.status_code, 201)

		user = get_user_model().objects.get(email="ana.lopez@example.com")
		self.assertEqual(user.rol, Usuario.CLIENTE)
		self.assertTrue(Cliente.objects.filter(usuario=user).exists())
		self.assertTrue(ListaDeseos.objects.filter(cliente__usuario=user).exists())

	def test_registro_cliente_rechaza_email_repetido(self):
		crear_usuario(
			username="cliente_existente",
			email="duplicado@example.com",
			rol=Usuario.CLIENTE,
		)

		payload = {
			"user_data": {
				"username": "otro_cliente",
				"first_name": "Luis",
				"last_name": "Garcia",
				"email": "duplicado@example.com",
				"telefono": "600000099",
				"direccion": "Calle 45",
				"fecha_nacimiento": "1992-01-01",
				"password": "Pass123456!",
			}
		}

		response = self.client.post(self.url, payload, format="json")
		self.assertEqual(response.status_code, 400)
		self.assertIn("user_data", response.data)


class AuthYPasswordResetAPITests(APITestCase):
	def setUp(self):
		self.usuario = crear_usuario(
			username="cliente_login",
			email="cliente_login@example.com",
			rol=Usuario.CLIENTE,
			password="Pass123456!",
		)

	def test_login_devuelve_tokens(self):
		url = reverse("login_session")
		response = self.client.post(
			url,
			{"username": "cliente_login", "password": "Pass123456!"},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertIn("access", response.data)
		self.assertIn("refresh", response.data)
		self.assertTrue(response.data.get("is_authenticated"))

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_password_reset_envia_correo_si_email_existe(self):
		url = reverse("password_reset")
		mail.outbox = []

		response = self.client.post(
			url,
			{"email": "cliente_login@example.com"},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn("restablecer", mail.outbox[0].body)

	@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
	def test_password_reset_respuesta_neutra_si_email_no_existe(self):
		url = reverse("password_reset")
		mail.outbox = []

		response = self.client.post(
			url,
			{"email": "no-existe@example.com"},
			format="json",
		)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(mail.outbox), 0)


class DevolucionesAPITests(APITestCase):
	def setUp(self):
		self.cliente_user = crear_usuario(
			username="cliente_dev",
			email="cliente_dev@example.com",
			rol=Usuario.CLIENTE,
		)
		self.cliente = Cliente.objects.create(usuario=self.cliente_user)

		self.vendedor_user = crear_usuario(
			username="empleado_dev",
			email="empleado_dev@example.com",
			rol=Usuario.EMPLEADO,
		)
		self.vendedor = Vendedor.objects.create(
			usuario=self.vendedor_user,
			fecha_contratacion=date.today(),
			comision_porcentaje=Decimal("10.00"),
		)

		self.categoria = CategoriaPieza.objects.create(
			nombre="Motor",
			descripcion="Categoria de motores",
		)
		self.pieza = Pieza.objects.create(
			estado=Pieza.NUEVO,
			nombre="Bujia",
			referencia="BUJ-001",
			version="v1",
			marca="Bosch",
			anio=2020,
			precio_base=Decimal("50.00"),
			descripcion="Bujia de prueba",
			stock=3,
			categoria=self.categoria,
		)

		self.pedido = Pedido.objects.create(
			estado=Pedido.ENVIADO,
			cliente=self.cliente,
			vendedor=self.vendedor,
			fecha_pedido=date.today(),
			direccion_envio="Calle Cliente 1",
			total=Decimal("100.00"),
		)

		self.linea = LineaPedido.objects.create(
			pedido=self.pedido,
			pieza=self.pieza,
			cantidad=2,
			precio_unitario=Decimal("50.00"),
			descuento_aplicado=Decimal("0.00"),
			subtotal=Decimal("100.00"),
		)

	def test_cliente_no_puede_devolver_si_pedido_no_entregado(self):
		self.client.force_authenticate(user=self.cliente_user)
		url = reverse("mis-devoluciones-list")

		response = self.client.post(
			url,
			{
				"linea_pedido": self.linea.id,
				"motivo": "Producto incorrecto",
				"cantidad_devuelta": 1,
			},
			format="json",
		)

		self.assertEqual(response.status_code, 400)
		self.assertIn("error", response.data)

	def test_cliente_puede_crear_devolucion_en_pedido_entregado(self):
		self.pedido.estado = Pedido.ENTREGADO
		self.pedido.save(update_fields=["estado"])

		self.client.force_authenticate(user=self.cliente_user)
		url = reverse("mis-devoluciones-list")

		response = self.client.post(
			url,
			{
				"linea_pedido": self.linea.id,
				"motivo": "Producto defectuoso",
				"cantidad_devuelta": 1,
			},
			format="json",
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(Devolucion.objects.count(), 1)
		devolucion = Devolucion.objects.first()
		self.assertEqual(devolucion.estado, Devolucion.PENDIENTE)

	def test_empleado_aprueba_devolucion_y_restaura_stock(self):
		self.pedido.estado = Pedido.ENTREGADO
		self.pedido.save(update_fields=["estado"])

		devolucion = Devolucion.objects.create(
			linea_pedido=self.linea,
			cliente=self.cliente,
			fecha_solicitud=date.today(),
			motivo="Producto defectuoso",
			estado=Devolucion.PENDIENTE,
			cantidad_devuelta=1,
			monto_reembolso=Decimal("50.00"),
		)

		self.client.force_authenticate(user=self.vendedor_user)
		url = reverse("devoluciones-aprobar", args=[devolucion.id])

		response = self.client.post(url, {}, format="json")
		self.assertEqual(response.status_code, 200)

		devolucion.refresh_from_db()
		self.pieza.refresh_from_db()
		self.linea.refresh_from_db()

		self.assertEqual(devolucion.estado, Devolucion.APROBADA)
		self.assertEqual(self.pieza.stock, 4)
		self.assertEqual(self.linea.estado, LineaPedido.DEVUELTO)


