from datetime import date
from rest_framework import serializers
from django.core.validators import EmailValidator
from django.utils import timezone
from .models import *


# ============================================================
# USUARIO / CLIENTE / VENDEDOR
# ============================================================

class UsuarioSerializer(serializers.ModelSerializer):
    #class Meta:
    #    model = Usuario
    #    fields = "__all__"
    class Meta:
        model = Usuario
        fields = [
            'url',
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'telefono',
            'direccion',
            'fecha_nacimiento',
            'password',
            'date_joined',
            'is_staff',
        ]


class ClienteSerializer(serializers.ModelSerializer): 
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = Cliente
        fields = ['id', 'usuario']


        



class VendedorSerializer(serializers.HyperlinkedModelSerializer):
    usuario = UsuarioSerializer(read_only=True)

    class Meta:
        model = Vendedor
        fields = ['id', 'usuario', 'fecha_contratacion', 'comision_porcentaje']




# ============================================================
# CATEGORIA_PIEZAS 
# ============================================================

class CategoriaPiezaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CategoriaPieza
        fields = ['id', 'nombre', 'imagen_categoria']





# ============================================================
# PIEZAS 
# ============================================================

class PiezaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Pieza
        fields = ['id', 'nombre', 'marca', 'anio', 'precio_base', 'descripcion', 'estado', 'referencia', 'version','imagen']


class ImagenPiezaSerializer(serializers.HyperlinkedModelSerializer):
    pieza = PiezaSerializer(read_only=True)

    class Meta:
        model = ImagenPieza
        fields = "__all__"



    


# ============================================================
# PEDIDOS / LINEAS DE PEDIDO
# ============================================================

class LineaPedidoSerializer(serializers.HyperlinkedModelSerializer):
    pieza = PiezaSerializer(read_only=True)
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = LineaPedido
        fields = "__all__"


    def to_representation(self, instance):
        """
        Método principal: Genera el JSON y aplica filtros de seguridad.
        """
        # 1. Obtenemos el objeto linea pedido (instance) de la bd en formato dict  para convertirlo a JSON
        data = super().to_representation(instance)

        # 2. Si el usuario es cliente, limpiamos los datos sensibles
        if self.es_cliente():
            data = self.filtrar_datos_para_cliente_lineaPedido(data, instance)

        return data

    # ------------------------------------------------------------------
    # MÉTODOS AUXILIARES (HELPER METHODS)
    # ------------------------------------------------------------------

    def es_cliente(self):
        """Devuelve True si quien hace la petición es un CLIENTE."""
        datosUser = self.context.get('request')
        if datosUser and datosUser.user.is_authenticated:
            #getattr: obtiene el atributo 'rol' del usuario, si no existe devuelve None
            es_cliente= getattr(datosUser.user, 'rol', None) == Usuario.CLIENTE
            return es_cliente
        return False

    def filtrar_datos_para_cliente_lineaPedido(self, data, instance):
        """Reemplaza los objetos complejos por información que interesa enviar al cliente."""
        
        if instance.pieza:
            data['pieza'] = {
                "nombre": instance.pieza.nombre,   
                "marca": instance.pieza.marca,
                "anio": instance.pieza.anio,
                "descripcion": instance.pieza.descripcion,
                "estado": instance.pieza.estado,


            }
        else:
            data['pieza'] = None

        return data


class PedidoSerializer(serializers.HyperlinkedModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    vendedor = VendedorSerializer(read_only=True)
    lineas_pedido = LineaPedidoSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = "__all__"

     
    def to_representation(self, instance):
        """
        Método principal: Genera el JSON y aplica filtros de seguridad.
        """
        # 1. Obtenemos el objeto pedido (instance) de la bd en formato dict  para convertirlo a JSON
        data = super().to_representation(instance)

        # 2. Si el usuario es cliente, limpiamos los datos sensibles
        if self.es_cliente():
            data = self.filtrar_datos_para_cliente(data, instance)

        return data

    # ------------------------------------------------------------------
    # MÉTODOS AUXILIARES (HELPER METHODS)
    # ------------------------------------------------------------------

    def es_cliente(self):
        """Devuelve True si quien hace la petición es un CLIENTE."""
        datosUser = self.context.get('request')
        if datosUser and datosUser.user.is_authenticated:
            #getattr: obtiene el atributo 'rol' del usuario, si no existe devuelve None
            es_cliente= getattr(datosUser.user, 'rol', None) == Usuario.CLIENTE
            return es_cliente
        return False

    def filtrar_datos_para_cliente(self, data, instance):
        """Reemplaza los objetos complejos por información que interesa enviar al cliente."""
        # Simplificar Vendedor (Solo nombre y apellido)
        if instance.vendedor and instance.vendedor.usuario:
            data['vendedor'] = {
                "nombre": instance.vendedor.usuario.first_name,
                "apellido": instance.vendedor.usuario.last_name
            }
        else:
            data['vendedor'] = None
        return data



class PedidoSimpleSerializer(serializers.ModelSerializer):
    """
    Serializador simplificado de Pedido con los datos más relevantes para perfil vendedor.
    """
    cliente_nombre = serializers.CharField(source='cliente.usuario.first_name', read_only=True)
    cliente_apellido = serializers.CharField(source='cliente.usuario.last_name', read_only=True)
    cliente_email = serializers.CharField(source='cliente.usuario.email', read_only=True)
    vendedor_nombre = serializers.CharField(source='vendedor.usuario.first_name', read_only=True)
    lineas_pedido = LineaPedidoSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'id',
            'cliente_nombre',
            'cliente_apellido',
            'cliente_email',
            'vendedor_nombre',
            'estado',
            'fecha_pedido',
            'direccion_envio',
            'total',
            'lineas_pedido'
        ]


class CambiarEstadoPedidoVendedorSerializer(serializers.Serializer):
    estado = serializers.IntegerField(min_value=1, max_value=5)

    
# ============================================================
# CARRITO EN SESIÓN
# ============================================================
class FinalizarCompraSerializer(serializers.Serializer):
    """Serializador para finalizar la compra del carrito."""
    direccion_envio = serializers.CharField(
        max_length=255,
        required=False,
        help_text="Dirección donde se enviará el pedido"
    )

    metodo_pago_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID del método de pago a utilizar (opcional, usa el predeterminado si no se envía)"
    )

    def validate_direccion_envio(self, valor):
        """Validar la longitud mínima si se proporciona."""
        if valor and len(valor.strip()) < 5:
            raise serializers.ValidationError("La dirección de envío es demasiado corta (mínimo 5 caracteres).")
        return valor.strip() if valor else valor
    



# ============================================================
# METODOS DE PAGO
# ============================================================

class MetodoPagoSerializer(serializers.ModelSerializer):
    #cliente = ClienteSerializer()

    class Meta:
        model = MetodoPago
        fields = "__all__"


class TarjetaSerializer(serializers.HyperlinkedModelSerializer):
    metodo_pago = MetodoPagoSerializer(read_only=True)

    class Meta:
        model = Tarjeta
        fields = "__all__"


class CuentaBancariaSerializer(serializers.HyperlinkedModelSerializer):
    metodo_pago = MetodoPagoSerializer(read_only=True)

    class Meta:
        model = CuentaBancaria
        fields = "__all__"


class BilleteraDigitalSerializer(serializers.HyperlinkedModelSerializer):
    metodo_pago = MetodoPagoSerializer(read_only=True)

    class Meta:
        model = BilleteraDigital
        fields = "__all__"


# ============================================================
# METODO DE PAGO PARA CLIENTE
# ============================================================
# --- Serializadores Auxiliares para validar los datos hijos ---
class TarjetaInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarjeta
        exclude = ['metodo_pago']
        # RELAJAMOS LAS REGLAS: Hacemos todo opcional aquí
        extra_kwargs = {
            'num_tarjeta_encriptado': {'required': False},
            'propietario': {'required': False},
            'fecha_caducidad': {'required': False},
            'moneda': {'required': False},
            'tipo_tarjeta': {'required': False}, 
        }

class CuentaBancariaInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuentaBancaria
        exclude = ['metodo_pago']
        # RELAJAMOS LAS REGLAS
        extra_kwargs = {
            'iban': {'required': False},
            'banco': {'required': False},
            'moneda': {'required': False},
        }

class BilleteraDigitalInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = BilleteraDigital
        exclude = ['metodo_pago']
        # RELAJAMOS LAS REGLAS
        extra_kwargs = {
            'email': {'required': False},
            'proveedor': {'required': False},
        }

# --- EL SERIALIZADOR MAESTRO ---
class CrearMetodoPagoUnificadoSerializer(serializers.ModelSerializer):
    # Permitimos null para que el frontend pueda enviar null si quiere
    detalles_tarjeta = TarjetaInputSerializer(required=False, allow_null=True)
    detalles_cuenta = CuentaBancariaInputSerializer(required=False, allow_null=True)
    detalles_billetera = BilleteraDigitalInputSerializer(required=False, allow_null=True)

    class Meta:
        model = MetodoPago
        fields = [
            'id', 
            'tipo_metodo', 
            'es_predeterminado', 
            'detalles_tarjeta', 
            'detalles_cuenta', 
            'detalles_billetera'
        ]


    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.tipo_metodo == MetodoPago.TARJETA:
            tarjeta = getattr(instance, 'tarjeta', None)
            if tarjeta:
                data['detalles_tarjeta'] = TarjetaSerializer(tarjeta, context=self.context).data
            else:
                data['detalles_tarjeta'] = None
            data['detalles_cuenta'] = None
            data['detalles_billetera'] = None
        elif instance.tipo_metodo == MetodoPago.CUENTA:
            cuenta = getattr(instance, 'cuenta_bancaria', None)
            if cuenta:
                data['detalles_cuenta'] = CuentaBancariaSerializer(cuenta, context=self.context).data
            else:
                data['detalles_cuenta'] = None
            data['detalles_tarjeta'] = None
            data['detalles_billetera'] = None
        elif instance.tipo_metodo == MetodoPago.BILLETERA:
            billetera = getattr(instance, 'billetera_digital', None)
            if billetera:
                data['detalles_billetera'] = BilleteraDigitalSerializer(billetera, context=self.context).data
            else:
                data['detalles_billetera'] = None
            data['detalles_tarjeta'] = None
            data['detalles_cuenta'] = None
        else:
            data['detalles_tarjeta'] = None
            data['detalles_cuenta'] = None
            data['detalles_billetera'] = None
        return data
    
    



    def validate(self, data):
        tipo = data.get('tipo_metodo')

        # --- VALIDACIÓN CONDICIONAL ---
        
        # CASO 1: TARJETA
        if tipo == MetodoPago.TARJETA:
            tarjeta_data = data.get('detalles_tarjeta')
            
            if not tarjeta_data:
                raise serializers.ValidationError({"detalles_tarjeta": "Faltan los datos de la tarjeta."})
            
            # Validación manual de campos críticos (porque los hicimos opcionales arriba)
            errores_tarjeta = {}

            if not tarjeta_data.get('num_tarjeta_encriptado'):
                errores_tarjeta['num_tarjeta_encriptado'] = "Este campo es requerido."
            
            if not tarjeta_data.get('propietario'):
                errores_tarjeta['propietario'] = "Este campo es requerido."
            
            if errores_tarjeta:
                raise serializers.ValidationError({"detalles_tarjeta": errores_tarjeta})

        # CASO 2: CUENTA BANCARIA
        elif tipo == MetodoPago.CUENTA:
            cuenta_data = data.get('detalles_cuenta')
            if not cuenta_data:
                raise serializers.ValidationError({"detalles_cuenta": "Faltan los datos de la cuenta bancaria."})
            
            errores_cuenta = {}
            if not cuenta_data.get('iban'):
                errores_cuenta['iban'] = "El IBAN es obligatorio."
            if not cuenta_data.get('banco'):
                errores_cuenta['banco'] = "El nombre del banco es obligatorio."
            
            if errores_cuenta:
                raise serializers.ValidationError({"detalles_cuenta": errores_cuenta})

        # CASO 3: BILLETERA DIGITAL
        elif tipo == MetodoPago.BILLETERA:
            billetera_data = data.get('detalles_billetera')
            if not billetera_data:
                raise serializers.ValidationError({"detalles_billetera": "Faltan los datos de la billetera."})
            
            if not billetera_data.get('email'):
                 raise serializers.ValidationError({"detalles_billetera": {"email": "El email es obligatorio."}})
            
        else:
            raise serializers.ValidationError({"tipo_metodo": "Tipo de método de pago no válido."})


        return data

    def create(self, validated_data):
        datos_tarjeta = validated_data.pop('detalles_tarjeta', None)
        datos_cuenta = validated_data.pop('detalles_cuenta', None)
        datos_billetera = validated_data.pop('detalles_billetera', None)

        #TODO: Es posible que de error porque hay que hacer una query al usuario autenticado
        cliente = self.context['request'].user.cliente 
        
        metodo_pago = MetodoPago.objects.create(cliente=cliente, **validated_data)

        if metodo_pago.tipo_metodo == MetodoPago.TARJETA and datos_tarjeta:
            Tarjeta.objects.create(metodo_pago=metodo_pago, **datos_tarjeta)
        elif metodo_pago.tipo_metodo == MetodoPago.CUENTA and datos_cuenta:
            CuentaBancaria.objects.create(metodo_pago=metodo_pago, **datos_cuenta)
        elif metodo_pago.tipo_metodo == MetodoPago.BILLETERA and datos_billetera:
            BilleteraDigital.objects.create(metodo_pago=metodo_pago, **datos_billetera)

        return metodo_pago

    def destroy(self):
        instance = self.instance
        # 1. Validación: No permitir borrar si tiene pagos asociados (historial financiero)
        # if instance.pagos.exists():
        #     raise serializers.ValidationError({"detail": "No se puede eliminar este método de pago porque tiene historial de pagos asociados."})

        era_predeterminado = instance.es_predeterminado
        cliente = instance.cliente

        # 2. Eliminamos el registro
        # Al eliminar el MetodoPago, se eliminan automáticamente los detalles (Tarjeta/Cuenta/Billetera) por el CASCADE del modelo
        instance.delete()

        # 3. Si borramos el predeterminado, asignamos uno nuevo (el más reciente que quede)
        if era_predeterminado:
            nuevo_default = MetodoPago.objects.filter(cliente=cliente).order_by('-id').first()
            if nuevo_default:
                nuevo_default.es_predeterminado = True
                nuevo_default.save()



# ============================================================
# PAGOS
# ============================================================

class PagoSerializer(serializers.HyperlinkedModelSerializer):
    pedido = PedidoSerializer(read_only=True)
    metodo_pago = MetodoPagoSerializer(read_only=True)

    class Meta:
        model = Pago
        fields = "__all__"


# ============================================================
# POST-VENTA
# ============================================================

# class DevolucionSerializer(serializers.HyperlinkedModelSerializer):
#     linea_pedido = LineaPedidoSerializer(read_only=True)
#     cliente = ClienteSerializer(read_only=True)

#     class Meta:
#         model = Devolucion
#         fields = "__all__"



class DevolucionSerializer(serializers.ModelSerializer):
    """Serializer para devoluciones."""
    
    # Campos de solo lectura para mostrar info útil
    pieza_nombre = serializers.CharField(source='linea_pedido.pieza.nombre', read_only=True)
    pedido_id = serializers.IntegerField(source='linea_pedido.pedido.id', read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.usuario.username', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    linea_pedido_estado= serializers.IntegerField(source='linea_pedido.estado', read_only=True)

    class Meta:
        model = Devolucion
        fields = [
            'id',
            'linea_pedido',
            'cliente',
            'fecha_solicitud',
            'fecha_aprobacion',
            'motivo',
            'estado',
            'estado_display',
            'cantidad_devuelta',
            'monto_reembolso',
            # Campos extra
            'pieza_nombre',
            'pedido_id',
            'cliente_nombre',
            'linea_pedido_estado',
        ]
        read_only_fields = ['id', 'fecha_solicitud', 'fecha_aprobacion', 'monto_reembolso']




#class ValoracionSerializer(serializers.HyperlinkedModelSerializer):
#    pieza = PiezaSerializer(read_only=True)
#    cliente = ClienteSerializer(read_only=True)
#    
#    """serializers.SerializerMethodField() es un campo especial de Django REST 
#    Framework que permite agregar campos calculados o personalizados a un 
#    serializer sin que existan como atributos reales en el modelo."""
#    nombre_cliente = serializers.SerializerMethodField()
#
#    class Meta:
#        model = Valoracion
#        fields = "__all__"
#    
#    def get_nombre_cliente(self, obj):
#        """Devuelve el nombre completo del cliente"""
#        if obj.cliente and obj.cliente.usuario:
#            return f"{obj.cliente.usuario.first_name} {obj.cliente.usuario.last_name}"
#        return "Usuario Anónimo"



class ValoracionSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar y editar valoraciones.
    """
    #Obtenemos el nombre de la pieza asociada a la valoración
    #con el campo personalizado 'nombre_pieza'  
    nombre_pieza = serializers.CharField(source='pieza.nombre', read_only=True)
    nombre_cliente = serializers.CharField(source='cliente.usuario.first_name', read_only=True)
    

    
    class Meta:
        model = Valoracion
        fields = [
            'id',
            'pieza_id',
            'nombre_pieza',
            'nombre_cliente',
            'puntuacion',
            'titulo',
            'comentario',
            'fecha_valoracion',
            'cliente'
        ]
        #Evitamos que se puedan modificar estos campos
        read_only_fields = ['id', 'pieza', 'nombre_pieza', 'nombre_cliente', 'cliente', 'fecha_valoracion']





    def validate_puntuacion(self, value):
        """
        Validar que la puntuación esté entre 1 y 5
        """
        if value < 1 or value > 5:
            raise serializers.ValidationError(
                "La puntuación debe estar entre 1 y 5."
            )
        return value

    def validate_titulo(self, value):
        """
        Validar que el título no esté vacío
        """
        if not value or len(value.strip()) <= 1:
            raise serializers.ValidationError(
                "El título no puede estar vacío o debe tener más de 1 carácter."
            )
        return value

    def validate_comentario(self, value):
        """
        Validar que el comentario no esté vacío
        """
        if not value or len(value.strip()) <= 1:
            raise serializers.ValidationError(
                "El comentario no puede estar vacío o debe tener más de 1 carácter."
            )
        return value

class ListaDeseosPiezaSerializer(serializers.HyperlinkedModelSerializer):
    pieza = PiezaSerializer(read_only=True)

    class Meta:
        model = ListaDeseosPieza
        fields = "__all__"


class ListaDeseosSerializer(serializers.HyperlinkedModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    items = ListaDeseosPiezaSerializer(many=True, read_only=True)

    class Meta:
        model = ListaDeseos
        fields = "__all__"


# Serializers de entrada para acciones de ListaDeseos
class AgregarPiezaListaDeseosSerializer(serializers.Serializer):
    """Serializer para agregar una pieza a la lista de deseos."""
    pieza_id = serializers.IntegerField(
        required=True,
        help_text="ID de la pieza a agregar a la lista de deseos"
    )


class EliminarPiezaListaDeseosSerializer(serializers.Serializer):
    """Serializer para eliminar una pieza de la lista de deseos."""
    pieza_id = serializers.IntegerField(
        required=True,
        help_text="ID de la pieza a eliminar de la lista de deseos"
    )


class PasarAlCarritoSerializer(serializers.Serializer):
    """Serializer para pasar items de la lista de deseos al carrito."""
    piezas_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="IDs de las piezas a pasar al carrito (si no se envía, pasa todas)"
    )
    eliminar_de_lista = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Si es true, elimina las piezas pasadas de la lista de deseos"
    )


# ============================================================
# MARKETING
# ============================================================

class DescuentoSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Descuento
        fields = "__all__"


class ClienteDescuentoSerializer(serializers.HyperlinkedModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    descuento = DescuentoSerializer(read_only=True)

    class Meta:
        model = ClienteDescuento
        fields = "__all__"


# ============================================================
# REGISTROS DE USUARIOS 
# ============================================================
class RegistroClienteSerializer(serializers.Serializer):
    #Creamos primero el usuario
    user_data = UsuarioSerializer()

    # #Luego Creamos el cliente con los datos de usuario
    # cliente_data = ClienteSerializer()

    def validate(self, data):
    #     """
    #     Validación general de los datos de registro
    #     """
         user_data = data.get('user_data', {})
        
    #     # Validar email
         self.validate_email(user_data.get('email'))
        
    #     # Validar teléfono
         self.validate_telefono(user_data.get('telefono'))
        
    #     # Validar fecha de nacimiento
         self.validate_fecha_nacimiento(user_data.get('fecha_nacimiento'))
        
         return data

    def validate_email(self, email):
    #     """
    #     Valida que el email tenga un formato válido
    #     """
        if not email: #email vacío
             raise serializers.ValidationError({
                 "user_data": {
                     "email": "El email es obligatorio."
                 }
             })
        
    #     # Crea una instancia para validar formato de email
        email_validator = EmailValidator()
        try:
             email_validator(email)
        except Exception:
             raise serializers.ValidationError({
                 "user_data": {
                     "email": "El formato del email no es válido."
                 }
             })
        
    #     # Verificar que el email no esté ya registrado
        if Usuario.objects.filter(email=email).exists():
             raise serializers.ValidationError({
                 "user_data": {
                     "email": "Este email ya está registrado."
                 }
             })

    def validate_telefono(self, telefono):
        """
        Valida que el teléfono tenga entre 9 y 15 dígitos
        """
        if not telefono:
            raise serializers.ValidationError({
                "user_data": {
                    "telefono": "El teléfono es obligatorio."
                }
            })
        
        # Eliminar espacios y caracteres especiales para contar solo dígitos
        digitos = ''.join(filter(str.isdigit, str(telefono)))
        
        if len(digitos) < 9 or len(digitos) > 15:
            raise serializers.ValidationError({
                "user_data": {
                    "telefono": "El teléfono debe tener entre 9 y 15 dígitos."
                }
            })

    def validate_fecha_nacimiento(self, fecha_nacimiento):
        """
        Valida que la fecha de nacimiento sea válida y en el pasado
        """
        if not fecha_nacimiento:
            raise serializers.ValidationError({
                "user_data": {
                    "fecha_nacimiento": "La fecha de nacimiento es obligatoria."
                }
            })
        
        # Verificar que la fecha no sea en el futuro
        hoy = timezone.now().date()
        if fecha_nacimiento > hoy:
            raise serializers.ValidationError({
                "user_data": {
                    "fecha_nacimiento": "La fecha de nacimiento no puede ser en el futuro."
                }
            })
        
        # Verificar que sea mayor de 18 años (opcional, ajusta según tu lógica de negocio)
        edad_minima_fecha = date(hoy.year - 18, hoy.month, hoy.day)
        if fecha_nacimiento > edad_minima_fecha:
            raise serializers.ValidationError({
                "user_data": {
                    "fecha_nacimiento": "Debes ser mayor de 18 años para registrarte."
                }
            })

    def create(self, validated_data):
        #Separamos los datos de usuario y cliente
        user_data = validated_data.pop("user_data") 
        #cliente_data = validated_data.pop("cliente_data") # Hasheamos el password

        #Creamos el usuario (desempaquetando con **)
        password = user_data.pop("password")
        user = Usuario.objects.create(rol=Usuario.CLIENTE, **user_data)
        user.set_password(password)
        user.save()

        #Cliente.objects.create(usuario=user, **cliente_data)
        Cliente.objects.create(usuario=user)
    
        return {
             "user_data": user,
    
        }
