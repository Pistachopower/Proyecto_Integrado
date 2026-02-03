from django.urls import path, include
from .api_views import *
from rest_framework.routers import DefaultRouter #
from .api_views import LoginSessionView, LogoutSessionView, ValoracionViewSet, AuthStatusView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView



router = DefaultRouter()  #Este router se encarga de crear mostrar los enlaces de la API ROOT

router.register(r'usuario', UsuarioViewSet, basename='usuario') 
router.register(r'cliente', ClienteViewSet, basename='cliente')
router.register(r'vendedor', VendedorViewSet, basename='vendedor')
router.register(r'categoria_pieza', CategoriaPiezaViewSet, basename='categoriapieza')
router.register(r'pieza', PiezaViewSet, basename='pieza')
router.register(r'pedido', PedidoViewSet, basename='pedido')
router.register(r'lineas_pedido', LineaPedidoViewSet, basename='lineapedido')
router.register(r'metodo_pago', MetodoPagoViewSet, basename='metodopago')
router.register(r'tarjeta', TarjetaViewSet, basename='tarjeta')
router.register(r'cuenta_bancaria', CuentaBancariaViewSet, basename='cuentabancaria')
router.register(r'billetera_digital', BilleteraDigitalViewSet, basename='billeteradigital')
router.register(r'pago', PagoViewSet, basename='pago')
#router.register(r'devolucion', DevolucionViewSet, basename='devolucion')
router.register(r'valoracion', ValoracionViewSet, basename='valoracion')
router.register(r'lista_deseo', ListaDeseosViewSet, basename='listadeseos')
router.register(r'lista_deseos_pieza', ListaDeseosPiezaViewSet, basename='listadeseospieza')
router.register(r'descuento', DescuentoViewSet, basename='descuento')
router.register(r'cliente_descuento', ClienteDescuentoViewSet, basename='clientedescuento')
router.register(r'imagen_pieza', ImagenPiezaViewSet, basename='imagenpieza')

# Ruta para métodos de pago específicos del cliente
router.register(r'metodo_pago_cliente', MetodoPagoClienteViewSet, basename='metodopagocliente')

# Carrito en sesión
router.register(r'carrito', CarritoViewSet, basename='carrito')

#Devoluciones cliente y vendedor
router.register(r'mis-devoluciones', DevolucionClienteViewSet, basename='mis-devoluciones')
router.register(r'devoluciones', DevolucionVendedorViewSet, basename='devoluciones')

urlpatterns = [
    path('', include(router.urls)),

    #/token/: El usuario envía su username y password, y recibe un par de tokens (access y refresh). 
    # El access token se usa para autenticar peticiones, el refresh para obtener nuevos access tokens cuando el anterior expira.
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), 

    #/token/refresh/: El usuario envía su refresh token y recibe un nuevo access token sin tener que volver a iniciar sesión.
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),


    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')), #inicio de sesion API ROOT
    path('registro_cliente/', RegistroClienteViewSet.as_view(), name='registro_cliente'),
    path('mi-perfil/', VerMiPerfilView.as_view()),

    # Rutas de Login/Logout 
    path('login/', LoginSessionView.as_view(), name='login_session'),
    path('logout/', LogoutSessionView.as_view(), name='logout_session'),


    # Estado de autenticación JWT
    path('auth/status/', AuthStatusView.as_view(), name='auth_status'),

    # Dashboard vendedor
    path('dashboard-vendedor/', DashboardVendedorView.as_view(), name='dashboard-vendedor'),

]