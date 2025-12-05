from proyecto.permissions import *
from .models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets #importante importar viewsets
from rest_framework.generics import CreateAPIView #importante para crear usuarios tipo cliente
from rest_framework.permissions import IsAuthenticated  # Login
from rest_framework.views import APIView # Login
from rest_framework import status # Logout
from rest_framework_simplejwt.tokens import RefreshToken # Logout

# ============================================================
# CRUD CON DRF
# ============================================================


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    http_method_names = ['post', 'put', 'delete', 'head','options'] ##Esto sirve para controlar los métodos permitidos (lectura, borrado, etc)
    permission_classes = [IsAuthenticated, EsDuenioUsuarioOSoloLectura]  # Requiere autenticación para acceder a este ViewSet


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]  # Requiere autenticación para acceder a este ViewSet


class VendedorViewSet(viewsets.ModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class TiendaViewSet(viewsets.ModelViewSet):
    queryset = Tienda.objects.all()
    serializer_class = TiendaSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class PiezaViewSet(viewsets.ModelViewSet):
    queryset = Pieza.objects.all()
    serializer_class = PiezaSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class InventarioViewSet(viewsets.ModelViewSet):
    queryset = Inventario.objects.all()
    serializer_class = InventarioSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class LineaPedidoViewSet(viewsets.ModelViewSet):
    queryset = LineaPedido.objects.all()
    serializer_class = LineaPedidoSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class MetodoPagoViewSet(viewsets.ModelViewSet):
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class TarjetaViewSet(viewsets.ModelViewSet):
    queryset = Tarjeta.objects.all()
    serializer_class = TarjetaSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class CuentaBancariaViewSet(viewsets.ModelViewSet):
    queryset = CuentaBancaria.objects.all()
    serializer_class = CuentaBancariaSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class BilleteraDigitalViewSet(viewsets.ModelViewSet):
    queryset = BilleteraDigital.objects.all()
    serializer_class = BilleteraDigitalSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class DevolucionViewSet(viewsets.ModelViewSet):
    queryset = Devolucion.objects.all()
    serializer_class = DevolucionSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class ValoracionViewSet(viewsets.ModelViewSet):
    queryset = Valoracion.objects.all()
    serializer_class = ValoracionSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class ListaDeseosViewSet(viewsets.ModelViewSet):
    queryset = ListaDeseos.objects.all()
    serializer_class = ListaDeseosSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class ListaDeseosPiezaViewSet(viewsets.ModelViewSet):
    queryset = ListaDeseosPieza.objects.all()
    serializer_class = ListaDeseosPiezaSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class DescuentoViewSet(viewsets.ModelViewSet):
    queryset = Descuento.objects.all()
    serializer_class = DescuentoSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]

class ClienteDescuentoViewSet(viewsets.ModelViewSet):
    queryset = ClienteDescuento.objects.all()
    serializer_class = ClienteDescuentoSerializer
    permission_classes = [IsAuthenticated, EsDuenioOSoloLectura]


# ============================================================
# LOGIN Y LOGOUT
# ============================================================


class RegistroClienteViewSet(CreateAPIView):
    serializer_class = RegistroClienteSerializer


class VerMiPerfilView(APIView):

    permission_classes = [IsAuthenticated]  

    #Sobrescribo el método get para devolver los datos del cliente autenticado
    def get(self, request):
        # request.user es el usuario autenticado gracias al token
        # Ahora buscamos el cliente relacionado a ese usuario
        try:
            cliente = Cliente.objects.get(usuario=request.user)
        except Cliente.DoesNotExist:
            return Response({"error": "El cliente no existe"}, status=404)


        # Agregamos context={'request': request} para que pueda crear los enlaces
        serializer = ClienteSerializer(cliente, context={'request': request})
        return Response(serializer.data)


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            # Recibimos el token de refresco del cuerpo de la petición
            refresh_token = request.data["refresh"]
            
            # Instanciamos el token
            token = RefreshToken(refresh_token)
            
            # ¡Lo metemos en la lista negra!
            token.blacklist()

            return Response({"message": "Logout exitoso"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            # Si el token no es válido o hay error, devolvemos 400
            return Response(status=status.HTTP_400_BAD_REQUEST)