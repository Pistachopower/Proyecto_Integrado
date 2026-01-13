from datetime import date
from rest_framework import serializers
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
        fields = "__all__"





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
        
        # Simplificar Tienda (Solo nombre)
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
        if instance.pagos.exists():
            raise serializers.ValidationError({"detail": "No se puede eliminar este método de pago porque tiene historial de pagos asociados."})

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

class DevolucionSerializer(serializers.HyperlinkedModelSerializer):
    linea_pedido = LineaPedidoSerializer(read_only=True)
    cliente = ClienteSerializer(read_only=True)

    class Meta:
        model = Devolucion
        fields = "__all__"


class ValoracionSerializer(serializers.HyperlinkedModelSerializer):
    pieza = PiezaSerializer(read_only=True)
    cliente = ClienteSerializer(read_only=True)

    class Meta:
        model = Valoracion
        fields = "__all__"


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

    #Luego Creamos el cliente con los datos de usuario
    cliente_data = ClienteSerializer()

    def create(self, validated_data):
        #Separamos los datos de usuario y cliente
        user_data = validated_data.pop("user_data") 
        cliente_data = validated_data.pop("cliente_data") # Hasheamos el password

        #Creamos el usuario (desempaquetando con **)
        password = user_data.pop("password")
        user = Usuario.objects.create(rol=Usuario.CLIENTE, **user_data)
        user.set_password(password)
        user.save()

        Cliente.objects.create(usuario=user, **cliente_data)

        return {
            "user_data": user,
            "cliente_data": cliente_data 
        }
