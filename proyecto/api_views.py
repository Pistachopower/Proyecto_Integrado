from .models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets #importante importar viewsets
from rest_framework.generics import CreateAPIView #importante para crear usuarios tipo cliente
from rest_framework.permissions import IsAuthenticated  # Login
from rest_framework.views import APIView # Login

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    http_method_names = ['get', 'post', 'put', 'delete'] ##Esto sirve para controlar los métodos permitidos (lectura, borrado, etc)

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

class VendedorViewSet(viewsets.ModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer

class TiendaViewSet(viewsets.ModelViewSet):
    queryset = Tienda.objects.all()
    serializer_class = TiendaSerializer

class PiezaViewSet(viewsets.ModelViewSet):
    queryset = Pieza.objects.all()
    serializer_class = PiezaSerializer

class InventarioViewSet(viewsets.ModelViewSet):
    queryset = Inventario.objects.all()
    serializer_class = InventarioSerializer

class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer

class LineaPedidoViewSet(viewsets.ModelViewSet):
    queryset = LineaPedido.objects.all()
    serializer_class = LineaPedidoSerializer

class MetodoPagoViewSet(viewsets.ModelViewSet):
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer

class TarjetaViewSet(viewsets.ModelViewSet):
    queryset = Tarjeta.objects.all()
    serializer_class = TarjetaSerializer

class CuentaBancariaViewSet(viewsets.ModelViewSet):
    queryset = CuentaBancaria.objects.all()
    serializer_class = CuentaBancariaSerializer

class BilleteraDigitalViewSet(viewsets.ModelViewSet):
    queryset = BilleteraDigital.objects.all()
    serializer_class = BilleteraDigitalSerializer

class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer

class DevolucionViewSet(viewsets.ModelViewSet):
    queryset = Devolucion.objects.all()
    serializer_class = DevolucionSerializer

class ValoracionViewSet(viewsets.ModelViewSet):
    queryset = Valoracion.objects.all()
    serializer_class = ValoracionSerializer

class ListaDeseosViewSet(viewsets.ModelViewSet):
    queryset = ListaDeseos.objects.all()
    serializer_class = ListaDeseosSerializer

class ListaDeseosPiezaViewSet(viewsets.ModelViewSet):
    queryset = ListaDeseosPieza.objects.all()
    serializer_class = ListaDeseosPiezaSerializer

class DescuentoViewSet(viewsets.ModelViewSet):
    queryset = Descuento.objects.all()
    serializer_class = DescuentoSerializer

class ClienteDescuentoViewSet(viewsets.ModelViewSet):
    queryset = ClienteDescuento.objects.all()
    serializer_class = ClienteDescuentoSerializer


# ============================================================
# CREATE CLIENTE
# ============================================================


class RegistroClienteViewSet(CreateAPIView):
    #permission_classes = [AllowAny]
    serializer_class = RegistroClienteSerializer


class VerMiPerfilView(APIView):
    # 1. ¡Aquí pones al portero!
    # Esto le dice a Django: "Antes de dejar pasar a nadie,
    # comprueba que traiga un "Token de Acceso" válido".
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 2. Gracias a IsAuthenticated, "request.user"
        # será el usuario que hizo login (el dueño del token).
        usuario = request.user
        
        # 3. Buscamos al cliente asociado a ese usuario
        # Usamos .get() porque sabemos que solo hay uno (OneToOneField)
        try:
            cliente = Cliente.objects.get(usuario=usuario)
            
            # 4. Creamos una "ficha" con los datos del cliente para devolverla
            # Usamos tu ClienteSerializer para convertir el objeto a JSON
            serializer = ClienteSerializer(cliente) 
            
            return Response(serializer.data)
            
        except Cliente.DoesNotExist:
            return Response({"error": "No se encontró un perfil de cliente para este usuario."}, status=404)
