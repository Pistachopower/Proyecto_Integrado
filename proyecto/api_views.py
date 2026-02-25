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
from django.conf import settings
import paypalrestsdk
from dotenv import load_dotenv
import os
import requests



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
    @action(detail=False, methods=['get'])
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

#Factura cliente
from django.http import HttpResponse
from reportlab.pdfgen import canvas
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader

class PedidoViewSet(viewsets.ModelViewSet):
    """
    PATCH /api/v1/pedido/{id}/cambiar_estado_vendedor/
    Body: {"estado": 2}
    
    GET /api/v1/pedido/{id}/factura_cliente/
    """
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated]

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

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def filtrar_pedidosCliente(self, request):
        """
        Filtra pedidos por id, estado (uno o varios), fecha.
        GET /api/v1/pedido/filtrar_pedidosCliente/?id=1
        GET /api/v1/pedido/filtrar_pedidosCliente/?estado=pendiente
        GET /api/v1/pedido/filtrar_pedidosCliente/?fecha=2026-02-19
        """
        pedidos = Pedido.objects.all()

        pedido_id = request.query_params.get('id')
        estados = request.query_params.getlist('estado')
        fecha = request.query_params.get('fecha')

        if pedido_id:
            pedidos = pedidos.filter(id=pedido_id)
        if estados:
            pedidos = pedidos.filter(estado__in=estados)
        if fecha:
            pedidos = pedidos.filter(fecha_pedido__date=fecha)

        # Ordenar siempre por fecha_pedido, id y estado de forma ascendente
        pedidos = pedidos.order_by('id')


        serializer = PedidoSerializer(pedidos, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def filtrar_pedidosVendedor(self, request):
        """
        Filtra pedidos por vendedor, id, nombre del cliente, monto y fecha.
        GET /api/v1/pedido/filtrar_pedidosVendedor/?vendedor_id=1&id=1&nombre_cliente=Juan&monto=100.00&fecha=2026-02-19
        """
        pedidos = Pedido.objects.all()
        pedido_id = request.query_params.get('id')
        nombre_cliente = request.query_params.get('nombre_cliente')
        monto = request.query_params.get('monto')
        fecha = request.query_params.get('fecha')

        if pedido_id:
            pedidos = pedidos.filter(id=pedido_id)
        if nombre_cliente:
            pedidos = pedidos.filter(cliente__usuario__first_name__icontains=nombre_cliente)
            #piezas = piezas.filter(nombre__icontains=busqueda)
        if monto:
            pedidos = pedidos.filter(total=monto)
        if fecha:
            pedidos = pedidos.filter(fecha_pedido=fecha)

        pedidos = pedidos.order_by('id')
        
        serializer = PedidoSimpleSerializer(pedidos, many=True, context={'request': request})
        return Response(serializer.data)



    @action(detail=True, methods=['get'])
    def factura_cliente(self, request, pk=None):
        """
        Genera y descarga una factura PDF profesional para el pedido.

        GET /api/v1/pedido/{id}/factura_cliente/
        """
        #Obtenemos el id del pedido. Obtiene el objeto pedido
        pedido = self.get_object()

        if pedido.estado not in [Pedido.PAGADO, Pedido.ENVIADO, Pedido.ENTREGADO]:
            return Response({'error': 'La factura solo está disponible para pedidos pagados.'}, status=403)

        #Crea objeto HttpResponse con el tipo de contenido PDF y el nombre del archivo
        response = HttpResponse(content_type='application/pdf')

        # configura la cabecera HTTP Content-Disposition de la respuesta para indicar al navegador que el contenido debe descargarse como un archivo adjunto
        response['Content-Disposition'] = f'attachment; filename="factura_pedido_{pedido.id}.pdf"'
        
        #Aquí se crea un objeto canvas de ReportLab, que permite dibujar y generar el contenido del PDF. 
        # Se le indica que el PDF se escribirá directamente en la respuesta HTTP (response) y que el 
        # tamaño de la página será A4
        p = canvas.Canvas(response, pagesize=A4)
        
        #Definimos el tamaño de la página en formato A4
        width, height = A4

        #Hacemos el cálculo con la constante mm 
        #30 × 2.83465= 85.04 puntos: definir el margen a la izquierda
        margen_izq = 30 * mm

        #30 × 2.83465= 85.04 puntos: definir el margen superior
        margen_sup = height - 30 * mm

        #establece la posición vertical inicial (coordenada Y) desde donde se empezará a dibujar 
        # el contenido en el PDF.
        y = margen_sup

        # --- Cabecera: Logo y datos empresa ---

        #Obtenemos la ruta absoluta del logo de la empresa. /home/nelson/Documentos/Proyecto_Integrado/media/logo.png
        logo_path = os.path.join(settings.BASE_DIR, 'media/logo.png')
        
        #ImageReader abre el archivo de imagen directamente desde el disco y lo convierte en un objeto que ReportLab puede usar para dibujar la imagen en el PDF
        logo = ImageReader(logo_path)
        
        #logo: es el objeto de imagen cargado previamente (con ImageReader).
        #margen_izq: posición X (horizontal) donde empieza la imagen (margen izquierdo).
        #y-10*mm: posición Y (vertical) desde arriba, bajando 10 mm desde la coordenada y.
        #width=40*mm: ancho de la imagen (40 milímetros).
        #height=20*mm: alto de la imagen (20 milímetros).
        #mask='auto': hace transparente el fondo blanco de la imagen si es posible.
        p.drawImage(logo, margen_izq, y-10*mm, width=40*mm, height=20*mm, mask='auto')
        

        # Datos empresa
        #Esto posiciona el texto de la empresa (nombre, dirección, etc.) a la derecha del logo, 
        # dejando un espacio de 50 mm desde el margen izquierdo. Así, el texto no se superpone 
        # con el logo y queda alineado de forma profesional en la cabecera del PDF.
        empresa_x = margen_izq + 50*mm

        #Configuracion de tipo de letra y tamaño 
        p.setFont("Helvetica-Bold", 12)

        #Pinta nombre empresa con las medidas definidas en empresa_x y y.
        p.drawString(empresa_x, y, "Motor Part Express S.L.")
        
        #Cambiamos el tamaño y tipo de letra para los datos adicionales de la empresa
        p.setFont("Helvetica", 9)
        p.drawString(empresa_x, y-12, "CIF: B12345678")
        p.drawString(empresa_x, y-24, "Calle Ejemplo 123, 41000 Sevilla")
        p.drawString(empresa_x, y-36, "Tel: 954 000 000 | info@miempresa.com")

        #Bajamos la coordenada Y para dejar espacio entre la cabecera y el resto del contenido
        y -= 45
        
        # Línea separadora
        #Dibuja linea en gris debajo de la cabecera para separar visualmente la información de la empresa del resto del contenido.
        p.setStrokeColor(colors.grey)
        p.setLineWidth(0.9)
        p.line(margen_izq, y, width-margen_izq, y)
        y -= 15

        # # --- Datos de la factura y cliente ---
        p.setFont("Helvetica-Bold", 14)
        p.drawString(margen_izq, y, f"Número de Pedido: {pedido.id}")
        p.setFont("Helvetica", 10)
        p.drawRightString(width - margen_izq, y, f"Fecha del pedido: {pedido.fecha_pedido}")
        y -= 18
        p.drawString(margen_izq, y, f"Cliente: {pedido.cliente.usuario.first_name} {pedido.cliente.usuario.last_name}")
        y -= 15
        p.drawString(margen_izq, y, f"Email: {pedido.cliente.usuario.email}")
        y -= 15
        p.drawString(margen_izq, y, f"Dirección: {pedido.direccion_envio}")
        y -= 32

        # # --- Tabla de líneas de pedido ---
        #Definimos la cabecera de la tabla de productos para la factura PDF.
        data = [["Producto", "Cantidad", "Precio Unitario", "Subtotal"]]

        #Con la relacion inversa de lineas_pedido a pedido, obtenemos todas las líneas de pedido asociadas al pedido actual y las recorremos para añadirlas a la tabla.
        for linea in pedido.lineas_pedido.all():
            data.append([
                str(linea.pieza.nombre),
                str(linea.cantidad),
                f"{linea.precio_unitario:.2f} €", #Formateamos el precio unitario con dos decimales y el símbolo de euro
                f"{linea.subtotal:.2f} €"
            ])
        # # Añadir total
        data.append(["", "", "TOTAL:", f"{pedido.total:.2f} €"])

        #Estilo de la tabla para la factura PDF. Define colores, alineación, fuentes, bordes, etc. para que la tabla tenga un aspecto profesional y sea fácil de leer.
        table = Table(data, colWidths=[70*mm, 30*mm, 35*mm, 35*mm])
        style = TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (1,1), (-1,-1), 'CENTER'),
            ('ALIGN', (2,1), (3,-2), 'RIGHT'),
            ('ALIGN', (2,-1), (3,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-2), 0.5, colors.grey),
            ('BOX', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,-1), (-1,-1), colors.whitesmoke),
            ('FONTNAME', (2,-1), (2,-1), 'Helvetica-Bold'),
            ('FONTNAME', (3,-1), (3,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (2,-1), (3,-1), 11),
        ])
        table.setStyle(style)
        table.wrapOn(p, width, height)

        #Pintamos los datos de la tabla en el PDF, comenzando desde la posición definida por
        #  margen_izq y y-15*len(data) para dejar espacio entre las filas. Luego actualizamos 
        # la coordenada Y para dejar espacio debajo de la tabla.
        table.drawOn(p, margen_izq, y-15*len(data))
        y -= 15*len(data) + 40

        # # --- Pie de página ---
        p.setFont("Helvetica-Oblique", 9)
        p.setFillColor(colors.black)
        p.drawString(margen_izq, 30, "Gracias por su compra. Para cualquier consulta, contacte con nosotros.")
        p.setFillColor(colors.black)

        #Finalizamos el PDF
        p.showPage()
        
        #Guarda el PDF para que se pueda descargar o enviar en la respuesta HTTP
        p.save()
        return response









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
            #Obtenemos la devolución por su ID (pk) para aprobarla. Si no existe, se devuelve un error 404.
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
        
        serializer = self.get_serializer(data=datos) #self.get_serializer() devuelve una instancia de ValoracionSerialize
        
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

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def pendientes(self, request):
        """
        Lista todas las valoraciones pendientes de aprobación (aprobado=False).
        Solo accesible para empleados o administradores.

        GET /api/v1/valoracion/pendientes/
        """
        #Obtenemos el usuario autenticado
        usuario = request.user

        #Definimos los roles permitidos para acceder a este endpoint
        roles_permitidos = [Usuario.EMPLEADO, Usuario.ADMINISTRADOR]

        #Verificamos si el usuario tiene un rol permitido
        # Usamos getattr para evitar errores si el atributo no existe
        if not getattr(usuario, 'rol', None) in roles_permitidos:
            return Response({'error': 'No tienes permisos para ver valoraciones pendientes.'}, status=403)

        #Obtenemos todas las valoraciones pendientes de aprobación, ordenadas por fecha descendente
        valoraciones = Valoracion.objects.filter(aprobado=False).order_by('-fecha_valoracion')

        valoraciones_data = []  # Lista donde guardaremos cada valoración con su imagen

        #Recorremos cada valoración pendiente
        for valoracion in valoraciones:
            pieza = valoracion.pieza  # Obtener la pieza asociada a la valoración

            # 6. Buscar la imagen principal de la pieza
            imagen_principal = None
            imagen_obj = ImagenPieza.objects.filter(pieza=pieza).first()  # Buscar imagen en ImagenPieza
            
            # Simplificado: Si imagen_obj existe y tiene url_imagen, usarla
            if imagen_obj and getattr(imagen_obj, 'url_imagen', None):
                # Si existe una imagen en ImagenPieza, uso esa
                imagen_principal = request.build_absolute_uri(imagen_obj.url_imagen.url)
            


            #Serializar la valoración y agregar la URL de la imagen
            valoracion_serializada = ValoracionSerializer(valoracion, context={'request': request}).data
            
            valoracion_serializada['imagen_pieza'] = imagen_principal  # Añado campo imagen_pieza
            
            valoraciones_data.append(valoracion_serializada)

        #Calculamos el total de valoraciones pendientes
        total_pendientes = valoraciones.count()

        #Construimos la respuesta final
        respuesta = {
            'total_pendientes': total_pendientes,
            'valoraciones': valoraciones_data
        }

        #Devolvemos la respuesta al frontend
        return Response(respuesta)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def aprobar(self, request, pk=None):
        """
        Aprueba una valoración (aprobado=True).
        Solo accesible para empleados o administradores.

        POST /api/v1/valoracion/{id}/aprobar/
        """
        usuario = request.user
        roles_permitidos = [Usuario.EMPLEADO, Usuario.ADMINISTRADOR]
        # Usar getattr para obtener el rol de forma segura
        if not getattr(usuario, 'rol', None) in roles_permitidos:
            return Response({'error': 'No tienes permisos para aprobar valoraciones.'}, status=403)

        valoracion = self.get_object()
        valoracion.aprobado = True
        valoracion.save()

        mensaje = 'Valoración aprobada correctamente.'
        respuesta = {'mensaje': mensaje, 'valoracion_id': valoracion.id, 'aprobado': valoracion.aprobado}
        return Response(respuesta)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def rechazar(self, request, pk=None):
        """
        Rechaza (elimina) una valoración pendiente.
        Solo accesible para empleados o administradores.

        POST /api/v1/valoracion/{id}/rechazar/
        """
        usuario = request.user
        roles_permitidos = [Usuario.EMPLEADO, Usuario.ADMINISTRADOR]
        
        if not getattr(usuario, 'rol', None) in roles_permitidos:
            return Response({'error': 'No tienes permisos para rechazar valoraciones.'}, status=403)

        valoracion = self.get_object()
        valoracion_id = valoracion.id
        valoracion.delete()

        mensaje = 'Valoración rechazada y eliminada correctamente.'
        respuesta = {'mensaje': mensaje, 'valoracion_id': valoracion_id}
        return Response(respuesta)

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
    """
    Endpoint de login personalizado que devuelve tokens JWT.
    
    POST /api/v1/login/
    {
        "username": "usuario",
        "password": "contraseña"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # 1. Recogemos usuario y contraseña
        username = request.data.get('username')
        password = request.data.get('password')

        # 2. Django verifica si existen
        #Busca user en bd, compara password hasheada, retorna objeto user o None
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # 3. Generar tokens JWT
            #Se renueva el token cada vez que se loguea
            refresh = RefreshToken.for_user(user)
            
            response_data = {
                "message": "Sesión iniciada correctamente",
                "is_authenticated": True,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "rol": user.rol,
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Credenciales inválidas"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )




class LogoutSessionView(APIView):
    """
    Endpoint de logout que invalida el refresh token JWT.
    
    POST /api/v1/logout/
    {
        "refresh": "TU_REFRESH_TOKEN"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {"error": "Debe proporcionar el refresh token"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Blacklist del token para invalidarlo
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {"message": "Sesión cerrada correctamente"}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": "Token inválido o ya expirado"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    


# ===================== CARRITO CON PEDIDO Y LINEA PEDIDO =====================
class CarritoViewSet(ViewSet):
    """
    ViewSet para gestionar el carrito del cliente usando Pedido con estado CARRITO.
    
    Endpoints:
    - GET /api/v1/carrito/ - Ver carrito actual
    - POST /api/v1/carrito/ - Agregar pieza al carrito
    - DELETE /api/v1/carrito/{pieza_id}/ - Eliminar pieza del carrito
    - POST /api/v1/carrito/finalizar/ - Finalizar compra
    - POST /api/v1/carrito/vaciar/ - Vaciar carrito
    - PATCH /api/v1/carrito/{pieza_id}/ - Actualizar cantidad de una pieza
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_carrito(self, cliente):
        """
        Obtiene o crea el Pedido con estado CARRITO para el cliente.
        """
        pedido, created = Pedido.objects.get_or_create(
            cliente=cliente,
            estado=Pedido.CARRITO,
            defaults={
                'vendedor': Vendedor.objects.first(),
                'fecha_pedido': date.today(),
                'direccion_envio': cliente.usuario.direccion or '',
                'total': Decimal('0.00')
            }
        )
        return pedido

    def calcular_total(self, pedido):
        """Recalcula el total del pedido sumando las líneas y aplica 
        descuento de bienvenida si corresponde."""

        # total = pedido.lineas_pedido.aggregate(
        #     total=Sum('subtotal')
        # )['total'] or Decimal('0.00')
        # pedido.total = total
        # pedido.save()
        # return total

        # Suma todos los subtotales de las líneas de pedido
        subtotales = pedido.lineas_pedido.aggregate(total=Sum('subtotal')) #
        suma_subtotales = subtotales['total']
        
        if suma_subtotales is None:
            total = Decimal('0.00')
        else:
            total = suma_subtotales

        cliente = pedido.cliente
        pedidos_previos = cliente.pedidos_cliente.exclude(id=pedido.id).exclude(estado=pedido.CARRITO)
        es_primer_pedido = not pedidos_previos.exists()
    
        descuento = Decimal('0.00')
        if es_primer_pedido:
            # Buscar el descuento de bienvenida activo
            descuento_obj = Descuento.objects.filter(nombre__icontains="Bienvenida", estado=Descuento.ACTIVO).first()
            if descuento_obj:
                if descuento_obj.tipo == Descuento.PORCENTAJE:
                    descuento = total * (descuento_obj.valor / Decimal('100'))
                
                elif descuento_obj.tipo == Descuento.FIJO:
                    descuento = descuento_obj.valor
                # Controla que el descuento no sea mayor al total
                descuento = min(descuento, total)
                total -= descuento

        pedido.total = total
        pedido.save()
        return total


    def list(self, request):
        """
        Devuelve el contenido actual del carrito.
        
        GET /api/v1/carrito/
        """
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'error': 'Usuario no es cliente'}, status=400)

        pedido = self.get_carrito(cliente)
        items = []
        
        for linea in pedido.lineas_pedido.all():
            pieza = linea.pieza
            imagen_principal = None
            
            # Buscar imagen principal
            imagen_obj = ImagenPieza.objects.filter(pieza=pieza).first()
            if imagen_obj and imagen_obj.url_imagen:
                imagen_principal = request.build_absolute_uri(imagen_obj.url_imagen.url)
            elif pieza.imagen:
                imagen_principal = request.build_absolute_uri(pieza.imagen.url)
            
            items.append({
                'id': pieza.id,
                'linea_id': linea.id,
                'cantidad': linea.cantidad,
                'nombre': pieza.nombre,
                'imagen': imagen_principal,
                'precio': str(linea.precio_unitario),
                'precio_total_piezas': str(linea.subtotal),
                'stock_disponible': pieza.stock,
            })

        return Response({
            'pedido_id': pedido.id,
            'items': items,
            'total_items': len(items),
            'precio_total': str(pedido.total)
        })

    def retrieve(self, request, pk=None):
        """
        Devuelve el detalle de una pieza específica del carrito.
        
        GET /api/v1/carrito/{pieza_id}/
        """
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'error': 'Usuario no es cliente'}, status=400)

        pedido = self.get_carrito(cliente)
        
        try:
            linea = pedido.lineas_pedido.get(pieza_id=pk)
            pieza = linea.pieza
            
            imagen_principal = None
            imagen_obj = ImagenPieza.objects.filter(pieza=pieza).first()
            if imagen_obj and imagen_obj.url_imagen:
                imagen_principal = request.build_absolute_uri(imagen_obj.url_imagen.url)
            elif pieza.imagen:
                imagen_principal = request.build_absolute_uri(pieza.imagen.url)
            
            return Response({
                'id': pieza.id,
                'linea_id': linea.id,
                'cantidad': linea.cantidad,
                'nombre': pieza.nombre,
                'imagen': imagen_principal,
                'precio': str(linea.precio_unitario),
                'precio_total_piezas': str(linea.subtotal),
            })
        except LineaPedido.DoesNotExist:
            return Response({'error': 'Pieza no encontrada en el carrito'}, status=404)

    def create(self, request):
        """
        Agrega o actualiza una pieza en el carrito.
        
        POST /api/v1/carrito/
        {
            "pieza_id": 7,
            "cantidad": 3
        }
        """
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'error': 'Usuario no es cliente'}, status=400)

        pieza_id = request.data.get('pieza_id')
        cantidad = int(request.data.get('cantidad', 1))
        
        if not pieza_id:
            return Response({'error': 'Debe indicar el ID de la pieza'}, status=400)
        
        if cantidad < 1:
            return Response({'error': 'Cantidad debe ser mayor a 0'}, status=400)

        # Verificar que la pieza existe
        try:
            pieza = Pieza.objects.get(id=pieza_id)
        except Pieza.DoesNotExist:
            return Response({'error': 'Pieza no encontrada'}, status=404)

        # Verificar stock
        if pieza.stock < cantidad:
            return Response({
                'error': f'Stock insuficiente. Disponible: {pieza.stock}'
            }, status=400)

        pedido = self.get_carrito(cliente)
        
        # Busca si ya existe la línea
        linea, created = LineaPedido.objects.get_or_create(
            pedido=pedido,
            pieza=pieza,
            defaults={
                'cantidad': cantidad,
                'precio_unitario': pieza.precio_base,
                'descuento_aplicado': Decimal('0.00'),
                'subtotal': pieza.precio_base * cantidad
            }
        )
        
        if not created:
            # Actualizar cantidad si ya existía
            linea.cantidad = cantidad
            linea.subtotal = pieza.precio_base * cantidad
            linea.save()
        
        # Recalcular total del pedido
        self.calcular_total(pedido)

        if created:
            status_code = 201  # Se creó una nueva línea en el carrito
        else:
            status_code = 200  # Se actualizó una línea existente


        return Response({
            'message': 'Pieza agregada/actualizada en el carrito',
            'pieza_id': pieza.id,
            'pieza_nombre': pieza.nombre,
            'cantidad': linea.cantidad,
            'subtotal': str(linea.subtotal),
            'total_carrito': str(pedido.total)
        }, status=status_code)

    def partial_update(self, request, pk=None):
        """
        Actualiza la cantidad de una pieza en el carrito.
        
        PATCH /api/v1/carrito/{pieza_id}/
        {
            "cantidad": 5
        }
        """
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'error': 'Usuario no es cliente'}, status=400)

        cantidad = request.data.get('cantidad')
        if cantidad is None:
            return Response({'error': 'Debe indicar la cantidad'}, status=400)
        
        cantidad = int(cantidad)
        if cantidad < 1:
            return Response({'error': 'Cantidad debe ser mayor a 0'}, status=400)

        pedido = self.get_carrito(cliente)
        
        try:
            linea = pedido.lineas_pedido.get(pieza_id=pk)
        except LineaPedido.DoesNotExist:
            return Response({'error': 'Pieza no encontrada en el carrito'}, status=404)

        # Verificar stock
        if linea.pieza.stock < cantidad:
            return Response({
                'error': f'Stock insuficiente. Disponible: {linea.pieza.stock}'
            }, status=400)

        linea.cantidad = cantidad
        linea.subtotal = linea.precio_unitario * cantidad
        linea.save()
        
        self.calcular_total(pedido)

        return Response({
            'message': 'Cantidad actualizada',
            'pieza_id': linea.pieza.id,
            'cantidad': linea.cantidad,
            'subtotal': str(linea.subtotal),
            'total_carrito': str(pedido.total)
        })

    def destroy(self, request, pk=None):
        """
        Elimina una pieza del carrito.
        
        DELETE /api/v1/carrito/{pieza_id}/
        """
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'error': 'Usuario no es cliente'}, status=400)

        pedido = self.get_carrito(cliente)
        
        try:
            linea = pedido.lineas_pedido.get(pieza_id=pk)
            nombre_pieza = linea.pieza.nombre
            linea.delete()
            
            self.calcular_total(pedido)
            
            return Response({
                'message': f'"{nombre_pieza}" eliminada del carrito',
                'total_carrito': str(pedido.total)
            })
        except LineaPedido.DoesNotExist:
            return Response({'error': 'Pieza no encontrada en el carrito'}, status=404)

    @action(detail=False, methods=['post'])
    def vaciar(self, request):
        """
        Vacía completamente el carrito.
        
        POST /api/v1/carrito/vaciar/
        """
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'error': 'Usuario no es cliente'}, status=400)

        pedido = self.get_carrito(cliente)
        cantidad = pedido.lineas_pedido.count()
        pedido.lineas_pedido.all().delete()
        pedido.total = Decimal('0.00')
        pedido.save()

        return Response({
            'message': f'Carrito vaciado ({cantidad} items eliminados)'
        })

    @action(detail=False, methods=['post'])
    def finalizar(self, request):
        """
        Finaliza la compra del carrito actual.
        
        POST /api/v1/carrito/finalizar/
        {
            "direccion_envio": "Calle Ejemplo 123",
            "metodo_pago_id": 1  // opcional
        }
        """
        import uuid

        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response({'error': 'Usuario no es cliente'}, status=400)

        # 1. Obtener carrito
        pedido = self.get_carrito(cliente)
        
        if not pedido.lineas_pedido.exists():
            return Response({'error': 'El carrito está vacío'}, status=400)

        # 2. Verificar que tiene al menos un método de pago
        metodos_cliente = MetodoPago.objects.filter(cliente=cliente)
        if not metodos_cliente.exists():
            return Response({
                'error': 'Debe registrar al menos un método de pago antes de realizar la compra'
            }, status=400)

        # 3. Obtener dirección
        direccion = request.data.get('direccion_envio')
        if not direccion:
            return Response({'error': 'Debe proporcionar una dirección de envío'}, status=400)

        
        # 4. Obtener método de pago
        metodo_pago_id = request.data.get('metodo_pago_id')
        if metodo_pago_id:
            try:
                metodo_pago = MetodoPago.objects.get(id=metodo_pago_id, cliente=cliente)
            except MetodoPago.DoesNotExist:
                return Response({'error': 'Método de pago no válido'}, status=400)



        # 5. Verificar stock de todas las piezas
        for linea in pedido.lineas_pedido.all():
            if linea.pieza.stock < linea.cantidad:
                return Response({
                    'error': f'Stock insuficiente para "{linea.pieza.nombre}". Disponible: {linea.pieza.stock}'
                }, status=400)

        # 6. Descontar stock
        for linea in pedido.lineas_pedido.all():
            linea.pieza.stock -= linea.cantidad
            linea.pieza.save()

        # 7. Actualizar pedido
        pedido.estado = Pedido.PENDIENTE
        pedido.fecha_pedido = date.today()
        pedido.direccion_envio = direccion
        if not pedido.vendedor:
            pedido.vendedor = Vendedor.objects.first()
        pedido.save()

        # 8. Crear registro de pago
        Pago.objects.create(
            pedido=pedido,
            metodo_pago=metodo_pago,
            fecha_pago=date.today(),
            monto=pedido.total,
            estado=Pago.PENDIENTE,
            numero_transaccion=str(uuid.uuid4())[:20]
        )

        return Response({
            'message': 'Compra realizada con éxito',
            'pedido_id': pedido.id,
            'total': str(pedido.total),
            'items': pedido.lineas_pedido.count(),
            'metodo_pago_usado': metodo_pago.id
        }, status=201)




# ==================== ESTADO DE AUTENTICACIÓN ====================
class AuthStatusView(APIView):
    """
    Verifica si el usuario está autenticado usando JWT.
    
    GET /api/v1/auth/status/
    Header: Authorization: Bearer TU_ACCESS_TOKEN
    """
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user and request.user.is_authenticated:
            return Response({
                'is_authenticated': True,
                'user': {
                    'id': request.user.id,
                    'username': request.user.username,
                    'email': request.user.email,
                    'rol': request.user.rol,
                }
            })
        return Response({'is_authenticated': False}, status=200)


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


# ============================================================
# PAYPAL - INTEGRACIÓN DE PAGOS
# ============================================================

def configurar_paypal():
    """Configura el SDK de PayPal con las credenciales. Este método
    funciona para conectarme a PayPal Sandbox.  
    
    """
    paypalrestsdk.configure({
        "mode": settings.PAYPAL_MODE,  #Defino que uso el entorno de prueba sandbox
        "client_id": settings.PAYPAL_CLIENT_ID, #Identificador público de tu aplicación en PayPal
        "client_secret": settings.PAYPAL_CLIENT_SECRET #Clave secreta de tu aplicación en PayPal
    })


class CrearOrdenPayPalView(APIView):
    """
    Crea una orden de pago en PayPal.
    
    POST /api/v1/paypal/crear-orden/
    {
        "pedido_id": 123
    }
    
    Respuesta exitosa:
    {
        "success": true,
        "order_id": "PAYID-...",
        "approval_url": "https://www.sandbox.paypal.com/..."
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pedido_id = request.data.get('pedido_id')
        
        if not pedido_id:
            return Response(
                {'error': 'El campo pedido_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que el usuario es cliente
        try:
            cliente = request.user.cliente
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'El usuario no tiene perfil de cliente'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener el pedido
        try:
            pedido = Pedido.objects.get(id=pedido_id, cliente=cliente)
        except Pedido.DoesNotExist:
            return Response(
                {'error': 'Pedido no encontrado o no pertenece al cliente'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar estado válido para pagar
        if pedido.estado not in [Pedido.PENDIENTE, Pedido.CARRITO]:
            return Response(
                {'error': f'El pedido no está en estado válido para pagar. Estado actual: {pedido.get_estado_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar si ya existe un pago PayPal pendiente
        pago_existente = PagoPayPal.objects.filter(
            pedido=pedido,
            estado__in=[PagoPayPal.CREADO, PagoPayPal.APROBADO]
        ).first()

        if pago_existente:
            # Construir la URL de aprobación de PayPal Sandbox
            url_aprobacion = f"https://www.sandbox.paypal.com/checkoutnow?token={pago_existente.paypal_order_id}"
            
            return Response({
                'success': True,
                'order_id': pago_existente.paypal_order_id,
                'approval_url': url_aprobacion,
                'message': 'Ya existe una orden de pago pendiente'
            })

        # Configurar PayPal (iniciarlo con las credenciales)
        configurar_paypal()

        # Crear la orden en PayPal
        monto_total = str(pedido.total)
        
        #Crea un objeto de pago de PayPal (orde de pago) usando la librería paypalrestsdk
        payment = paypalrestsdk.Payment({
            "intent": "sale", #Se define el pago como una venta ("intent": "sale").
            "payer": {
                "payment_method": "paypal" #Se indica que el método de pago será PayPal ("payment_method": "paypal").
            },
            #Se configuran las URLs a las que PayPal redirigirá al usuario tras aprobar o cancelar el pago
            "redirect_urls": {
                "return_url": settings.PAYPAL_RETURN_URL,
                "cancel_url": settings.PAYPAL_CANCEL_URL
            },

            #Se especifica la transacción
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": f"Pedido #{pedido.id}",
                        "sku": f"PED-{pedido.id}",
                        "price": monto_total,
                        "currency": "EUR",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": monto_total,
                    "currency": "EUR"
                },
                "description": f"Pago del pedido #{pedido.id}"
            }]
        })

        if payment.create():
            # Obtener la URL de aprobación
            approval_url = None

            for link in payment.links: #Itera sobre los enlaces que PayPal devuelve en la respuesta de creación del pago
                #Busca el enlace que tiene la relación "approval_url", que es la URL
                #  a la que el usuario debe ser redirigido para aprobar el pago
                if link.rel == "approval_url": 
                    approval_url = link.href 
                    break

            # Guardar el registro de PagoPayPal
            pago_paypal = PagoPayPal.objects.create(
                pedido=pedido,
                paypal_order_id=payment.id,
                estado=PagoPayPal.CREADO,
                monto=Decimal(monto_total),
                moneda="EUR",
                respuesta_paypal=payment.to_dict()
            )

            return Response({
                'success': True,
                'order_id': payment.id,
                'approval_url': approval_url,
                'pago_paypal_id': pago_paypal.id
            })
        else:
            return Response({
                'success': False,
                'error': 'Error al crear la orden en PayPal',
                'details': payment.error
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CapturarPagoPayPalView(APIView):
    """
    Captura el pago después de que el usuario lo aprobó en PayPal.
    
    POST /api/v1/paypal/capturar-pago/
    {
        "payment_id": "PAYID-...",
        "payer_id": "ABCD1234..."
    }
    
    El payer_id viene en la URL de retorno de PayPal como query param.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payment_id = request.data.get('payment_id') #identifica la orden pago creada en PayPal, viene en la URL de retorno de PayPal como query param
        payer_id = request.data.get('payer_id') # identifica al pagador, viene en la URL de retorno de PayPal como query param

        if not payment_id or not payer_id:
            return Response(
                {'error': 'payment_id y payer_id son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Buscar el registro de PagoPayPal
        try:
            pago_paypal = PagoPayPal.objects.get(paypal_order_id=payment_id)
        except PagoPayPal.DoesNotExist:
            return Response(
                {'error': 'No se encontró el registro de pago'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar que pertenece al cliente
        try:
            cliente = request.user.cliente
            if pago_paypal.pedido.cliente != cliente:
                return Response(
                    {'error': 'Este pago no pertenece al cliente'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'El usuario no tiene perfil de cliente'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar si ya fue capturado
        if pago_paypal.estado == PagoPayPal.CAPTURADO:
            return Response({
                'success': True,
                'message': 'Este pago ya fue capturado anteriormente',
                'pedido_id': pago_paypal.pedido.id
            })

        if pago_paypal.estado not in [PagoPayPal.CREADO, PagoPayPal.APROBADO]:
            return Response(
                {'error': f'El pago no está en estado válido. Estado: {pago_paypal.get_estado_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        #Volvemos a iniciar Paypal con nuestras credenciales 
        configurar_paypal()

        #Recuperamos la orden de pago de PayPal usando el payment_id (paypal_order_id) que guardamos en nuestro modelo PagoPayPal
        payment = paypalrestsdk.Payment.find(payment_id)

        #Intentamos ejecutar (capturar) el pago usando el payer_id que PayPal nos devuelve cuando el usuario aprueba el pago.
        if payment.execute({"payer_id": payer_id}):
            # Pago exitoso
            pago_paypal.estado = PagoPayPal.CAPTURADO
            pago_paypal.respuesta_paypal = payment.to_dict() # Guardamos la respuesta completa de PayPal
            
            # Obtener el capture_id
            try:

                #Accede a la lista de recursos relacionados (related_resources) de la primera transacción del pago.
                related_resources = payment.transactions[0].related_resources
                
                #Verifica que la lista no esté vacía (es decir, que PayPal devolvió información de la venta).
                if related_resources:
                    pago_paypal.paypal_capture_id = related_resources[0].sale.id
            
            except (IndexError, AttributeError):
                pass

            pago_paypal.save() # Guardamos el estado actualizado del pago PayPal en nuestra base de datos

            # Actualizar el pedido a PAGADO
            pedido = pago_paypal.pedido
            pedido.estado = Pedido.PAGADO
            pedido.save()

            # Buscar el método de pago tipo BILLETERA del cliente para asociarlo al pago
            metodo_paypal = MetodoPago.objects.filter(
                            cliente=pedido.cliente,
                            tipo_metodo=MetodoPago.BILLETERA).first()

            # Crear registro en modelo Pago
            pago = Pago.objects.create(
                pedido=pedido,
                metodo_pago= metodo_paypal,
                fecha_pago=date.today(),
                monto=pago_paypal.monto,
                estado=Pago.COMPLETADO,
                numero_transaccion=payment_id
            )

            pago_paypal.pago = pago
            pago_paypal.save()

            return Response({
                'success': True,
                'message': 'Pago completado exitosamente',
                'pedido_id': pedido.id,
                'estado_pedido': pedido.get_estado_display(),
                'monto': str(pago_paypal.monto),
                'transaction_id': pago_paypal.paypal_capture_id or payment_id
            })
        else:
            pago_paypal.estado = PagoPayPal.FALLIDO
            pago_paypal.respuesta_paypal = payment.error
            pago_paypal.save()

            return Response({
                'success': False,
                'error': 'Error al procesar el pago',
                'details': payment.error
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelarPagoPayPalView(APIView):
    """
    Maneja cuando el usuario cancela el pago en PayPal.
    
    POST /api/v1/paypal/cancelar-pago/
    {
        "payment_id": "PAYID-..."
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        payment_id = request.data.get('payment_id')

        if not payment_id:
            return Response(
                {'error': 'payment_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pago_paypal = PagoPayPal.objects.get(paypal_order_id=payment_id)
            
            cliente = request.user.cliente
            if pago_paypal.pedido.cliente != cliente:
                return Response(
                    {'error': 'Este pago no pertenece al cliente'},
                    status=status.HTTP_403_FORBIDDEN
                )

            pago_paypal.estado = PagoPayPal.CANCELADO
            pago_paypal.save()

            return Response({
                'success': True,
                'message': 'Pago cancelado',
                'pedido_id': pago_paypal.pedido.id
            })

        except PagoPayPal.DoesNotExist:
            return Response(
                {'error': 'No se encontró el registro de pago'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'El usuario no tiene perfil de cliente'},
                status=status.HTTP_400_BAD_REQUEST
            )


from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from .serializers import PasswordResetSerializer

class PasswordResetRequestView(APIView): 
    """
    Maneja las solicitudes de reseteo de contraseña. Recibe un email, verifica 
    si existe un usuario con ese email y envía un enlace de reseteo si es así. 

    POST /api/v1/auth/password-reset/ { "email": "usuario@tienda.com" }

    Documentación de Django sobre tokens de reseteo de contraseña:
    https://docs.djangoproject.com/en/4.2/topics/auth/default/#django.contrib.auth.tokens.PasswordResetTokenGenerator

    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = Usuario.objects.get(email=email)
            
            except Usuario.DoesNotExist:
                # Por seguridad, respondemos igual aunque el usuario no exista
                return Response({"detail": "Si el email existe, se enviará un enlace de reseteo."}, status=status.HTTP_200_OK)

            #generamos el token
            token = PasswordResetTokenGenerator().make_token(user)

            #Codificamos el ID del usuario en base64 para incluirlo en la URL de reseteo
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            
            #URL de reseteo a la app de vue, donde el frontend tendrá una ruta que reciba 
            # el uid y el token para mostrar el formulario de nueva contraseña
            reset_url = f"http://localhost:8080/restablecer-contrasena?uid={uid}&token={token}"


            #Este método viene de django.core.mail 
            send_mail(
                subject="Recupera tu contraseña",
                message=f"Para restablecer tu contraseña, haz clic en el siguiente enlace: {reset_url}",
                
                #from_email: El correo del remitente, tomado de settings.DEFAULT_FROM_EMAIL (debes definirlo en tu settings.py).
                from_email=settings.DEFAULT_FROM_EMAIL,
                
                #recipient_list: Una lista con el email del destinatario (el usuario que pidió el reseteo).
                recipient_list=[email],
                
                #fail_silently=False: Si ocurre un error al enviar el correo, lanzará una excepción (útil para detectar problemas en desarrollo).
                fail_silently=False,
            )

            return Response({"detail": "Si el email existe, se enviará un enlace de reseteo."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            #Obtiene el uid, token y nueva contraseña del cuerpo de la solicitud
            uid = serializer.validated_data['uid']
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']

            #Obtenemos el modelo de usuario activo en el proyecto (el modelo Usuario personalizado)
            User = get_user_model()
            try:
                #Decodifica el uid que viene en base64 para obtener el ID del usuario
                uid_decoded = urlsafe_base64_decode(uid).decode()

                #Busca el usuario en la base de datos usando el ID decodificado
                user = User.objects.get(pk=uid_decoded)

             #ValueError, TypeError, OverflowError: Si el uid está malformado, vacío, o no puede convertirse correctamente (por ejemplo, si alguien manipula el enlace).   
            except (User.DoesNotExist, ValueError, TypeError, OverflowError):
                return Response({"error": "Enlace no válido o usuario no encontrado."}, status=status.HTTP_400_BAD_REQUEST)


            #Utiliza el PasswordResetTokenGenerator de Django para verificar que el token es válido para ese usuario. 
            # El token se genera usando información del usuario (como su ID, fecha de última modificación de contraseña, etc.) 
            # y tiene una validez limitada (por defecto, unas horas). Si el token no es válido o ha expirado, se devuelve un error.
            token_generator = PasswordResetTokenGenerator()

            if not token_generator.check_token(user, token): 
                return Response({"error": "El enlace de reseteo no es válido o ha expirado."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Actualiza la contraseña del usuario
            user.set_password(new_password)
            user.save()
            return Response({"detail": "Contraseña actualizada con éxito."}, status=status.HTTP_200_OK)
            
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        


#######################################################################
# ==================== Contacto con vendedor ====================
#######################################################################
from django.core.mail import send_mail
class ContactoVendedorAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Endpoint para que los clientes puedan enviar un mensaje de contacto al vendedor.
        Post /api/v1/contacto-vendedor/
        {
            "nombre": "Juan Pérez",
            "email": "juan.perez@example.com",
            "numero_telefono": "123456789",
            "mensaje": "Estoy interesado en uno de tus productos, ¿podrías darme más información?"
        }   

        """
        serializer = ContactoVendedorSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        datos = serializer.validated_data
        nombre = datos['nombre']
        email = datos['email']
        numero_telefono = datos['numero_telefono']
        asunto = f"Nuevo mensaje de contacto de {nombre}"
        mensaje = f"Nombre: {nombre}\nEmail: {email}\nNúmero de teléfono: {numero_telefono}\n\nMensaje:\n{datos['mensaje']}"

        try:
            #send_mail es una función de Django que envía un correo electrónico. 
            send_mail(
                asunto,
                mensaje,
                None,  # Usa DEFAULT_FROM_EMAIL
                [settings.EMAIL_HOST_USER],  # Envía el correo al email del vendedor (definido en settings.EMAIL_HOST_USER)
                fail_silently=False, #Si ocurre un error al enviar el correo, lanzará una excepción (útil para detectar problemas en desarrollo).
            )
            return Response({'mensaje': 'Mensaje enviado correctamente.'}, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({'error': f'Error al enviar el correo: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

#######################################################################
# ==================== Chatbot ==================== 
#######################################################################
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
#import os

from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes

# Cargar variables de entorno
load_dotenv()
#GEMINI_API_KEY_1 = os.getenv('GEMINI_API_KEY_1')
#GEMINI_API_KEY_2 = os.getenv('GEMINI_API_KEY_2')
#
#GEMINI_API_URL_1 = f'https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY_1}'
#GEMINI_API_URL_2 = f'https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY_2}'

# @api_view(['POST'])
# @permission_classes([AllowAny])
# def chatbot_view(request):
#     """
#     Endpoint para el chatbot.
#     1. Recibe una pregunta del usuario (POST, campo 'pregunta').
#     2. Lee el documento FAQ (Markdown) con la información de referencia.
#     3. Arma el prompt para el LLM (aquí solo lo mostramos, luego se enviará a Gemini).
#     4. Llama a Gemini y devuelve la respuesta real.

#     POST /api/v1/chatbot/
#     {
#         "pregunta": "¿Cuál es el horario de atención?"
#     }

#     Respuesta:
#     {
#         "respuesta": "Nuestro horario de atención es de lunes a viernes de 9:00
#         a 18:00 y sábados de 10:00 a 14:00."
#     }
#     """
#     #Busca la clave pregunta, en caso contrario muestra cadena vacia
#     #.strip() para eliminar espacios al inicio y al final de la pregunta
#     pregunta = request.data.get('pregunta', '').strip()
    
#     if not pregunta:
#         return Response({'error': 'No se recibió ninguna pregunta.'}, status=status.HTTP_400_BAD_REQUEST)

#     # 2. Leer el documento FAQ
#     #faq_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'faq_motorpartexpress.md')
    
#     # Obtiene la ruta absoluta de la carpeta actual (donde está este archivo)
#     base_dir = os.path.dirname(__file__)

#     # Une la ruta base con la carpeta 'chatbot' y el nombre del archivo FAQ
#     faq_path = os.path.join(base_dir, 'chatbot', 'faq_motorpartexpress.md')


#     try:
#         #Abrimos el archivo FAQ en modo lectura ('r') y con codificación UTF-8 para asegurarnos de que se lean correctamente los caracteres especiales.
#         with open(faq_path, 'r', encoding='utf-8') as f: #f es una variable que representa el archivo abierto, y se utiliza para leer su contenido.
#             faq_contenido = f.read() #Lee contenido, convierte a string y guarda contenido en variable faq_contenido
#     except Exception as e:
#         return Response({'error': f'No se pudo leer el documento FAQ: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     # 3. Armar el prompt
#     instruccion_extra = (
#         'Si ya saludaste antes, no repitas el saludo en las siguientes respuestas. '
#         'Responde directamente a la pregunta si ya hubo interacción previa.'
#     )
#     prompt = (
#         'Eres el asistente de Motor Part Express. Debes ser amigable. Recuerda que eres un experto en piezas de coches.'
#         ' Usa solo la información del siguiente documento para responder. '
#         'Si no encuentras la respuesta, indica que el usuario debe contactar a un vendedor o usar el formulario de contacto.\n\n'
#         f'{instruccion_extra}\n'
#         f'DOCUMENTO DE REFERENCIA:\n{faq_contenido}\n\n'
#         f'PREGUNTA DEL USUARIO: {pregunta}\n\n'
#         'RESPUESTA:'
#     )

#     # 4. Enviar el prompt a Gemini
#     headers = {'Content-Type': 'application/json'} #Encabezados HTTP para indicar que el cuerpo de la solicitud es JSON
    
#     #Cuerpo o payload tipo post para enviar a Gemini, con el prompt dentro de la estructura que Gemini espera (en contents -> parts -> text)
#     data = {
#         "contents": [
#             {"parts": [{"text": prompt}]}
#         ]
#     }

#     try:
#         #GEMINI_API_URL_1: Es la URL del endpoint de la API de Gemini a la que se envía la solicitud.
#         response = requests.post(GEMINI_API_URL_1, headers=headers, json=data, timeout=20)
        
#         response.raise_for_status() #verifica si la respuesta HTTP de la API de Gemini fue exitosa
        
#         gemini_data = response.json() #Convierte la respuesta de Gemini de formato JSON a un diccionario de Python para poder trabajar con los datos devueltos por Gemini.
        
#         # Extraer respuesta de forma robusta
#         respuesta_llm = ""

#         try:
#         #gemini_data es un diccionario con la respuesta completa de Gemini (la API de Google).
#         #['candidates'][0] accede al primer candidato de respuesta que devuelve Gemini (puede haber varios, pero normalmente solo usas el primero).
#         #['content']['parts'][0] entra al contenido de ese candidato y toma la primera parte de la respuesta.
#         #.get('text', '') busca el texto de la respuesta generada por Gemini. Si no lo encuentra, devuelve una cadena vacía.
#             respuesta_llm = gemini_data['candidates'][0]['content']['parts'][0].get('text', '')
#             print("Respuesta Gemini:", respuesta_llm)
#         except Exception:
#             respuesta_llm = str(gemini_data)
    
#     except Exception as e:
#         return Response({'error': f'Error al consultar Gemini: {str(e)}'}, status=500)

#     # 5. Devolver la respuesta al usuario
#     return Response({'respuesta': respuesta_llm})


import json

class ChatbotView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Obtener el mensaje del usuario y el historial de la conversación
        mensajeUsuario = request.data.get('mensaje', '')
        historialConversacion = request.data.get('historial', [])

        base_dir = os.path.dirname(os.path.abspath(__file__))
        faq_path = os.path.join(base_dir, 'chatbot', 'faq_motorpartexpress.md')
        
        # Leer el contenido del archivo FAQ
        try:
            with open(faq_path, 'r', encoding='utf-8') as f:
                faq_content = f.read()
        
        except Exception as e:
            return Response({'error': f'Error al leer el archivo FAQ: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

     
        historial_formateado = [] #variable para enviar contexto de conversación al modelo
        for msj in historialConversacion:
            usuario = msj.get('user', '')
            bot = msj.get('bot', '')
            historial_formateado.append(f"Usuario: {usuario}\nBot: {bot}")

        prompt = (
            "Eres un chatbot experto en atención al cliente de MotorPartExpress. "
            "Responde de forma profesional, útil y sin repetir saludos como 'Hola' o 'Bienvenido' en cada respuesta. "
            "Utiliza la siguiente información de la FAQ para ayudar al usuario.\n\n"
            f"FAQ:\n{faq_content}\n\n"
            "Historial de la conversación:\n" +
            "\n".join(historial_formateado) +
            f"\n\nUsuario: {mensajeUsuario}\nBot:"
        )

        # Obtener las claves de API de Gemini desde variables de entorno
        api_key_1 = os.getenv('GEMINI_API_KEY_1')
        api_key_2 = os.getenv('GEMINI_API_KEY_2')
        url = 'https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash-lite:generateContent'

        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [
                {"parts": [{"text": prompt}]}
            ]
        }

        def llamada_gemini(api_key):
            """
            Realiza una petición a la API de Gemini con la clave proporcionada.
            Imprime el status code y el texto de la respuesta para depuración.
            """
            response = requests.post(f"{url}?key={api_key}", headers=headers, data=json.dumps(payload))
            #print(f"[Gemini] Status: {response.status_code}")
            #print(f"[Gemini] Body: {response.text}")
            return response

        # --- Fallback automático entre dos claves API ---
        response = None
        error_messages = []

        # Intentar con la primera clave llamando a la funcion llamada_gemini
        #si falla una prueba con la otra y guarda el error
        if api_key_1:
            response = llamada_gemini(api_key_1)
            
            # Si hay error de cuota o rate limit, guardar el error y probar la segunda clave
            if response.status_code == 429 or (response.status_code == 400 and 'quota' in response.text.lower()):
                error_messages.append(f"Clave 1: {response.status_code} {response.text}")
                
                if api_key_2:
                    response = llamada_gemini(api_key_2)
            # Si no hay error, continuar
        
        elif api_key_2:
            # Si no hay clave 1, probar directamente con la clave 2
            response = llamada_gemini(api_key_2)

        # Procesar la respuesta
        if response and response.status_code == 200:
            data = response.json()
            try:
                mensaje_bot = data['candidates'][0]['content']['parts'][0]['text']
            
            except Exception:
                mensaje_bot = "Lo siento, no pude procesar la respuesta de Gemini."
            
            return Response({'response': mensaje_bot})
        
        else:
            # Si ambas claves fallan, mostrar los errores acumulados
            if error_messages:
                error_detail = " | ".join(error_messages)
            elif response:
                error_detail = f"Error de Gemini: {response.status_code} {response.text}"
            else:
                error_detail = "No se pudo conectar a Gemini."
            return Response({'error': error_detail}, status=status.HTTP_502_BAD_GATEWAY)