from proyecto.permissions import *
from .models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework import status
from rest_framework.viewsets import ViewSet
from rest_framework import viewsets,filters #importante importar viewsets
from rest_framework.generics import CreateAPIView #importante para crear usuarios tipo cliente
from rest_framework.permissions import IsAuthenticated  # Login
from rest_framework.views import APIView # Login
from rest_framework import status # Logout
from rest_framework_simplejwt.tokens import RefreshToken # Logout


from django.contrib.auth import login, logout, authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend # Filtros para los ViewSets


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    http_method_names = ['get','post', 'put', 'delete'] ##Esto sirve para controlar los métodos permitidos (lectura, borrado, etc)
    permission_classes = [IsAuthenticated, EsDuenioUsuario]  # Requiere autenticación para acceder a este ViewSet


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated, EsDuenioDirecto]


class VendedorViewSet(viewsets.ModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer
    permission_classes = [IsAuthenticated, EsDuenioDirecto]


class CategoriaPiezaViewSet(viewsets.ModelViewSet):
    queryset = CategoriaPieza.objects.all()
    serializer_class = CategoriaPiezaSerializer
    permission_classes = [AllowAny]  # Permite acceso público para ver categorías de piezas

#TODO: CAMBIAR EL NOMBRE DEL PERMISO
class PiezaViewSet(viewsets.ModelViewSet):
    queryset = Pieza.objects.all()
    serializer_class = PiezaSerializer
    http_method_names = ['get'] ##Esto sirve para controlar los métodos permitidos (lectura, borrado, etc)
    permission_classes = [AllowAny] #TODO: Permitir ver piezas pero no crear/modificar/borrar (admin,empleado) 

    filter_backends= [DjangoFilterBackend]
    filterset_fields= ['categoria'] #Permite filtrar las piezas por categoría
    
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def por_marca(self, request):
        """
        Devuelve piezas de la misma marca, excluyendo la pieza actual.
        
        GET /api/piezas/por_marca/?pieza_id=1&limite=6
        
        Parámetros query:
        - pieza_id (requerido): ID de la pieza actual para obtener su marca
        - limite: Número de piezas a devolver (default=6)
        """
        pieza_id = request.query_params.get('pieza_id', None)
        limite = int(request.query_params.get('limite', 6))
        
        if not pieza_id:
            return Response(
                {'error': 'El parámetro "pieza_id" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pieza_actual = Pieza.objects.get(id=pieza_id)
        except Pieza.DoesNotExist:
            return Response(
                {'error': f'Pieza con ID {pieza_id} no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Filtrar piezas de la misma marca, excluyendo la pieza actual
        #__iexact: muestre las piezas sin importar mayúsculas o minúsculas
        piezas = Pieza.objects.filter(
            marca__iexact=pieza_actual.marca
        ).exclude(
            id=pieza_id
        )[:limite]
        
        if not piezas.exists():
            # Si no hay piezas de la misma marca, devolver aleatorias
            from django.db.models.functions import Random
            piezas = Pieza.objects.exclude(id=pieza_id).order_by(Random())[:limite]
        
        serializer = PiezaSerializer(piezas, many=True, context={'request': request})
        return Response(serializer.data)
  


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
    

# ============================================================
# METODO DE PAGO PARA CLIENTE
# ============================================================
class MetodoPagoClienteViewSet(viewsets.ModelViewSet):
    
    permission_classes = [permissions.IsAuthenticated]

    filter_backends=[
        DjangoFilterBackend,
    ]

    filterset_fields=[
        'cliente_id'   ]


    def get_queryset(self):
        # Filtramos para que el usuario solo vea SUS métodos
        return MetodoPago.objects.filter(cliente=self.request.user.cliente)

    def get_serializer_class(self):
        # Usamos el serializador complejo para CREAR (POST) y ACTUALIZAR (PUT/PATCH)
        if self.action in ['create', 'update', 'partial_update', 'retrieve', 'list']:

            return CrearMetodoPagoUnificadoSerializer
        # Usamos el serializador original para LISTAR/VER (GET)
        return MetodoPagoSerializer


    def perform_destroy(self, instance):
        """
        Maneja la eliminación de un método de pago.
        IMPORTANTE: Pasamos el contexto con el request para evitar errores con HyperlinkedIdentityField.
        """
        serializer = CrearMetodoPagoUnificadoSerializer(instance, context=self.get_serializer_context())
        serializer.destroy()

    

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

#class ValoracionViewSet(viewsets.ModelViewSet):
#    queryset = Valoracion.objects.all()
#    serializer_class = ValoracionSerializer
#    #permission_classes = [IsAuthenticated, EsDuenioDeObjeto]
#
#    #Permite filtrar las valoraciones por cliente_id
#    filter_backends=[
#        DjangoFilterBackend,
#    ]
#
#    filterset_fields=[
#        'cliente_id'   ]
    
class ValoracionViewSet(viewsets.ModelViewSet):
    queryset = Valoracion.objects.all()
    serializer_class = ValoracionSerializer
    
    filter_backends=[
        DjangoFilterBackend,
    ]

    filterset_fields=[
        'cliente_id' 
    ]

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def por_pieza(self, request):
        """
        Obtiene todas las valoraciones de una pieza específica.

        GET /api/v1/valoracion/por_pieza/?pieza_id=1

        Parámetros query:
        - pieza_id (requerido): ID de la pieza

        Respuesta:
        {
            "pieza": { ... },
            "promedio_puntuacion": 4.5,
            "total_valoraciones": 10,
            "valoraciones": [ ... ]
        }
        """

        pieza_id = request.query_params.get('pieza_id', None)

        if not pieza_id:
            return Response(
                {'error': 'El parámetro "pieza_id" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pieza = Pieza.objects.get(id=pieza_id)
        
        except Pieza.DoesNotExist:
            return Response(
                {'error': f'Pieza con ID {pieza_id} no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener todas las valoraciones de la pieza
        #Las ordena por fecha DESCENDENTE (más recientes primero con -fecha_valoracion)
        valoraciones = Valoracion.objects.filter(pieza=pieza).order_by('-fecha_valoracion')

        # Calcular promedio de puntuación
        from django.db.models import Avg
        promedio = valoraciones.aggregate(Avg('puntuacion'))['puntuacion__avg']

        # Serializar las valoraciones
        serializer = ValoracionSerializer(valoraciones, many=True, context={'request': request})

        # Variable 1: Promedio redondeado a 2 decimales (si hay valoraciones, sino 0)
        promedio_puntuacion = round(promedio, 2) if promedio else 0

        # Variable 2: Total de valoraciones
        total_valoraciones = valoraciones.count()

        # Variable 3: Datos serializados de las valoraciones
        valoraciones_data = serializer.data

        # Serializar la pieza
        pieza_data = PiezaSerializer(pieza, context={'request': request}).data

        # Retornar Response con las variables
        return Response({
            'pieza': pieza_data,
            'promedio_puntuacion': promedio_puntuacion,
            'total_valoraciones': total_valoraciones,
            'valoraciones': valoraciones_data
        })

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
    
    def put(self, request):
        """
        Actualiza los datos del Usuario (email) y del Perfil específico (Cliente/Vendedor).
        """
        usuario = request.user
        data = request.data # Los datos que envía el frontend (Vue)

        # ---------------------------------------------------------
        # PASO 1: ACTUALIZACIÓN DE DATOS DE CUENTA (Modelo Usuario)
        # ---------------------------------------------------------
        # Verificamos si quieren cambiar el email
        nuevo_email = data.get('email')
        
        if nuevo_email and nuevo_email != usuario.email:
            # Comprobamos que el email no esté usado por OTRA persona
            if Usuario.objects.filter(email=nuevo_email).exclude(pk=usuario.pk).exists():
                return Response(
                    {"email": ["Correo inválido."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            usuario.email = nuevo_email
            usuario.save() # Guardamos el cambio en la tabla Usuario

        # Verificamos si quieren cambiar el nombre del usuario
        nuevo_username = data.get('username')
        
        if nuevo_username != usuario.username:
            return Response(
                {"username": ["No se puede cambiar el nombre de usuario."]},
                status=status.HTTP_400_BAD_REQUEST
            )
           
        

        # ---------------------------------------------------------
        # PASO 2: ACTUALIZACIÓN DE DATOS DE PERFIL (Modelo Cliente/Vendedor)
        # ---------------------------------------------------------
        
        # CASO A: ES UN CLIENTE
        if usuario.rol == Usuario.CLIENTE:
            try:
                perfil = Cliente.objects.get(usuario=usuario)
                
                # Usamos el Serializer para validar y guardar los datos del perfil
                # partial=True permite enviar solo el nombre sin tener que enviar todo lo demás
                serializer = UsuarioSerializer(perfil.usuario, data=data, partial=True, context={'request': request})
                
                if serializer.is_valid():
                    serializer.save()
                    
                    # Preparamos respuesta
                    respuesta_data = serializer.data
                    respuesta_data['tipo_usuario'] = 'cliente'
                    # Aseguramos que el email devuelto sea el actualizado
                    respuesta_data['email'] = usuario.email 
                    
                    return Response(respuesta_data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            except Cliente.DoesNotExist:
                return Response({"error": "Perfil de cliente no encontrado"}, status=404)

        # CASO B: ES UN EMPLEADO
        elif usuario.rol == Usuario.EMPLEADO:
            try:
                perfil = Vendedor.objects.get(usuario=usuario)
                
                serializer = VendedorSerializer(perfil, data=data, partial=True)
                
                if serializer.is_valid():
                    serializer.save()
                    
                    respuesta_data = serializer.data
                    respuesta_data['tipo_usuario'] = 'empleado'
                    respuesta_data['email'] = usuario.email
                    
                    return Response(respuesta_data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
            except Vendedor.DoesNotExist:
                return Response({"error": "Perfil de vendedor no encontrado"}, status=404)

        return Response({"error": "No se pueden editar datos de Administrador aquí"}, status=403)


class ImagenPiezaViewSet(viewsets.ModelViewSet):
    queryset = ImagenPieza.objects.all()
    serializer_class = ImagenPiezaSerializer
    permission_classes = [AllowAny]


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


# ===================== CARRITO EN SESIÓN =====================
class CarritoViewSet(ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def _get_carrito(self, request):
        print(request.user)
        return request.session.get('carrito', {})

    def _save_carrito(self, request, carrito):
        request.session['carrito'] = carrito
        request.session.modified = True # Asegura que Django guarde los cambios en la sesión

    def list(self, request):
        """Obtener el carrito actual con info de piezas"""
        from .models import Pieza, ImagenPieza
        carrito = self._get_carrito(request)
        resultado = {}
        items = []
        precio_total = 0
        for pieza_id, info in carrito.items():
            try:
                pieza = Pieza.objects.get(id=pieza_id)
                # Buscar imagen principal: primero ImagenPieza, si no, el campo imagen de Pieza
                imagen_principal = None
                imagen_obj = ImagenPieza.objects.filter(pieza=pieza).first()
                if imagen_obj and imagen_obj.url_imagen:
                    imagen_principal = request.build_absolute_uri(imagen_obj.url_imagen.url)
                elif pieza.imagen:
                    imagen_principal = request.build_absolute_uri(pieza.imagen.url)
                
                items.append({
                    'id': pieza.id,
                    'cantidad': info['cantidad'],
                    'nombre': pieza.nombre,
                    'imagen': imagen_principal,
                    'precio': pieza.precio_base,
                    'precio_total_piezas': pieza.precio_base * info['cantidad'],
                    

                })
                precio_total += pieza.precio_base * info['cantidad']

            except Pieza.DoesNotExist:
                continue

        resultado['items'] = items
        resultado['precio_total'] = precio_total
        return Response(resultado)

    def create(self, request):
        """Agregar o actualizar una pieza en el carrito"""
        pieza_id = str(request.data.get('pieza_id'))
        cantidad = int(request.data.get('cantidad', 1))
        
        if cantidad < 1:
            return Response({'error': 'Cantidad debe ser mayor a 0'}, status=400)
        
        carrito = self._get_carrito(request)
        # Puedes agregar más info si lo deseas (precio, nombre, etc)
        carrito[pieza_id] = {'cantidad': cantidad}
        self._save_carrito(request, carrito) #guardar en sesión
        return Response({'message': 'Pieza agregada/actualizada', 'carrito': carrito})

    def destroy(self, request, pk=None):
        """Eliminar una pieza del carrito"""
        carrito = self._get_carrito(request)
        pieza_id = str(pk)
        if pieza_id in carrito:
            del carrito[pieza_id]
            self._save_carrito(request, carrito)
            return Response({'message': 'Pieza eliminada', 'carrito': carrito})
        return Response({'error': 'Pieza no encontrada en el carrito'}, status=404)

    @action(detail=False, methods=['post'])
    def vaciar(self, request):
        """Vaciar el carrito"""
        self._save_carrito(request, {})
        return Response({'message': 'Carrito vaciado'})

    @action(detail=False, methods=['post'])
    def finalizar(self, request):
        """Finalizar compra: crea Pedido y LineaPedido, limpia carrito"""
        from .models import Pedido, LineaPedido, Pieza, Cliente, Tienda, Vendedor
        from decimal import Decimal
        carrito = self._get_carrito(request)
        
        if not carrito:
            return Response({'error': 'El carrito está vacío'}, status=400)
        user = request.user
        
        try:
            cliente = user.cliente
        
        except Exception:
            return Response({'error': 'El usuario no es cliente'}, status=400)
        
        tienda = Tienda.objects.first()
        vendedor = Vendedor.objects.first()

        if not tienda or not vendedor:
            return Response({'error': 'No hay tienda o vendedor configurado'}, status=400)
        
        total = Decimal('0.00')
        lineas = []
        
        for pieza_id, info in carrito.items():
            pieza = get_object_or_404(Pieza, id=pieza_id)
            cantidad = int(info['cantidad'])
            precio_unitario = pieza.precio_base
            subtotal = precio_unitario * cantidad
            total += subtotal
            lineas.append({'pieza': pieza, 'cantidad': cantidad, 'precio_unitario': precio_unitario, 'subtotal': subtotal})
        
        pedido = Pedido.objects.create(
            estado=Pedido.PENDIENTE,
            cliente=cliente,
            tienda=tienda,
            vendedor=vendedor,
            fecha_pedido=None,  # Puedes poner date.today() si quieres 
            direccion_envio='(por definir)',
            total=total
        )
        for l in lineas:
            LineaPedido.objects.create(
                pedido=pedido,
                pieza=l['pieza'],
                cantidad=l['cantidad'],
                precio_unitario=l['precio_unitario'],
                descuento_aplicado=0,
                subtotal=l['subtotal']
            )
        self._save_carrito(request, {})
        return Response({'message': 'Compra finalizada', 'pedido_id': pedido.id})
    


# ==================== ESTADO DE AUTENTICACIÓN ====================
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def auth_status(request):
    """Verifica si el usuario está autenticado basado en las cookies de sesión."""
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': request.user.is_authenticated})
    
    return JsonResponse({'authenticated': False}, status=403)