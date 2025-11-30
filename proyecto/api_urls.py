from django.urls import path
from .api_views import *
from rest_framework.routers import DefaultRouter #
from django.urls import include

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
]