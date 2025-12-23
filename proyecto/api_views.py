from proyecto.permissions import *
from .models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets,filters #importante importar viewsets
from rest_framework.generics import CreateAPIView #importante para crear usuarios tipo cliente
from rest_framework.permissions import IsAuthenticated  # Login
from rest_framework.views import APIView # Login
from rest_framework import status # Logout
from rest_framework_simplejwt.tokens import RefreshToken # Logout


from django.contrib.auth import login, logout, authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    http_method_names = ['get','post', 'put', 'delete'] ##Esto sirve para controlar los métodos permitidos (lectura, borrado, etc)
    permission_classes = [IsAuthenticated, EsDuenioUsuario]  # Requiere autenticación para acceder a este ViewSet


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated, EsDuenioDirecto]  # Requiere autenticación para acceder a este ViewSet


class VendedorViewSet(viewsets.ModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer
    permission_classes = [IsAuthenticated, EsDuenioDirecto]

class TiendaViewSet(viewsets.ModelViewSet): 
    queryset = Tienda.objects.all()
    serializer_class = TiendaSerializer
    permission_classes = [IsAuthenticated, SoloAdmin]

#TODO: CAMBIAR EL NOMBRE DEL PERMISO
class PiezaViewSet(viewsets.ModelViewSet):
    queryset = Pieza.objects.all()
    serializer_class = PiezaSerializer
    http_method_names = ['get'] ##Esto sirve para controlar los métodos permitidos (lectura, borrado, etc)
    permission_classes = [AllowAny,SoloVerPiezasLineaPedido]

class InventarioViewSet(viewsets.ModelViewSet):
    queryset = Inventario.objects.all()
    serializer_class = InventarioSerializer
    permission_classes = [IsAuthenticated, PermisoGestionInventario]

class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    #permission_classes = [IsAuthenticated, EsDuenioDeObjeto]

    #Permite filtrar los pedidos por cliente_id
    filter_backends=[
        DjangoFilterBackend,
    ]

    filterset_fields=[
        'cliente_id'   ]


#class PedidoViewSet(viewsets.ModelViewSet):
#    serializer_class = PedidoSerializer
#    # CAMBIO IMPORTANTE:
#    # Quitamos 'EsDuenioDeObjeto' porque la seguridad la haremos filtrando la lista (get_queryset).
#    # Si dejáramos EsDuenioDeObjeto, el Vendedor no podría ver el detalle del pedido porque 
#    # ese permiso busca obj.cliente.usuario == request.user.
#    permission_classes = [IsAuthenticated]
#
#    def get_queryset(self):
#        user = self.request.user
#        
#        # Seguridad extra: Si no está autenticado, lista vacía
#        if not user.is_authenticated:
#            return Pedido.objects.none()
#
#        # Obtenemos el rol del usuario
#        rol = getattr(user, 'rol', None)
#
#        # CASO 1: ADMINISTRADOR
#        # El jefe puede ver todos los pedidos del sistema
#        if user.is_staff or user.is_superuser:
#            return Pedido.objects.all()
#
#        # CASO 2: CLIENTE
#        # Filtramos: Dame los pedidos donde el cliente soy YO
#        if rol == Usuario.CLIENTE:
#            return Pedido.objects.filter(cliente__usuario=user)
#
#        # CASO 3: EMPLEADO (Vendedor)
#        # Filtramos: Dame los pedidos donde el vendedor asignado soy YO
#        if rol == Usuario.EMPLEADO:
#            return Pedido.objects.filter(vendedor__usuario=user)
#
#        # Por defecto, no devolver nada
#        return Pedido.objects.none()
    

class LineaPedidoViewSet(viewsets.ModelViewSet):
    queryset = LineaPedido.objects.all()
    serializer_class = LineaPedidoSerializer
    http_method_names = ['get'] ##Esto sirve para controlar los métodos permitidos (lectura, borrado, etc)
    #permission_classes = [IsAuthenticated, SoloVerPiezasLineaPedido]
    permission_classes = [IsAuthenticated, SoloVerPiezasLineaPedido]




class MetodoPagoViewSet(viewsets.ModelViewSet):
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer
    #permission_classes = [IsAuthenticated, EsDuenioDeObjeto]

    filter_backends=[
        DjangoFilterBackend,
    ]

    filterset_fields=[
        'cliente_id'   ]
    

class TarjetaViewSet(viewsets.ModelViewSet):
    queryset = Tarjeta.objects.all()
    serializer_class = TarjetaSerializer
    permission_classes = [IsAuthenticated, EsDuenioDeObjeto]

class CuentaBancariaViewSet(viewsets.ModelViewSet):
    queryset = CuentaBancaria.objects.all()
    serializer_class = CuentaBancariaSerializer
    permission_classes = [IsAuthenticated, EsDuenioDeObjeto]

class BilleteraDigitalViewSet(viewsets.ModelViewSet):
    queryset = BilleteraDigital.objects.all()
    serializer_class = BilleteraDigitalSerializer
    permission_classes = [IsAuthenticated, EsDuenioDeObjeto]

class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated, EsDuenioDeObjeto]

class DevolucionViewSet(viewsets.ModelViewSet):
    queryset = Devolucion.objects.all()
    serializer_class = DevolucionSerializer
    permission_classes = [IsAuthenticated, EsDuenioDeObjeto]

class ValoracionViewSet(viewsets.ModelViewSet):
    queryset = Valoracion.objects.all()
    serializer_class = ValoracionSerializer
    #permission_classes = [IsAuthenticated, EsDuenioDeObjeto]

    #Permite filtrar las valoraciones por cliente_id
    filter_backends=[
        DjangoFilterBackend,
    ]

    filterset_fields=[
        'cliente_id'   ]

class ListaDeseosViewSet(viewsets.ModelViewSet):
    queryset = ListaDeseos.objects.all()
    serializer_class = ListaDeseosSerializer
    permission_classes = [IsAuthenticated, EsDuenioDeObjeto]

class ListaDeseosPiezaViewSet(viewsets.ModelViewSet):
    queryset = ListaDeseosPieza.objects.all()
    serializer_class = ListaDeseosPiezaSerializer
    permission_classes = [IsAuthenticated, EsDuenioDeObjeto]

class DescuentoViewSet(viewsets.ModelViewSet):
    queryset = Descuento.objects.all()
    serializer_class = DescuentoSerializer
    permission_classes = [IsAuthenticated, SoloAdmin]

class ClienteDescuentoViewSet(viewsets.ModelViewSet):
    queryset = ClienteDescuento.objects.all()
    serializer_class = ClienteDescuentoSerializer
    permission_classes = [IsAuthenticated, EsDuenioDeObjeto]


# ============================================================
# LOGIN Y LOGOUT
# ============================================================


class RegistroClienteViewSet(CreateAPIView):
    serializer_class = RegistroClienteSerializer

    permission_classes = [AllowAny]  # Permite el acceso sin autenticación



# proyecto/api_views.py

class VerMiPerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user
        
        # CASO 1: ES UN CLIENTE
        if usuario.rol == Usuario.CLIENTE:
            try:
                perfil = Cliente.objects.get(usuario=usuario)
                serializer = ClienteSerializer(perfil, context={'request': request})
                
                # Truco: Añadimos el campo 'tipo_usuario' a la respuesta JSON
                # para que Vue sepa qué pintar
                data = serializer.data
                data['tipo_usuario'] = 'cliente'
                return Response(data)
                
            except Cliente.DoesNotExist:
                return Response({"error": "Perfil de cliente no encontrado"}, status=404)

        # CASO 2: ES UN EMPLEADO (VENDEDOR)
        elif usuario.rol == Usuario.EMPLEADO:
            try:
                # Modelo Vendedor vinculado al usuario
                perfil = Vendedor.objects.get(usuario=usuario)
                serializer = VendedorSerializer(perfil, context={'request': request})
                
                data = serializer.data
                data['tipo_usuario'] = 'empleado'
                return Response(data)
                
            except Vendedor.DoesNotExist:
                return Response({"error": "Perfil de vendedor no encontrado"}, status=404)

        # CASO 3: ADMINISTRADOR (Opcional, si tiene perfil propio o devolvemos datos básicos)
        elif usuario.is_staff or usuario.is_superuser:
             return Response({
                 "username": usuario.username,
                 "email": usuario.email,
                 "tipo_usuario": "admin",
                 "nombre": "Administrador",
                 "apellido": "Sistema"
             })

        return Response({"error": "Rol de usuario desconocido"}, status=400)





class LoginSessionView(APIView):
    permission_classes = [AllowAny] # Deja entrar a cualquiera para intentar loguearse

    def post(self, request):
        # 1. Recogemos usuario y contraseña
        username = request.data.get('username')
        password = request.data.get('password')

        # 2. Django verifica si existen
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # 3. ¡LA MAGIA! Esto crea la sesión y mete la cookie en el navegador
            login(request, user)
            
            return Response({
                "message": "Sesión iniciada correctamente",
                "user": user.username,
                # Aquí puedes devolver el rol si quieres para usarlo en Vue
                "rol": getattr(user, 'rol', None) 
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Credenciales inválidas"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

class LogoutSessionView(APIView):
    def post(self, request):
        # Esto borra la cookie y la sesión del servidor
        logout(request)
        return Response({"message": "Sesión cerrada"}, status=status.HTTP_200_OK)
