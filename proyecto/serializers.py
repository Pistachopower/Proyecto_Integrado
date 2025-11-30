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
            'email',
            'password',
            'date_joined',
            'is_staff',
        ]


class ClienteSerializer(serializers.ModelSerializer): #HyperlinkedModelSerializer: sirve para crear los enlaces en la API
    usuario = UsuarioSerializer(read_only=True) #muestro los datos del usuario asociado al cliente

    class Meta:
        model = Cliente
        fields = "__all__"


class TiendaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tienda
        fields = "__all__"


class VendedorSerializer(serializers.HyperlinkedModelSerializer):
    usuario = UsuarioSerializer(read_only=True)
    tienda = TiendaSerializer(read_only=True)

    class Meta:
        model = Vendedor
        fields = "__all__"


# ============================================================
# PIEZAS E INVENTARIO
# ============================================================

class PiezaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Pieza
        fields = "__all__"


class InventarioSerializer(serializers.HyperlinkedModelSerializer):
    pieza = PiezaSerializer(read_only=True)
    tienda = TiendaSerializer(read_only=True)

    class Meta:
        model = Inventario
        fields = "__all__"


# ============================================================
# PEDIDOS / LINEAS DE PEDIDO
# ============================================================

class LineaPedidoSerializer(serializers.HyperlinkedModelSerializer):
    pieza = PiezaSerializer(read_only=True)

    class Meta:
        model = LineaPedido
        fields = "__all__"


class PedidoSerializer(serializers.HyperlinkedModelSerializer):
    cliente = ClienteSerializer(read_only=True)
    tienda = TiendaSerializer(read_only=True)
    vendedor = VendedorSerializer(read_only=True)
    lineas_pedido = LineaPedidoSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = "__all__"


# ============================================================
# METODOS DE PAGO
# ============================================================

class MetodoPagoSerializer(serializers.HyperlinkedModelSerializer):
    cliente = ClienteSerializer(read_only=True)

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
            "cliente_data": cliente_data  # opcional: puedes serializar también el cliente si quieres
        }




