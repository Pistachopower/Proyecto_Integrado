from django.urls import path
from .api_views import *
from rest_framework.routers import DefaultRouter #
from django.urls import include

# ¡Importa las vistas que te da simplejwt!
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()  #Este router se encarga de crear mostrar los enlaces de la API ROOT

#(r'usuario')aqui indico cómo se va a generar la url en la API ROOT | basename: hace la referencia entre el serializer y la url
router.register(r'usuario', UsuarioViewSet, basename='usuario') 

router.register(r'cliente', ClienteViewSet, basename='cliente')
router.register(r'vendedor', VendedorViewSet, basename='vendedor')
router.register(r'tienda', TiendaViewSet, basename='tienda')
router.register(r'pieza', PiezaViewSet, basename='pieza')
router.register(r'inventario', InventarioViewSet, basename='inventario')
router.register(r'pedido', PedidoViewSet, basename='pedido')
router.register(r'lineas_pedido', LineaPedidoViewSet, basename='lineapedido')
router.register(r'metodo_pago', MetodoPagoViewSet, basename='metodopago')
router.register(r'tarjeta', TarjetaViewSet, basename='tarjeta')
router.register(r'cuenta_bancaria', CuentaBancariaViewSet, basename='cuentabancaria')
router.register(r'billetera_digital', BilleteraDigitalViewSet, basename='billeteradigital')
router.register(r'pago', PagoViewSet, basename='pago')
router.register(r'devolucion', DevolucionViewSet, basename='devolucion')
router.register(r'valoracion', ValoracionViewSet, basename='valoracion')
router.register(r'lista_deseo', ListaDeseosViewSet, basename='listadeseos')
router.register(r'lista_deseos_pieza', ListaDeseosPiezaViewSet, basename='listadeseospieza')
router.register(r'descuento', DescuentoViewSet, basename='descuento')
router.register(r'cliente_descuento', ClienteDescuentoViewSet, basename='clientedescuento')

urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('registro_cliente/', RegistroClienteViewSet.as_view(), name='registro_cliente'),


    # --- ¡AQUÍ ESTÁ EL LOGIN! ---
    # 1. La URL para "pedir los sellos" (Login)
    # Cuando alguien envíe un POST aquí con "username" y "password"...
    # TokenObtainPairView se encargará de darles los tokens.
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    # 2. La URL para "renovar el sello de acceso"
    # Cuando el token de acceso caduque, envían su "token de refresco" aquí...
    # y TokenRefreshView les dará un token de acceso nuevo.
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('mi-perfil/', VerMiPerfilView.as_view()),

]