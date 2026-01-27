from proyecto.permissions import *
from .models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Avg
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
from django.db.models import Avg
from decimal import Decimal
from datetime import date

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

    #Para el dashboard vendedor - obtener clientes asociados a un vendedor específico
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def clientes_vendedor(self, request):
        """ 
        Obtiene todos los clientes asociados a un vendedor específico mediante pedidos.
        
        GET /api/v1/cliente/clientes_vendedor/?vendedor_id=1
        """
        
        id_vendedor = request.query_params.get('vendedor_id', None)

        if not id_vendedor:
            return Response(
                {'error': 'El parámetro "vendedor_id" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            vendedor = Vendedor.objects.get(id=id_vendedor)

            # Obtenemos todos los clientes asociados a este vendedor mediante pedidos (relacion inversa)
            #Cliente -> Pedido: campo vendedor de Pedido
            clientes = Cliente.objects.filter(pedidos_cliente__vendedor=vendedor).distinct()
            print(f"Total Clientes encontrados: {clientes.count()}")


        
            serializer = ClienteSerializer(clientes, many=True, context={'request': request})
            
            return Response(serializer.data)

        except Vendedor.DoesNotExist:
            return Response(
                {'error': f'Vendedor con ID {id_vendedor} no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            ) 




class VendedorViewSet(viewsets.ModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer
    permission_classes = [IsAuthenticated, EsDuenioDirecto]

    #Para el dashboard vendedor - obtener pedidos asociados a un vendedor específico
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def pedidos_vendedor(self, request):
        """
        Obtiene todos los pedidos asociados a un vendedor específico.
        
        GET /api/v1/vendedor/pedidos_vendedor/?vendedor_id=1
        """
        
        id_vendedor = request.query_params.get('vendedor_id', None)
        
        if not id_vendedor:
            return Response(
                {'error': 'El parámetro "vendedor_id" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            vendedor = Vendedor.objects.get(id=id_vendedor)
            
            # Obtener todos los pedidos del vendedor usando el related_name
            pedidos = vendedor.pedidos_vendedor.all()
            
            print(f"Total Pedidos encontrados: {pedidos.count()}")
            
            serializer = PedidoSimpleSerializer(pedidos, many=True, context={'request': request})
            
            return Response({
                'pedidos': serializer.data
            })
        
        except Vendedor.DoesNotExist:
            return Response(
                {'error': f'Vendedor con ID {id_vendedor} no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            ) 


class CategoriaPiezaViewSet(viewsets.ModelViewSet):
    queryset = CategoriaPieza.objects.all()
    serializer_class = CategoriaPiezaSerializer
    permission_classes = [AllowAny]  # Permite acceso público para ver categorías de piezas

#TODO: CAMBIAR EL NOMBRE DEL PERMISO
class PiezaViewSet(viewsets.ModelViewSet):
    """
    Obtener una pieza específica.
        
    GET /api/v1/pieza/id/
    """
    queryset = Pieza.objects.all()
    serializer_class = PiezaSerializer
    # http_method_names = ['get'] ##Esto sirve para controlar los métodos permitidos (lectura, borrado, etc)
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
  
    #TODO: REVISAR Y PROBAR FUNCIONAMIENTO
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def otros_filtros(self, request):
        """
        Filtra piezas por estado.

        GET /api/piezas/otros_filtros/?estado=activo&estado=pendiente
        GET /api/piezas/otros_filtros/?estado=activo

        Parámetros query:
        - estado: Estado de la pieza (puede repetirse para múltiples valores)
        - busqueda: Búsqueda por nombre
        """
        # Recibe MÚLTIPLES valores: ['activo', 'pendiente']
        estados = request.query_params.getlist('estado')
        busqueda = request.query_params.get('busqueda', None)
        stock = request.query_params.get('stock', None)
        marca= request.query_params.get('marca', None)


        piezas = Pieza.objects.all()

        # Filtrar por estados (si hay)
        if estados:
            piezas = piezas.filter(estado__in=estados)

        # Filtrar por búsqueda (si hay)
        if busqueda:
            piezas = piezas.filter(nombre__icontains=busqueda)

        if stock.lower() == 'true'.lower():
            piezas = piezas.filter(stock__gt=0)

        if marca:
            piezas = piezas.filter(marca__iexact=marca)
            

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
#    
#    filter_backends=[
#        DjangoFilterBackend,
#    ]
#
#    filterset_fields=[
#        'cliente_id' 
#    ]
#
#    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
#    def por_pieza(self, request):
#        """
#        Obtiene todas las valoraciones de una pieza específica.
#
#        GET /api/v1/valoracion/por_pieza/?pieza_id=1
#
#        Parámetros query:
#        - pieza_id (requerido): ID de la pieza
#
#        Respuesta:
#        {
#            "pieza": { ... },
#            "promedio_puntuacion": 4.5,
#            "total_valoraciones": 10,
#            "valoraciones": [ ... ]
#        }
#        """
#
#        pieza_id = request.query_params.get('pieza_id', None)
#
#        if not pieza_id:
#            return Response(
#                {'error': 'El parámetro "pieza_id" es requerido'},
#                status=status.HTTP_400_BAD_REQUEST
#            )
#
#        try:
#            pieza = Pieza.objects.get(id=pieza_id)
#        
#        except Pieza.DoesNotExist:
#            return Response(
#                {'error': f'Pieza con ID {pieza_id} no encontrada'},
#                status=status.HTTP_404_NOT_FOUND
#            )
#
#        # Obtener todas las valoraciones de la pieza
#        #Las ordena por fecha DESCENDENTE (más recientes primero con -fecha_valoracion)
#        valoraciones = Valoracion.objects.filter(pieza=pieza).order_by('-fecha_valoracion')
#
#        # Calcular promedio de puntuación
#        from django.db.models import Avg
#        promedio = valoraciones.aggregate(Avg('puntuacion'))['puntuacion__avg']
#
#        # Serializar las valoraciones
#        serializer = ValoracionSerializer(valoraciones, many=True, context={'request': request})
#
#        # Variable 1: Promedio redondeado a 2 decimales (si hay valoraciones, sino 0)
#        promedio_puntuacion = round(promedio, 2) if promedio else 0
#
#        # Variable 2: Total de valoraciones
#        total_valoraciones = valoraciones.count()
#
#        # Variable 3: Datos serializados de las valoraciones
#        valoraciones_data = serializer.data
#
#        # Serializar la pieza
#        pieza_data = PiezaSerializer(pieza, context={'request': request}).data
#
#        # Retornar Response con las variables
#        return Response({
#            'pieza': pieza_data,
#            'promedio_puntuacion': promedio_puntuacion,
#            'total_valoraciones': total_valoraciones,
#            'valoraciones': valoraciones_data
#        })






class ValoracionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar valoraciones/comentarios de piezas.
    
    - GET /api/v1/valoracion/ -> Lista todas las valoraciones (público)
    - GET /api/v1/valoracion/{id}/ -> Detalle de una valoración (público)
    - PUT /api/v1/valoracion/{id}/ -> Editar valoración (solo si es dueño)
    - DELETE /api/v1/valoracion/{id}/ -> Eliminar valoración (solo si es dueño)
    """
    
    queryset = Valoracion.objects.all()
    serializer_class = ValoracionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente_id', 'pieza_id']
    


    def perform_update(self, serializer):
        """
       Actualiza una valoración.
        """
        serializer.save()


    def perform_destroy(self, instance):
        """
        Elimina una valoración.
        """
        instance.delete()

    #Obtiene las valoraciones de una pieza específica componente frontend C_Valoraciones
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def por_pieza(self, request):
        """
        Endpoint personalizado para obtener valoraciones de una pieza específica.
        
        GET /api/v1/valoracion/por_pieza/?pieza_id=1
        
        Devuelve:
        - Información de la pieza
        - Promedio de puntuación
        - Total de valoraciones
        - Lista de todas las valoraciones
        """
        pieza_id = request.query_params.get('pieza_id', None)

        # Validar que se proporcione el parámetro
        if not pieza_id:
            return Response(
                {'error': 'El parámetro "pieza_id" es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que la pieza existe
        try:
            pieza = Pieza.objects.get(id=pieza_id)
        except Pieza.DoesNotExist:
            return Response(
                {'error': f'Pieza con ID {pieza_id} no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener todas las valoraciones de la pieza de mayor a menor fecha
        valoraciones = Valoracion.objects.filter(
            pieza=pieza
        ).order_by('-fecha_valoracion')

        # Calcular promedio de puntuación
        promedio = valoraciones.aggregate(
            Avg('puntuacion')
        )['puntuacion__avg']

        # Serializar datos
        serializer = ValoracionSerializer(
            valoraciones,
            many=True,
            context={'request': request}
        )

        return Response({
            'pieza': PiezaSerializer(pieza, context={'request': request}).data,
            'promedio_puntuacion': round(promedio, 2) if promedio else 0,
            'total_valoraciones': valoraciones.count(),
            'valoraciones': serializer.data
        })

    #FUNCIONA
    # @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    # def mis_valoraciones(self, request):
    #     """
    #     Endpoint para que un cliente vea sus propias valoraciones.
        
    #     GET /api/v1/valoracion/mis_valoraciones/
    #     """
    #     try:
    #         cliente = request.user.cliente
    #     except:
    #         return Response(
    #             {'error': 'El usuario no es un cliente'},
    #             status=status.HTTP_400_BAD_REQUEST
    #         )

    #     valoraciones = Valoracion.objects.filter(
    #         cliente=cliente
    #     ).order_by('-fecha_valoracion')

    #     serializer = ValoracionSerializer(
    #         valoraciones,
    #         many=True,
    #         context={'request': request}
    #     )

    #     return Response({
    #         'usuario': request.user.email,
    #         'total_valoraciones': valoraciones.count(),
    #         'valoraciones': serializer.data
    #     })




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




#TO: DO: REVISAR Y COMPROBAR FUNCIONAMIENTO
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
        # PASO 2: ACTUALIZACIÓN DE DATOS DE PERFIL (Modelo Vendedor)
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
                
                serializer = UsuarioSerializer(perfil.usuario, data=data, partial=True, context={'request': request})
                
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


#class LoginSessionView(APIView):
#    permission_classes = [AllowAny] # Deja entrar a cualquiera para intentar loguearse
#
#    def post(self, request):
#        # 1. Recogemos usuario y contraseña
#        username = request.data.get('username')
#        password = request.data.get('password')
#
#        # 2. Django verifica si existen
#        user = authenticate(request, username=username, password=password)
#
#        if user is not None:
#            # 3. Esto crea la sesión y mete la cookie en el navegador
#            login(request, user)
#            
#            return Response({
#                "message": "Sesión iniciada correctamente",
#                "user": user.username,
#                # Aquí puedes devolver el rol si quieres para usarlo en Vue
#                "rol": getattr(user, 'rol', None) 
#            }, status=status.HTTP_200_OK)
#        else:
#            return Response(
#                {"error": "Credenciales inválidas"}, 
#                status=status.HTTP_401_UNAUTHORIZED
#            )


class LoginSessionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # 1. Recogemos usuario y contraseña
        username = request.data.get('username')
        password = request.data.get('password')

        # 2. Django verifica si existen
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # 3. Crear la sesión
            login(request, user)
            
            #Si la autenticación es correcta, devolvemos is_authenticated=True y un status 200
            return Response({
                "message": "Sesión iniciada correctamente",
               "is_authenticated": True,
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
    #http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [permissions.IsAuthenticated]

    #Obtiene el carrito actual de la sesión del usuario 
    # (un diccionario con los IDs de las piezas y sus cantidades).
    def get_carrito(self, request):
        #print(request.user)
        return request.session.get('carrito', {})

    #Guarda el carrito actualizado en la sesión.
    def save_carrito(self, request, carrito):
        request.session['carrito'] = carrito
        request.session.modified = True # Asegura que Django guarde los cambios en la sesión

    
    #USE
    def list(self, request):
        """Devuelve el contenido actual del carrito, mostrando 
        información de cada pieza (nombre, imagen, precio, cantidad, 
        etc.) y el precio total.
        """

        carrito = self.get_carrito(request)
        resultado = {}
        items = []
        precio_total = 0
        for pieza_id, info in carrito.items():
            
            # Validar que pieza_id no sea None o 'None'
            #TODO: Arreglar esto mejor (si lo quitas salta error: Field 'id' expected a number but got 'None'.)
            if pieza_id is None or pieza_id == 'None' or pieza_id == '':
                continue

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

    def retrieve(self, request, pk=None):
            """
            Devuelve el detalle de una pieza específica del carrito.
            GET /api/v1/carrito/{pieza_id}/
            """
            carrito = self.get_carrito(request)
            pieza_id = str(pk)
            info = carrito.get(pieza_id)
            if not info:
                return Response({'error': 'Pieza no encontrada en el carrito'}, status=404)
            try:
                pieza = Pieza.objects.get(id=pieza_id)
                imagen_principal = None
                imagen_obj = ImagenPieza.objects.filter(pieza=pieza).first()
                
                if imagen_obj and imagen_obj.url_imagen:
                    #convertir la URL relativa de la imagen en una URL completa
                    imagen_principal = request.build_absolute_uri(imagen_obj.url_imagen.url)
                
                elif pieza.imagen:
                    imagen_principal = request.build_absolute_uri(pieza.imagen.url)
                
                detalle = {
                    'id': pieza.id,
                    'cantidad': info['cantidad'],
                    'nombre': pieza.nombre,
                    'imagen': imagen_principal,
                    'precio': pieza.precio_base,
                    'precio_total_piezas': pieza.precio_base * info['cantidad'],
                }
                return Response(detalle)
            except Pieza.DoesNotExist:
                return Response({'error': 'Pieza no encontrada'}, status=404)


    #USE
    def create(self, request):
        """
        Permite agregar o actualizar una pieza en el carrito. 
        Espera en el body un JSON con pieza_id y cantidad. 
        Si la pieza ya está, actualiza la cantidad; si no, la agrega.
        
        http://127.0.0.1:8000/api/v1/carrito/

        {
            "pieza_id": 7,
            "cantidad": 3
        }
 
        """
        pieza_id = str(request.data.get('pieza_id'))
        cantidad = int(request.data.get('cantidad', 1))
        
        if cantidad < 1:
            return Response({'error': 'Cantidad debe ser mayor a 0'}, status=400)
        
        carrito = self.get_carrito(request)
        
        carrito[pieza_id] = {'cantidad': cantidad}
        self.save_carrito(request, carrito) #guardar en sesión
        return Response({'message': 'Pieza agregada/actualizada', 'carrito': carrito})

    #USE
    def destroy(self, request, pk=None):
        """Eliminar una pieza del carrito por su ID.
        
        DELETE /api/v1/carrito/{pieza_id}/
        
        """
        carrito = self.get_carrito(request)
        pieza_id = str(pk)
        
        if pieza_id in carrito:
            del carrito[pieza_id] #Elimina la pieza del carrito
            self.save_carrito(request, carrito)
            return Response({'message': 'Pieza eliminada', 'carrito': carrito})
        
        return Response({'error': 'Pieza no encontrada en el carrito'}, status=404)


    @action(detail=False, methods=['post'])
    def finalizar(self, request):
        """
        POST /api/v1/carrito/finalizar/
        
        Body:
        {
            "direccion_envio": "Calle Ejemplo 123",
            "metodo_pago_id": 1  // opcional, si no se envía usa el predeterminado
        }
        """

        import uuid

        # 1. Obtener carrito
        carrito = self.get_carrito(request)
        if not carrito:
            return Response({'error': 'El carrito está vacío'}, status=400)

        # 2. Verificar que es cliente
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'error': 'Usuario no es cliente'}, status=400)

        # 3. Verificar que tiene al menos un método de pago
        metodos_cliente = MetodoPago.objects.filter(cliente=cliente)
        if not metodos_cliente.exists():
            return Response({
                'error': 'Debe registrar al menos un método de pago antes de realizar la compra'
            }, status=400)

        # 4. Obtener dirección
        direccion = request.data.get('direccion_envio')
        if not direccion:
            return Response({'error': 'Debe proporcionar una dirección de envío'}, status=400)

        # 5. Obtener método de pago (del body o el predeterminado)
        metodo_pago_id = request.data.get('metodo_pago_id')
        
        if metodo_pago_id:
            try:
                metodo_pago = MetodoPago.objects.get(id=metodo_pago_id, cliente=cliente)
            except MetodoPago.DoesNotExist:
                return Response({'error': 'Método de pago no válido'}, status=400)
        else:
            # Buscar el predeterminado o el primero disponible
            metodo_pago = metodos_cliente.filter(es_predeterminado=True).first()
            if not metodo_pago:
                metodo_pago = metodos_cliente.first()

        # 6. Obtener vendedor
        vendedor = Vendedor.objects.first()
        if not vendedor:
            return Response({'error': 'No hay vendedores disponibles'}, status=500)

        # 7. Preparar líneas y calcular total
        lineas = []
        total = Decimal('0.00')

        for pieza_id, info in carrito.items():
            if not pieza_id or pieza_id == 'None':
                continue

            try:
                pieza = Pieza.objects.get(id=pieza_id)
            except Pieza.DoesNotExist:
                return Response({'error': f'Pieza {pieza_id} no existe'}, status=400)

            cantidad = int(info['cantidad'])

            if pieza.stock < cantidad:
                return Response({
                    'error': f'Stock insuficiente para "{pieza.nombre}". Disponible: {pieza.stock}'
                }, status=400)

            subtotal = pieza.precio_base * cantidad
            total += subtotal

            lineas.append({
                'pieza': pieza,
                'cantidad': cantidad,
                'precio': pieza.precio_base,
                'subtotal': subtotal
            })

        if not lineas:
            return Response({'error': 'No hay productos válidos en el carrito'}, status=400)

        # 8. Crear pedido
        pedido = Pedido.objects.create(
            estado=Pedido.PENDIENTE,
            cliente=cliente,
            vendedor=vendedor,
            fecha_pedido=date.today(),
            direccion_envio=direccion,
            total=total
        )

        # 9. Crear líneas y descontar stock
        for linea in lineas:
            LineaPedido.objects.create(
                pedido=pedido,
                pieza=linea['pieza'],
                cantidad=linea['cantidad'],
                precio_unitario=linea['precio'],
                descuento_aplicado=Decimal('0.00'),
                subtotal=linea['subtotal']
            )
            
            linea['pieza'].stock -= linea['cantidad']
            linea['pieza'].save()

        # 10. Crear registro de pago
        Pago.objects.create(
            pedido=pedido,
            metodo_pago=metodo_pago,
            fecha_pago=date.today(),
            monto=total,
            estado=Pago.PENDIENTE,
        
            #uuid.uuid4() genera un identificador único universal
            numero_transaccion=str(uuid.uuid4())[:20]
        )

        # 11. Vaciar carrito
        self.save_carrito(request, {})

        return Response({
            'message': 'Compra realizada con éxito',
            'pedido_id': pedido.id,
            'total': str(total),
            'items': len(lineas),
            'metodo_pago_usado': metodo_pago.id
        }, status=201)




# ==================== ESTADO DE AUTENTICACIÓN ====================
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

#Para comprobar si el usuario ha iniciado sesión basado en las cookies de sesión
@require_http_methods(["GET"])
def auth_status(request):
    """Verifica si el usuario está autenticado basado en las cookies de sesión."""
    if request.user.is_authenticated:
        return JsonResponse({
            'is_authenticated': request.user.is_authenticated})
    
    return JsonResponse({'is_authenticated': False}, status=403)