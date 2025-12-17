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


from django.contrib.auth import login, logout, authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, AllowAny

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    http_method_names = ['get','post', 'put', "patch", 'delete'] ##Esto sirve para controlar los métodos permitidos (lectura, borrado, etc)
    permission_classes = [IsAuthenticated, PermisoSoloVerEditarPropioUsuario]  # Requiere autenticación para acceder a este ViewSet

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, 'rol', None)

        # ADMINISTRADOR: ve todos los usuarios
        if rol == Usuario.ADMINISTRADOR:
            return Usuario.objects.all()
        # EMPLEADO y CLIENTE: solo su propio usuario
        elif rol in [Usuario.EMPLEADO, Usuario.CLIENTE]:
            return Usuario.objects.filter(id=user.id)
        # Otros: ninguno
        return Usuario.objects.none()

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    http_method_names = ['get','post', 'put', "patch"]
    permission_classes = [IsAuthenticated, PermisoSoloVerEditarPropioCliente]  # Requiere autenticación para acceder a este ViewSet

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, 'rol', None)

        # ADMINISTRADOR: ve todos los clientes
        if rol == Usuario.ADMINISTRADOR:
            return Cliente.objects.all()
        # CLIENTE: solo su propio objeto cliente
        elif rol == Usuario.CLIENTE:
            return Cliente.objects.filter(usuario=user)
        # Otros: ninguno
        return Cliente.objects.none()
    


class VendedorViewSet(viewsets.ModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer
    http_method_names = ['get','post', 'put', "patch"]
    permission_classes = [IsAuthenticated,PermisoSoloVerEditarPropioEmpleado]

class TiendaViewSet(viewsets.ModelViewSet): 
    queryset = Tienda.objects.all()
    serializer_class = TiendaSerializer
    permission_classes = [IsAuthenticated,PermisoSoloVerTienda]

class PiezaViewSet(viewsets.ModelViewSet):
    queryset = Pieza.objects.all()
    serializer_class = PiezaSerializer
    permission_classes = [PermisoSoloVerPieza]

class InventarioViewSet(viewsets.ModelViewSet):
    queryset = Inventario.objects.all()
    serializer_class = InventarioSerializer
    permission_classes = [IsAuthenticated,PermisoInventarioSinAccesoCliente]

class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated, PermisoEmpleadoClienteEditarEstadoDireccionPedido]

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, 'rol', None)

        # ADMINISTRADOR: ve todos los pedidos
        if rol == Usuario.ADMINISTRADOR:
            return Pedido.objects.all()
        # CLIENTE: solo sus pedidos
        elif rol == Usuario.CLIENTE:
            return Pedido.objects.filter(cliente__usuario=user)
        # EMPLEADO: puedes ajustar aquí si quieres que vea otros pedidos
        
        elif rol == Usuario.EMPLEADO:
            return Pedido.objects.all()  # O ajusta el filtro según tu lógica
        ## Otros: ninguno
        return Pedido.objects.none()

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
    

# Asegúrate de importar el nuevo permiso
from proyecto.permissions import EsDuenioLineaPedido 

class LineaPedidoViewSet(viewsets.ModelViewSet):
    serializer_class = LineaPedidoSerializer
    # Usamos el nuevo permiso que SÍ deja pasar al cliente
    permission_classes = [IsAuthenticated, EsDuenioLineaPedido]

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, 'rol', None)

        # 1. Admin y Empleado ven TODO (para preparar pedidos)
        if rol in [Usuario.ADMINISTRADOR, Usuario.EMPLEADO]:
            return LineaPedido.objects.all()

        # 2. Cliente solo ve las líneas de SUS pedidos
        # La ruta es: LineaPedido -> pedido -> cliente -> usuario
        if rol == Usuario.CLIENTE:
            return LineaPedido.objects.filter(pedido__cliente__usuario=user)

        # Por seguridad, si no cae en ninguno de los anteriores, retorna nada
        return LineaPedido.objects.none()

#class MetodoPagoViewSet(viewsets.ModelViewSet):
#    queryset = MetodoPago.objects.all()
#    serializer_class = MetodoPagoSerializer
#    permission_classes = [IsAuthenticated,PermisoEliminarMetodoPagoSoloAdmin]
#
#class TarjetaViewSet(viewsets.ModelViewSet):
#    queryset = Tarjeta.objects.all()
#    serializer_class = TarjetaSerializer
#    permission_classes = [IsAuthenticated, PermisoEliminarTarjetaSoloAdmin]
#
#class CuentaBancariaViewSet(viewsets.ModelViewSet):
#    queryset = CuentaBancaria.objects.all()
#    serializer_class = CuentaBancariaSerializer
#    permission_classes = [IsAuthenticated, PermisoEliminarTarjetaSoloAdmin]
#
#class BilleteraDigitalViewSet(viewsets.ModelViewSet):
#    queryset = BilleteraDigital.objects.all()
#    serializer_class = BilleteraDigitalSerializer
#    permission_classes = [IsAuthenticated, PermisoEliminarBilleteraDigitalSoloAdmin]


# api_views.py

# 1. VIEWSET PADRE (Metodo de Pago General) 
class MetodoPagoViewSet(viewsets.ModelViewSet):
    serializer_class = MetodoPagoSerializer
    permission_classes = [IsAuthenticated, EsDuenioMetodoPago]

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, 'rol', None)

        if rol == Usuario.ADMINISTRADOR:
            return MetodoPago.objects.all()
        
        # MetodoPago SÍ tiene el campo 'cliente' directo
        return MetodoPago.objects.filter(cliente__usuario=user)

    def perform_create(self, serializer):
        cliente = Cliente.objects.get(usuario=self.request.user)
        serializer.save(cliente=cliente)


# 2. VIEWSET TARJETAS 
class TarjetaViewSet(viewsets.ModelViewSet):
    serializer_class = TarjetaSerializer
    permission_classes = [IsAuthenticated, EsDuenioMetodoPago]

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, 'rol', None)

        if rol == Usuario.ADMINISTRADOR:
            return Tarjeta.objects.all()
        
        # CORRECCIÓN: Tarjeta -> metodo_pago -> cliente -> usuario
        return Tarjeta.objects.filter(metodo_pago__cliente__usuario=user)

    def perform_create(self, serializer):
        pass 


# 3. VIEWSET CUENTAS BANCARIAS
class CuentaBancariaViewSet(viewsets.ModelViewSet):
    serializer_class = CuentaBancariaSerializer
    permission_classes = [IsAuthenticated, EsDuenioMetodoPago]

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, 'rol', None)

        if rol == Usuario.ADMINISTRADOR:
            return CuentaBancaria.objects.all()
        
        #CuentaBancaria -> metodo_pago -> cliente -> usuario
        return CuentaBancaria.objects.filter(metodo_pago__cliente__usuario=user)


# 4. VIEWSET BILLETERAS DIGITALES
class BilleteraDigitalViewSet(viewsets.ModelViewSet):
    serializer_class = BilleteraDigitalSerializer
    permission_classes = [IsAuthenticated, EsDuenioMetodoPago]

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, 'rol', None)

        if rol == Usuario.ADMINISTRADOR:
            return BilleteraDigital.objects.all()
        
        #BilleteraDigital -> metodo_pago -> cliente -> usuario
        return BilleteraDigital.objects.filter(metodo_pago__cliente__usuario=user)


class PagoViewSet(viewsets.ModelViewSet):
    queryset = Pago.objects.all()
    serializer_class = PagoSerializer
    permission_classes = [IsAuthenticated, PermisoEmpleadoEditarEstadoPago]

class DevolucionViewSet(viewsets.ModelViewSet):
    serializer_class = DevolucionSerializer
    permission_classes = [IsAuthenticated, EsDuenioDevolucion]
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, 'rol', None)

        # 1. Admin y Empleado ven TODAS las devoluciones
        if rol in [Usuario.ADMINISTRADOR, Usuario.EMPLEADO]:
            return Devolucion.objects.all()

        # 2. Cliente solo ve las SUYAS (usando el campo directo 'cliente')
        return Devolucion.objects.filter(cliente__usuario=user)

    def perform_create(self, serializer):
        user = self.request.user
        
        # Si es un cliente quien crea la devolución, forzamos que el campo 'cliente' sea él mismo.
        if getattr(user, 'rol', None) == Usuario.CLIENTE:
            cliente_obj = Cliente.objects.get(usuario=user)
            serializer.save(cliente=cliente_obj)
        else:
            # Si crea un Admin o Empleado, dejamos que el serializer use el cliente que venga en el JSON
            serializer.save()

class ValoracionViewSet(viewsets.ModelViewSet):
    queryset = Valoracion.objects.all()
    serializer_class = ValoracionSerializer
    permission_classes = [IsAuthenticated]


class ListaDeseosViewSet(viewsets.ModelViewSet):
    serializer_class = ListaDeseosSerializer
    # Usamos el permiso nuevo
    permission_classes = [IsAuthenticated, EsDuenioListaDeseos] 
    http_method_names = ['get'] # El cliente no crea la lista manual, se crea al registro

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, 'rol', None)

        if rol == Usuario.ADMINISTRADOR:
            return ListaDeseos.objects.all()

        # CLIENTE: Filtramos para que solo reciba SU lista
        if rol == Usuario.CLIENTE:
            return ListaDeseos.objects.filter(cliente__usuario=user)
            
        return ListaDeseos.objects.none()





class ListaDeseosPiezaViewSet(viewsets.ModelViewSet):
    serializer_class = ListaDeseosPiezaSerializer
    # Usamos el permiso nuevo para items
    permission_classes = [IsAuthenticated, EsDuenioItemListaDeseos]

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, 'rol', None)

        if rol == Usuario.ADMINISTRADOR:
            return ListaDeseosPieza.objects.all()

        # CLIENTE: Filtramos items que pertenezcan a una lista que sea suya
        if rol == Usuario.CLIENTE:
            return ListaDeseosPieza.objects.filter(lista_deseos__cliente__usuario=user)
            
        return ListaDeseosPieza.objects.none()

    def perform_create(self, serializer):
        """
        Cuando el cliente agrega una pieza, NO le dejamos elegir la lista.
        El sistema busca su lista automáticamente y la asigna.
        """
        user = self.request.user
        
        if getattr(user, 'rol', None) == Usuario.CLIENTE:
            # 1. Buscamos la lista de deseos de este usuario
            # (Usamos get_object_or_404 por si alguien intenta agregar a la petición una lista que no es suya)
            from django.shortcuts import get_object_or_404
            mi_lista = get_object_or_404(ListaDeseos, cliente__usuario=user)
            
            # 2. Guardamos el item forzando la lista correcta
            serializer.save(lista_deseos=mi_lista)
        else:
            # Si es admin, dejamos que decida él
            serializer.save()

class DescuentoViewSet(viewsets.ModelViewSet):
    """
    Vista administrativa para gestionar las campañas de descuentos.
    El cliente NO entra aquí.
    """
    queryset = Descuento.objects.all()
    serializer_class = DescuentoSerializer
    permission_classes = [IsAuthenticated, PermisoGestionDescuentos]

class ClienteDescuentoViewSet(viewsets.ModelViewSet):
    serializer_class = ClienteDescuentoSerializer
    permission_classes = [IsAuthenticated, PermisoClienteDescuento]

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, 'rol', None)

        # 1. ADMINISTRADORES y EMPLEADOS:
        # Ven todos los descuentos de todos los clientes
        if rol in [Usuario.ADMINISTRADOR, Usuario.EMPLEADO]:
            return ClienteDescuento.objects.all()

        # 2. CLIENTES:
        # Solo ven los registros que les pertenecen a ellos
        if rol == Usuario.CLIENTE:
            return ClienteDescuento.objects.filter(cliente__usuario=user)

        # Por seguridad, si no es ninguno de los anteriores, no devolvemos nada
        return ClienteDescuento.objects.none()


# ============================================================
# LOGIN Y LOGOUT
# ============================================================

#Utiliza CreateAPIView (una vista genérica más simple que un ViewSet)
class RegistroClienteViewSet(CreateAPIView):
    serializer_class = RegistroClienteSerializer

    permission_classes = [AllowAny]  # Permite el acceso sin autenticación



class VerMiPerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user
        
        # CASO 1: ES UN CLIENTE
        if usuario.rol == Usuario.CLIENTE:
            try:
                perfil = Cliente.objects.get(usuario=usuario)
                serializer = ClienteSerializer(perfil, context={'request': request})
                
                # Añadimos el campo 'tipo_usuario' a la respuesta JSON
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

        # CASO 3: ADMINISTRADOR (si tiene perfil propio o devolvemos datos básicos)
        elif usuario.is_staff or usuario.is_superuser:
             return Response({
                 "username": usuario.username,
                 "email": usuario.email,
                 "tipo_usuario": "admin",
                 "nombre": "Administrador",
                 "apellido": "Sistema"
             })

        return Response({"error": "Rol de usuario desconocido"}, status=400)




#Utiliza CreateAPIView (una vista genérica más simple que un ViewSet)
class LoginSessionView(APIView):
    permission_classes = [AllowAny] # Deja entrar a cualquiera para intentar loguearse

    def post(self, request):
        # 1. Recogemos usuario y contraseña
        username = request.data.get('username')
        password = request.data.get('password')

        # 2. Django verifica si existen
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # 3. Esto crea la sesión y mete la cookie en el navegador
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