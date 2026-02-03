from proyecto.permissions import *
from .models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Avg
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
from datetime import date, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods



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
    """
            PATCH /api/v1/pedido/{id}/cambiar_estado_vendedor/
            Body: {"estado": 2}
    """
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    #permission_classes = [IsAuthenticated, EsDuenioDeObjeto]

    #Permite filtrar los pedidos por cliente_id
    filter_backends=[
        DjangoFilterBackend,
    ]

    filterset_fields=[
        'cliente_id'   ]
    
    @action(detail=True, methods=['patch'])
    def cambiar_estado_vendedor(self, request, pk=None):
        pedido = self.get_object()
        serializer = CambiarEstadoPedidoVendedorSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        estado_anterior = pedido.get_estado_display()
        pedido.estado = serializer.validated_data['estado']
        pedido.save()

        return Response({
            'mensaje': 'Estado actualizado',
            'pedido_id': pedido.id,
            'estado_anterior': estado_anterior,
            'estado_actual': pedido.get_estado_display()
        })

    # def perform_create(self, serializer):
    #     pedido = serializer.save()
    #     cliente = pedido.cliente
    #     # Intentar asignar el descuento de fidelidad si corresponde
    #     asignar_descuento_fidelidad(cliente)


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

# class DevolucionViewSet(viewsets.ModelViewSet):
#     queryset = Devolucion.objects.all()
#     serializer_class = DevolucionSerializer
#     permission_classes = [IsAuthenticated, EsDuenioDeObjeto]




class DevolucionClienteViewSet(viewsets.ModelViewSet):
    """
    ViewSet para que los clientes gestionen sus devoluciones.
    
    POST /api/v1/mis-devoluciones/
    {
        "linea_pedido_id": 1,
        "motivo": "El producto llegó dañado",
        "cantidad_devuelta": 2
    }
    """
    serializer_class = DevolucionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Solo muestra las devoluciones del cliente autenticado."""
        try:
            cliente = self.request.user.cliente
            return Devolucion.objects.filter(cliente=cliente)
        
        except Cliente.DoesNotExist:
            return Devolucion.objects.none()

    def create(self, request):
        """
        Crear una solicitud de devolución.
        
        Solo se puede devolver si el pedido está ENTREGADO.
        POST /api/v1/mis-devoluciones/
        """
        # 1. Verificar que es cliente
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'error': 'Usuario no es cliente'}, status=400)

        # 2. Obtener datos del request
        linea_pedido_id = request.data.get('linea_pedido')
        motivo = request.data.get('motivo')
        cantidad_devuelta = request.data.get('cantidad_devuelta')

        # 3. Validar campos requeridos
        if not linea_pedido_id:
            return Response({'error': 'Debe indicar la línea de pedido'}, status=400)
        
        if not motivo or len(motivo.strip()) < 5:
            return Response({'error': 'El motivo debe tener al menos 5 caracteres'}, status=400)
        
        if not cantidad_devuelta or int(cantidad_devuelta) < 1:
            return Response({'error': 'La cantidad a devolver debe ser al menos 1'}, status=400)

        cantidad_devuelta = int(cantidad_devuelta)

        # 4. Obtener la línea de pedido
        try:
            linea_pedido = LineaPedido.objects.get(id=linea_pedido_id)
        except LineaPedido.DoesNotExist:
            return Response({'error': 'Línea de pedido no encontrada'}, status=404)

        # 5. Verificar que el pedido pertenece al cliente
        if linea_pedido.pedido.cliente != cliente:
            return Response({'error': 'Este pedido no te pertenece'}, status=403)

        # 6. Verificar que el pedido está ENTREGADO
        if linea_pedido.pedido.estado != Pedido.ENTREGADO:
            return Response({
                'error': 'Solo puedes devolver productos de pedidos entregados',
                'estado_actual': linea_pedido.pedido.get_estado_display()
            }, status=400)

        # 7. Verificar que la línea no esté ya devuelta
        if linea_pedido.estado == LineaPedido.DEVUELTO:
            return Response({'error': 'Esta línea ya fue devuelta'}, status=400)

        # 8. Verificar cantidad válida
        # Calcular cuánto ya se devolvió de esta línea
        #Sirve para saber cuántas unidades de esa línea de pedido ya han sido devueltas (o están en proceso de devolución), 
        # y así evitar que el cliente devuelva más unidades de las que compró.
        ya_devuelto = Devolucion.objects.filter(
            linea_pedido=linea_pedido,
            estado__in=[Devolucion.PENDIENTE, Devolucion.APROBADA]
        ).aggregate(total=models.Sum('cantidad_devuelta'))['total'] or 0

        disponible_devolver = linea_pedido.cantidad - ya_devuelto

        if cantidad_devuelta > disponible_devolver:
            return Response({
                'error': f'Solo puedes devolver {disponible_devolver} unidades',
                'cantidad_en_linea': linea_pedido.cantidad,
                'ya_devuelto': ya_devuelto
            }, status=400)

        # 9. Calcular monto de reembolso
        monto_reembolso = linea_pedido.precio_unitario * cantidad_devuelta

        # 10. Crear la devolución
        devolucion = Devolucion.objects.create(
            linea_pedido=linea_pedido,
            cliente=cliente,
            fecha_solicitud=date.today(),
            motivo=motivo,
            estado=Devolucion.PENDIENTE,
            cantidad_devuelta=cantidad_devuelta,
            monto_reembolso=monto_reembolso
        )

        return Response({
            'message': 'Solicitud de devolución creada correctamente',
            'devolucion_id': devolucion.id,
            'estado': 'Pendiente de aprobación',
            'cantidad_devuelta': cantidad_devuelta,
            'monto_reembolso': str(monto_reembolso)
        }, status=201)


class DevolucionVendedorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para que los vendedores gestionen las devoluciones.
    
    GET /api/v1/devoluciones/ - Lista devoluciones de pedidos del vendedor
    POST /api/v1/devoluciones/{id}/aprobar/ - Aprobar devolución
    POST /api/v1/devoluciones/{id}/rechazar/ - Rechazar devolución
    """
    queryset = Devolucion.objects.all()
    serializer_class = DevolucionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filtra las devoluciones:
        - Admin/Empleado: ve todas
        - Vendedor: solo las de sus pedidos
        """
        user = self.request.user
        
        # Admin o Empleado ven todo
        if user.rol in [Usuario.ADMINISTRADOR, Usuario.EMPLEADO]:
            return Devolucion.objects.all()
        
        # Vendedor solo ve devoluciones de sus pedidos
        try:
            vendedor = user.vendedor
            return Devolucion.objects.filter(
                linea_pedido__pedido__vendedor=vendedor
            )
        except Vendedor.DoesNotExist:
            return Devolucion.objects.none()

    def es_vendedor_o_admin(self, request):
        """Verifica si el usuario es vendedor, admin o empleado."""
        user = request.user
        if user.rol in [Usuario.ADMINISTRADOR, Usuario.EMPLEADO]:
            return True
        try:
            vendedor = user.vendedor
            return vendedor is not None
        except Vendedor.DoesNotExist:
            return False

    @action(detail=True, methods=['post'])
    def aprobar(self, request, pk=None):
        """
        Aprobar una devolución y restaurar el stock.
        
        POST /api/v1/devoluciones/{id}/aprobar/
        """
        # Verificar que es vendedor o admin
        if not self.es_vendedor_o_admin(request):
            return Response({'error': 'Solo vendedores pueden aprobar devoluciones'}, status=403)

        try:
            devolucion = self.get_queryset().get(id=pk)
        except Devolucion.DoesNotExist:
            return Response({'error': 'Devolución no encontrada'}, status=404)

        # Verificar que está pendiente
        if devolucion.estado != Devolucion.PENDIENTE:
            return Response({
                'error': 'Solo se pueden aprobar devoluciones pendientes',
                'estado_actual': devolucion.get_estado_display()
            }, status=400)

        # Aprobar la devolución
        devolucion.estado = Devolucion.APROBADA
        devolucion.fecha_aprobacion = date.today()
        devolucion.save()

        # Restaurar stock
        pieza = devolucion.linea_pedido.pieza
        pieza.stock += devolucion.cantidad_devuelta
        pieza.save()

        # Marcar línea como devuelta si se devolvió todo
        linea = devolucion.linea_pedido
        linea.estado = LineaPedido.DEVUELTO
        linea.save()


        total_devuelto = Devolucion.objects.filter(
            linea_pedido=linea,
            estado=Devolucion.APROBADA
        ).aggregate(total=models.Sum('cantidad_devuelta'))['total'] or 0

        if total_devuelto >= linea.cantidad:
            linea.estado = LineaPedido.DEVUELTO
            linea.save()

        return Response({
            'message': 'Devolución aprobada correctamente',
            'devolucion_id': devolucion.id,
            'stock_restaurado': devolucion.cantidad_devuelta,
            'stock_actual': pieza.stock,
            'monto_reembolso': str(devolucion.monto_reembolso)
        })

    @action(detail=True, methods=['post'])
    def rechazar(self, request, pk=None):
        """
        Rechazar una devolución.
        
        POST /api/v1/devoluciones/{id}/rechazar/
        Body opcional: {"motivo_rechazo": "Razón del rechazo"}
        """
        # Verificar que es vendedor o admin
        if not self.es_vendedor_o_admin(request):
            return Response({'error': 'Solo vendedores pueden rechazar devoluciones'}, status=403)

        try:
            devolucion = self.get_queryset().get(id=pk)
        except Devolucion.DoesNotExist:
            return Response({'error': 'Devolución no encontrada'}, status=404)

        if devolucion.estado != Devolucion.PENDIENTE:
            return Response({
                'error': 'Solo se pueden rechazar devoluciones pendientes'
            }, status=400)

        devolucion.estado = Devolucion.RECHAZADA
        devolucion.save()

        return Response({
            'message': 'Devolución rechazada',
            'devolucion_id': devolucion.id
        })



    
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
#        # Obtener todas las valoraciones de la pieza de mayor a menor fecha
#        valoraciones = Valoracion.objects.filter(
#            pieza=pieza
#        ).order_by('-fecha_valoracion')
#
#        # Calcular promedio de puntuación
#        promedio = valoraciones.aggregate(
#            Avg('puntuacion')
#        )['puntuacion__avg']
#
#        # Serializar datos
#        serializer = ValoracionSerializer(
#            valoraciones,
#            many=True,
#            context={'request': request}
#        )
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
      GET /api/v1/valoracion/por_pieza/?pieza_id=1
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


    def create(self, request, *args, **kwargs):
        """
        Permite crear una valoración solo si el cliente ha comprado la pieza.
        POST /api/v1/valoracion/

        {
          "pieza": 1,
          "puntuacion": 5,
          "titulo": "Muy buena",
          "comentario": "Me gustó mucho"
        }
        """
        # Paso 1: Verificar que el usuario es un cliente
        try:
            cliente = request.user.cliente
        except Exception:
            return Response({'error': 'Solo los clientes pueden valorar piezas.'}, status=403)

        # Paso 2: Obtener el ID de la pieza desde el request
        pieza_id = request.data.get('pieza')
        if not pieza_id:
            return Response({'error': 'Debes indicar la pieza a valorar.'}, status=400)

        # Paso 3: Verificar que la pieza existe
        try:
            pieza = Pieza.objects.get(id=pieza_id)
        except Pieza.DoesNotExist:
            return Response({'error': 'La pieza no existe.'}, status=404)

        # Paso 4: Verificar que el cliente ha comprado esa pieza
        la_ha_comprado = LineaPedido.objects.filter(pedido__cliente=cliente, pieza=pieza).exists()
        if not la_ha_comprado:
            return Response({'error': 'Solo puedes valorar piezas que has comprado.'}, status=403)

        # Paso 5: Verificar si ya ha comentado esta pieza
        ya_comento = Valoracion.objects.filter(cliente=cliente, pieza=pieza).exists()
        if ya_comento:
            return Response({'error': 'Ya has comentado esta pieza.'}, status=400)

        # Paso 6: Validar los datos enviados por el usuario
        datos = request.data  # Datos del comentario enviados por el frontend
        serializer = self.get_serializer(data=datos)
        if not serializer.is_valid():
            # Si hay errores de validación, los devolvemos
            return Response(serializer.errors, status=400)

        # Guardar la valoración, asignando el cliente, la fecha y la pieza de forma segura
        nueva_valoracion = serializer.save(cliente=cliente, pieza=pieza, fecha_valoracion=date.today())
        # Paso 7: Devolver la valoración creada como respuesta
        return Response(self.get_serializer(nueva_valoracion).data, status=201)
    

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
    """
    ViewSet para gestionar la lista de deseos del cliente.
    
    Endpoints:
    - GET /api/v1/lista_deseo/mi_lista/ - Obtener mi lista de deseos
    - POST /api/v1/lista_deseo/agregar_pieza/ - Agregar pieza a la lista
    - DELETE /api/v1/lista_deseo/eliminar_pieza/ - Eliminar pieza de la lista
    - POST /api/v1/lista_deseo/pasar_al_carrito/ - Pasar items al carrito
    - POST /api/v1/lista_deseo/vaciar/ - Vaciar la lista de deseos
    """
    queryset = ListaDeseos.objects.all()
    serializer_class = ListaDeseosSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción."""
        if self.action == 'agregar_pieza':
            return AgregarPiezaListaDeseosSerializer
        elif self.action == 'eliminar_pieza':
            return EliminarPiezaListaDeseosSerializer
        elif self.action == 'pasar_al_carrito':
            return PasarAlCarritoSerializer
        return ListaDeseosSerializer

    def get_queryset(self):
        """Solo muestra la lista de deseos del cliente autenticado."""
        try:
            cliente = self.request.user.cliente
            return ListaDeseos.objects.filter(cliente=cliente)
        except Cliente.DoesNotExist:
            return ListaDeseos.objects.none()

    def get_o_crear_lista(self, cliente):
        """Obtiene o crea la lista de deseos del cliente."""
        lista, created = ListaDeseos.objects.get_or_create(
            cliente=cliente,
            defaults={
                'nombre': f'Lista de deseos de {cliente.usuario.first_name}',
                'fecha_creacion': date.today()
            }
        )
        return lista

    @action(detail=False, methods=['get'])
    def mi_lista(self, request):
        """
        Obtiene la lista de deseos del usuario autenticado.
        
        GET /api/v1/lista_deseo/mi_lista/
        """
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'error': 'Usuario no es cliente'}, status=400)

        lista = self.get_o_crear_lista(cliente)
        
        # Obtener los items con información de las piezas
        items = []
        for item in lista.items.all():
            pieza = item.pieza
            imagen_principal = None
            
            # Buscar imagen principal
            imagen_obj = ImagenPieza.objects.filter(pieza=pieza).first()
            if imagen_obj and imagen_obj.url_imagen:
                imagen_principal = request.build_absolute_uri(imagen_obj.url_imagen.url)
            elif pieza.imagen:
                imagen_principal = request.build_absolute_uri(pieza.imagen.url)
            
            items.append({
                'id': item.id,
                'pieza_id': pieza.id,
                'nombre': pieza.nombre,
                'marca': pieza.marca,
                'precio': str(pieza.precio_base),
                'imagen': imagen_principal,
                'stock': pieza.stock,
                'fecha_agregado': item.fecha_agregado,
                'disponible': pieza.stock > 0
            })
        
        return Response({
            'lista_id': lista.id,
            'nombre': lista.nombre,
            'fecha_creacion': lista.fecha_creacion,
            'total_items': len(items),
            'items': items
        })

    @action(detail=False, methods=['post'])
    def agregar_pieza(self, request):
        """
        Agrega una pieza a la lista de deseos.
        
        POST /api/v1/lista_deseo/agregar_pieza/
        {
            "pieza_id": 1
        }
        """
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'error': 'Usuario no es cliente'}, status=400)

        pieza_id = request.data.get('pieza_id')
        if not pieza_id:
            return Response({'error': 'Debe indicar el ID de la pieza'}, status=400)

        try:
            pieza = Pieza.objects.get(id=pieza_id)
        except Pieza.DoesNotExist:
            return Response({'error': 'Pieza no encontrada'}, status=404)

        lista = self.get_o_crear_lista(cliente)

        # Verificar si ya está en la lista
        if ListaDeseosPieza.objects.filter(lista_deseos=lista, pieza=pieza).exists():
            return Response({
                'error': 'Esta pieza ya está en tu lista de deseos',
                'ya_existe': True
            }, status=400)

        # Agregar a la lista
        item = ListaDeseosPieza.objects.create(
            lista_deseos=lista,
            pieza=pieza,
            fecha_agregado=date.today()
        )

        return Response({
            'message': 'Pieza agregada a la lista de deseos',
            'item_id': item.id,
            'pieza_nombre': pieza.nombre
        }, status=201)


    @action(detail=False, methods=['delete', 'post'])
    def eliminar_pieza(self, request):
        """
        Elimina una pieza de la lista de deseos.
        
        DELETE /api/v1/lista_deseo/eliminar_pieza/
        {
            "pieza_id": 1
        }
        Esta implementación elimina todos los registros coincidentes, por si acaso hay duplicados.
        """
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'error': 'Usuario no es cliente'}, status=400)

        pieza_id = request.data.get('pieza_id')
        if not pieza_id:
            return Response({'error': 'Debe indicar el ID de la pieza'}, status=400)

        try:
            lista = ListaDeseos.objects.get(cliente=cliente)
        except ListaDeseos.DoesNotExist:
            return Response({'error': 'No tienes una lista de deseos'}, status=404)

        items = ListaDeseosPieza.objects.filter(lista_deseos=lista, pieza_id=pieza_id)
        if items.exists():
            nombre_pieza = items.first().pieza.nombre
            items.delete()
            return Response({
                'message': f'"{nombre_pieza}" eliminada de la lista de deseos'
            })
        else:
            return Response({'error': 'Esta pieza no está en tu lista de deseos'}, status=404)

    @action(detail=False, methods=['post'])
    def pasar_al_carrito(self, request):
        """
        Pasa los items de la lista de deseos al carrito.
        Puede pasar todos los items o solo algunos específicos.
        
        POST /api/v1/lista_deseo/pasar_al_carrito/
        
        Body (opcional):
        {
            "piezas_ids": [1, 2, 3],  // Si no se envía, pasa todas las piezas
            "eliminar_de_lista": true  // Si es true, elimina las piezas pasadas de la lista
        }
        """
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'error': 'Usuario no es cliente'}, status=400)

        try:
            lista = ListaDeseos.objects.get(cliente=cliente)
        except ListaDeseos.DoesNotExist:
            return Response({'error': 'No tienes una lista de deseos'}, status=404)

        # Obtener parámetros
        piezas_ids = request.data.get('piezas_ids', None)
        eliminar_de_lista = request.data.get('eliminar_de_lista', False)

        # Obtener items a pasar
        if piezas_ids:
            items = ListaDeseosPieza.objects.filter(
                lista_deseos=lista,
                pieza_id__in=piezas_ids
            )
        else:
            items = lista.items.all()

        if not items.exists():
            return Response({'error': 'No hay piezas para agregar al carrito'}, status=400)

        # Obtener carrito actual de la sesión
        carrito = request.session.get('carrito', {})
        
        piezas_agregadas = []
        piezas_sin_stock = []
        piezas_ya_en_carrito = []

        for item in items:
            pieza = item.pieza
            pieza_id = str(pieza.id)

            # Verificar stock
            if pieza.stock <= 0:
                piezas_sin_stock.append(pieza.nombre)
                continue

            # Verificar si ya está en el carrito
            if pieza_id in carrito:
                # Incrementar cantidad si hay stock
                cantidad_actual = carrito[pieza_id]['cantidad']
                if cantidad_actual < pieza.stock:
                    carrito[pieza_id]['cantidad'] += 1
                    piezas_agregadas.append(pieza.nombre)
                else:
                    piezas_ya_en_carrito.append(pieza.nombre)
            else:
                # Agregar al carrito con cantidad 1
                carrito[pieza_id] = {'cantidad': 1}
                piezas_agregadas.append(pieza.nombre)

        # Guardar carrito en sesión
        request.session['carrito'] = carrito
        request.session.modified = True

        # Eliminar de la lista si se solicitó
        items_eliminados = []
        if eliminar_de_lista and piezas_agregadas:
            for item in items:
                if item.pieza.nombre in piezas_agregadas:
                    items_eliminados.append(item.pieza.nombre)
                    item.delete()

        return Response({
            'message': 'Items procesados correctamente',
            'agregadas_al_carrito': piezas_agregadas,
            'sin_stock': piezas_sin_stock,
            'ya_en_carrito_max_stock': piezas_ya_en_carrito,
            'eliminadas_de_lista': items_eliminados,
            'total_en_carrito': len(carrito)
        })

    @action(detail=False, methods=['post'])
    def vaciar(self, request):
        """
        Vacía completamente la lista de deseos.
        
        POST /api/v1/lista_deseo/vaciar/
        """
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'error': 'Usuario no es cliente'}, status=400)

        try:
            lista = ListaDeseos.objects.get(cliente=cliente)
            cantidad = lista.items.count()
            lista.items.all().delete()
            return Response({
                'message': f'Lista de deseos vaciada ({cantidad} items eliminados)'
            })
        except ListaDeseos.DoesNotExist:
            return Response({'error': 'No tienes una lista de deseos'}, status=404)

    @action(detail=False, methods=['get'])
    def verificar_pieza(self, request):
        """
        Verifica si una pieza está en la lista de deseos.
        
        GET /api/v1/lista_deseo/verificar_pieza/?pieza_id=1
        """
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'en_lista': False})

        pieza_id = request.query_params.get('pieza_id')
        if not pieza_id:
            return Response({'error': 'Debe indicar el ID de la pieza'}, status=400)

        try:
            lista = ListaDeseos.objects.get(cliente=cliente)
            en_lista = ListaDeseosPieza.objects.filter(
                lista_deseos=lista,
                pieza_id=pieza_id
            ).exists()
            return Response({'en_lista': en_lista, 'pieza_id': int(pieza_id)})
        except ListaDeseos.DoesNotExist:
            return Response({'en_lista': False, 'pieza_id': int(pieza_id)})


class ListaDeseosPiezaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar items individuales de la lista de deseos.
    Principalmente para operaciones CRUD básicas.
    """
    queryset = ListaDeseosPieza.objects.all()
    serializer_class = ListaDeseosPiezaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Solo muestra los items de la lista del cliente autenticado."""
        try:
            cliente = self.request.user.cliente
            return ListaDeseosPieza.objects.filter(lista_deseos__cliente=cliente)
        except Cliente.DoesNotExist:
            return ListaDeseosPieza.objects.none()

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


    # def perform_create(self, serializer):
    #     cliente = serializer.save()
    #     try:
    #         descuento = Descuento.objects.get(codigo="A524844", estado=Descuento.ACTIVO)
    #         ClienteDescuento.objects.create(
    #             cliente=cliente,
    #             descuento=descuento,
    #             fecha_asignado=date.today(),
    #             veces_usado=0
    #         )
    #     except Descuento.DoesNotExist:
    #         pass



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
            
            # 4. Verificar si tiene lista de deseos con items
            lista_deseos_info = None
            try:
                cliente = user.cliente
                lista = ListaDeseos.objects.filter(cliente=cliente).first()
                if lista and lista.items.exists():
                    lista_deseos_info = {
                        'tiene_items': True,
                        'total_items': lista.items.count(),
                        'mensaje': f'Tienes {lista.items.count()} artículo(s) en tu lista de deseos'
                    }
            except Cliente.DoesNotExist:
                pass
            
            response_data = {
                "message": "Sesión iniciada correctamente",
                "is_authenticated": True,
            }
            
            # Agregar info de lista de deseos si existe
            if lista_deseos_info:
                response_data['lista_deseos'] = lista_deseos_info
            
            return Response(response_data, status=status.HTTP_200_OK)
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


    def list(self, request):
        """Devuelve el contenido actual del carrito, mostrando 
        información de cada pieza (nombre, imagen, precio, cantidad, 
        etc.) y el precio total.

        Agregar pieza al carrito:
        {
            "pieza_id": 7,
            "cantidad": 3
        }


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
                    #convertir la URL relativa de la imagen en una URL completa
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
        Método para finalizar la compra del carrito actual.

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
#Para comprobar si el usuario ha iniciado sesión basado en las cookies de sesión
@require_http_methods(["GET"])
def auth_status(request):
    """Verifica si el usuario está autenticado basado en las cookies de sesión."""
    if request.user.is_authenticated:
        return JsonResponse({
            'is_authenticated': request.user.is_authenticated})
    
    return JsonResponse({'is_authenticated': False}, status=403)


# ================= DASHBOARD VENDEDOR =====================
class DashboardVendedorView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            vendedor = Vendedor.objects.get(usuario=user)
        except Vendedor.DoesNotExist:
            return Response({"error": "No eres un vendedor válido."}, status=403)

        hoy = date.today()
        ayer = hoy - timedelta(days=1)
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        inicio_semana_pasada = inicio_semana - timedelta(days=7)
        fin_semana_pasada = inicio_semana - timedelta(days=1)

        # Ventas hoy y ayer
        #Busca los pedidos del vendedor, que sea fecha hoy y que estén en estado PAGADO, ENVIADO o ENTREGADO
        #Luego suma el total de esos pedidos y guarda en diccionario con la clave 'total'
        #Sino hay ventas, devuelve NONE, por eso el "or 0" al final
        ventas_hoy = Pedido.objects.filter(vendedor=vendedor, fecha_pedido=hoy, estado__in=
                                           [Pedido.PAGADO, Pedido.ENVIADO, Pedido.ENTREGADO]
                                           ).aggregate(total=Sum('total'))['total'] or 0
        
        #Misma lógica pero para ayer
        ventas_ayer = Pedido.objects.filter(vendedor=vendedor, fecha_pedido=ayer, estado__in=
                                            [Pedido.PAGADO, Pedido.ENVIADO, Pedido.ENTREGADO]
                                            ).aggregate(total=Sum('total'))['total'] or 0
        
        porcentaje_vs_ayer = 0
        
        #para evitar división por cero
        if ventas_ayer > 0:
            #ventas_hoy - ventas_ayer: diferencia de ventas entre hoy y ayer.
            #/ ventas_ayer: lo divide entre las ventas de ayer para saber cuánto ha cambiado en proporción.
            #* 100: lo convierte a porcentaje.
            #round(..., 2): redondea el resultado a 2 decimales.
            porcentaje_vs_ayer = round(((ventas_hoy - ventas_ayer) / ventas_ayer) * 100, 2)

        # Pedidos pendientes
        pedidos_pendientes = Pedido.objects.filter(vendedor=vendedor, estado=Pedido.PENDIENTE).count()

        # Producto más vendido (activo)
        #Consulta en la base de datos todas las líneas de pedido (LineaPedido) que pertenecen a pedidos de ese vendedor específico.
        #Agrupa los resultados por el ID y el nombre de la pieza (pieza__id, pieza__nombre).
        #Para cada grupo (cada pieza), suma la cantidad total vendida de esa pieza usando .annotate(total_vendido=Sum('cantidad')).
        #Ordena los resultados de mayor a menor según la cantidad total vendida (order_by('-total_vendido')).
        #Toma el primer resultado con .first(), que será la pieza más vendida.
        producto_mas_vendido = (
            LineaPedido.objects.filter(pedido__vendedor=vendedor)
            .values('pieza__id', 'pieza__nombre')
            .annotate(total_vendido=Sum('cantidad'))
            .order_by('-total_vendido')
            .first()
        )

        #Si existe algún resultado, extrae el nombre de la pieza más vendida (producto_activo) 
        # y la cantidad total vendida (producto_activo_cantidad). Si no hay resultados, ambos serán None o 0.
        producto_activo = producto_mas_vendido['pieza__nombre'] if producto_mas_vendido else None #Nombre del pieza más vendido
        producto_activo_cantidad = producto_mas_vendido['total_vendido'] if producto_mas_vendido else 0 #Cantidad vendida

        # Valoración promedio de productos del vendedor
        #Busca los IDs de todas las piezas que han sido vendidas por el vendedor (es decir, piezas que aparecen en alguna línea de pedido de un pedido de ese vendedor). El resultado es una lista de IDs únicos de piezas.
        #Con esa lista de IDs, busca todas las valoraciones (comentarios/puntuaciones) que existen para esas piezas.
        piezas_ids = Pieza.objects.filter(lineas_pedido__pedido__vendedor=vendedor).values_list('id', flat=True).distinct()

        #Calcula el promedio de la puntuación de todas esas valoraciones usando Avg('puntuacion').
        valoracion_promedio = Valoracion.objects.filter(pieza_id__in=piezas_ids).aggregate(avg=Avg('puntuacion'))['avg']
        
        #Si hay valoraciones, redondea el promedio a 2 decimales.
        if valoracion_promedio is not None:
            valoracion_promedio = round(valoracion_promedio, 2)

        # Ventas esta semana y semana anterior
        #Filtra los pedidos de ese vendedor cuya fecha está entre el inicio de la semana (lunes) y hoy, y cuyo estado es PAGADO, ENVIADO o ENTREGADO.
        #Suma el campo total de esos pedidos con aggregate(total=Sum('total')).
        #Si no hay ventas, devuelve 0.
        ventas_semana = Pedido.objects.filter(vendedor=vendedor, 
                                              fecha_pedido__gte=inicio_semana, fecha_pedido__lte=hoy, estado__in=[
                                                  Pedido.PAGADO, Pedido.ENVIADO, Pedido.ENTREGADO]).aggregate(total=Sum('total'))['total'] or 0
        
        #Filtra los pedidos del vendedor cuya fecha está entre el inicio y el fin de la semana pasada (de lunes a domingo de la semana anterior).
        #misma lógica pero para la semana pasada
        ventas_semana_pasada = Pedido.objects.filter(vendedor=vendedor, fecha_pedido__gte=inicio_semana_pasada, fecha_pedido__lte=fin_semana_pasada, 
                                                     estado__in=[Pedido.PAGADO, Pedido.ENVIADO, Pedido.ENTREGADO]).aggregate(total=Sum('total'))['total'] or 0
        
        porcentaje_vs_semana_pasada = 0
        
        #Indicador rápido para saber si vendiste más, menos o igual que la semana anterior.
        if ventas_semana_pasada > 0:
            porcentaje_vs_semana_pasada = round(((ventas_semana - ventas_semana_pasada) / ventas_semana_pasada) * 100, 2)

        # Cliente más frecuente
        #Filtra todos los pedidos de ese vendedor.
        #Agrupa los pedidos por cliente (usando el ID y el nombre del cliente).
        #Cuenta cuántos pedidos ha hecho cada cliente con annotate(num_pedidos=Count('id')).
        #Ordena los resultados de mayor a menor según el número de pedidos realizados.
        #Toma el primer resultado con .first(), que será el cliente que ha hecho más
        cliente_frecuente = (
            Pedido.objects.filter(vendedor=vendedor)
            .values('cliente__id', 'cliente__usuario__first_name', 'cliente__usuario__last_name')
            .annotate(num_pedidos=Count('id'))
            .order_by('-num_pedidos')
            .first()
        )

        cliente_frecuente_nombre = None #Almacena en un diccionario
        cliente_frecuente_pedidos = 0

        if cliente_frecuente:
            #Obtiene nombre y apellido del cliente más frecuente 
            cliente_frecuente_nombre = f"{cliente_frecuente['cliente__usuario__first_name']} {cliente_frecuente['cliente__usuario__last_name']}"
            
            #Obtiene número de pedidos realizados por el cliente más frecuente
            cliente_frecuente_pedidos = cliente_frecuente['num_pedidos']

        
        # Últimas transacciones (últimos 5 pedidos)
        #Busca todos los pedidos hechos al vendedor actual.
        # trae junto con cada pedido, los datos del cliente y del usuario (nombre, apellido) en una sola consulta a la base de datos
        #Ordena los pedidos por fecha de pedido en orden descendente (los más recientes primero).
        #Limita los resultados a los 5 pedidos más recientes.
        ultimos_pedidos = (
            Pedido.objects.filter(vendedor=vendedor)
            .select_related('cliente__usuario')
            .order_by('-fecha_pedido')[:5]
        )

        #
        ultimas_transacciones = []

        for pedido in ultimos_pedidos:
            # Obtener nombre completo del cliente
            nombre_cliente = pedido.cliente.usuario.first_name
            apellido_cliente = pedido.cliente.usuario.last_name
            nombre_completo = f"{nombre_cliente} {apellido_cliente}"

            # Obtener monto total del pedido
            monto = float(pedido.total)

            # Obtener estado legible del pedido
            estado = pedido.get_estado_display()

            # Obtener fecha del pedido
            fecha = pedido.fecha_pedido

            # Crear diccionario resumen
            resumen = {
                'cliente': nombre_completo,
                'monto': monto,
                'estado': estado,
                'fecha': fecha
            }
            ultimas_transacciones.append(resumen)

        return Response({
            'ventas_hoy': float(ventas_hoy),
            'porcentaje_vs_ayer': porcentaje_vs_ayer,
            'pedidos_pendientes': pedidos_pendientes,
            'producto_activo': producto_activo,
            'producto_activo_cantidad': producto_activo_cantidad,
            'valoracion_promedio': valoracion_promedio,
            'ventas_semana': float(ventas_semana),
            'porcentaje_vs_semana_pasada': porcentaje_vs_semana_pasada,
            'cliente_frecuente': cliente_frecuente_nombre,
            'cliente_frecuente_pedidos': cliente_frecuente_pedidos,
            'ultimas_transacciones': ultimas_transacciones
        })