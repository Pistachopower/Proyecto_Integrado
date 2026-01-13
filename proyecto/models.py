from django.db import models
from django.contrib.auth.models import (
    AbstractUser,
)  # agregamos estos para la autenticacion


# ============================================================
# NIVEL 1: IDENTIDAD Y AUTENTICACIÓN
# ============================================================

class Usuario(AbstractUser):
    ADMINISTRADOR = 1
    EMPLEADO = 2
    CLIENTE = 3
    ROLES = [
        (ADMINISTRADOR, "administrador"),
        (EMPLEADO, "empleado"),
        (CLIENTE, "cliente"),
    ]

        
    rol  = models.PositiveSmallIntegerField(
        choices=ROLES, default=CLIENTE
    )
    
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    fecha_registro = models.DateField(auto_now=True)

    def __str__(self):
        return self.email



class Cliente(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="cliente"
    )

    def __str__(self):
        return f"{self.usuario.first_name} {self.usuario.last_name}"
    



class Vendedor(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="vendedor"
    )
    fecha_contratacion = models.DateField()
    comision_porcentaje = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.usuario.first_name} {self.usuario.last_name}"


class CategoriaPieza(models.Model):
    nombre = models.CharField(max_length=100)
    imagen_categoria = models.ImageField(upload_to='categorias/', blank=True, null=True)  # Para mostrar en UI
    descripcion = models.TextField()


    def __str__(self):
        return self.nombre

class Pieza(models.Model):
    NUEVO = 1
    USADO = 2
    REACONDICIONADO = 3

    ESTADO = [
        (NUEVO, "Nuevo"),
        (USADO, "Usado"),
        (REACONDICIONADO, "Reacondicionado"),
    ]

    estado  = models.PositiveSmallIntegerField(
        choices=ESTADO
    )
    nombre = models.CharField(max_length=100)
    referencia = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=50)
    marca = models.CharField(max_length=50)
    anio = models.IntegerField()
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField()
    imagen= models.ImageField(upload_to='imagenes_piezas/', blank=True, null=True)
    stock = models.IntegerField(default=0)
    categoria= models.ForeignKey(
        CategoriaPieza,
        on_delete=models.CASCADE,
        related_name="categoria_piezas",
        null=True,
    )
    

    def __str__(self):
        return self.nombre
    
    

class ImagenPieza(models.Model):
    pieza = models.ForeignKey(
        Pieza,
        on_delete=models.CASCADE,
        related_name="imagenes"
    )
    url_imagen = models.ImageField(upload_to='imagenes_piezas/', blank=True, null=True)
    descripcion = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Imagen de {self.pieza.nombre}"
    






# ============================================================
# NIVEL 3: OPERACIONES COMERCIALES
# ============================================================


class Pedido(models.Model):
    PENDIENTE = 1
    PAGADO = 2
    ENVIADO = 3
    ENTREGADO = 4
    CANCELADO = 5

    ESTADO = [
        (PENDIENTE, "Pendiente"),
        (PAGADO, "Pagado"),
        (ENVIADO, "Enviado"),
        (ENTREGADO, "Entregado"),
        (CANCELADO, "Cancelado"),
    ]

    estado  = models.PositiveSmallIntegerField(
        choices=ESTADO
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="pedidos_cliente"
    )
    vendedor = models.ForeignKey(
        Vendedor,
        on_delete=models.CASCADE,
        related_name="pedidos_vendedor"
    )
    fecha_pedido = models.DateField()
    direccion_envio = models.CharField(max_length=255)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Pedido {self.id}"


class LineaPedido(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="lineas_pedido"
    )
    pieza = models.ForeignKey(
        Pieza,
        on_delete=models.CASCADE,
        related_name="lineas_pedido"
    )
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento_aplicado = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Linea {self.id} del pedido {self.pedido.id}"


# ============================================================
# SISTEMA DE PAGOS
# ============================================================

class MetodoPago(models.Model):

    TARJETA = 1
    CUENTA = 2
    BILLETERA = 3


    TIPO_METODO = [
        (TARJETA, "Tarjeta"),
        (CUENTA, "Cuenta Bancaria"),
        (BILLETERA, "Billetera Digital")
    ]

    tipo_metodo  = models.PositiveSmallIntegerField(
        choices=TIPO_METODO
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="metodos_pago"
    )
    #tipo_metodo = models.CharField(max_length=20, choices=TIPO_METODO)
    es_predeterminado = models.BooleanField(default=False) # Indica si es el método predeterminado
    fecha_agregado = models.DateField(auto_now=True)

    def __str__(self):
        return f"{self.tipo_metodo} de {self.cliente}"


class Tarjeta(models.Model):
    VISA = 1
    MASTERCARD = 2
    AMEX = 3


    TIPO_TARJETA = [
        (VISA, "Visa"),
        (MASTERCARD, "Mastercard"),
        (AMEX, "American Express")
    ]

    tipo_tarjeta  = models.PositiveSmallIntegerField(
        choices=TIPO_TARJETA
    )


    metodo_pago = models.OneToOneField(
        MetodoPago,
        on_delete=models.CASCADE,
        related_name="tarjeta"
    )
    num_tarjeta_encriptado = models.CharField(max_length=255)
    propietario = models.CharField(max_length=100)
    fecha_caducidad = models.CharField(max_length=7)  # Formato MM/AA
    #tipo_tarjeta = models.CharField(max_length=20, choices=TIPO_TARJETA)
    moneda = models.CharField(max_length=10)


class CuentaBancaria(models.Model):
    metodo_pago = models.OneToOneField(
        MetodoPago,
        on_delete=models.CASCADE,
        related_name="cuenta_bancaria"
    )
    iban = models.CharField(max_length=255)
    banco = models.CharField(max_length=100)
    moneda = models.CharField(max_length=10)

    


class BilleteraDigital(models.Model):
    PAYPAL = 1
    STRIPE = 2
    GOOGLEPAY = 3


    BILLETERADIGITAL = [
        (PAYPAL, "PayPal"),
        (STRIPE, "Stripe"),
        (GOOGLEPAY, "Google Pay")
    ]

    proveedor  = models.PositiveSmallIntegerField(
        choices=BILLETERADIGITAL
    )

    metodo_pago = models.OneToOneField(
        MetodoPago,
        on_delete=models.CASCADE,
        related_name="billetera_digital"
    )
    email = models.EmailField()
    #proveedor = models.CharField(max_length=20, choices=BILLETERADIGITAL)



class Pago(models.Model):
    PENDIENTE = 1
    COMPLETADO = 2
    FALLIDO = 3


    ESTADO = [
        (PENDIENTE, "PENDIENTE"),
        (COMPLETADO, "COMPLETADO"),
        (FALLIDO, "FALLIDO")
    ]

    estado  = models.PositiveSmallIntegerField(
        choices=ESTADO
    )

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="pagos"
    )
    metodo_pago = models.ForeignKey(
        MetodoPago,
        on_delete=models.CASCADE,
        related_name="pagos"
    )
    fecha_pago = models.DateField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    #estado = models.CharField(max_length=20, choices=ESTADO)
    numero_transaccion = models.CharField(max_length=100)


# ============================================================
# NIVEL 4: POST-VENTA
# ============================================================

class Devolucion(models.Model):
    PENDIENTE = 1
    APROBADA = 2
    RECHAZADA = 3


    ESTADO = [
        (PENDIENTE, "Pendiente"),
        (APROBADA, "Aprobada"),
        (RECHAZADA, "Rechazada"),
    ]

    estado  = models.PositiveSmallIntegerField(
        choices=ESTADO
    )

    linea_pedido = models.ForeignKey(
        LineaPedido,
        on_delete=models.CASCADE,
        related_name="devoluciones"
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="devoluciones"
    )
    fecha_solicitud = models.DateField()
    fecha_aprobacion = models.DateField(null=True, blank=True)
    motivo = models.TextField()
    #estado = models.CharField(max_length=20, choices=ESTADO)
    cantidad_devuelta = models.IntegerField()
    monto_reembolso = models.DecimalField(max_digits=10, decimal_places=2)


class Valoracion(models.Model):
    pieza = models.ForeignKey(
        Pieza,
        on_delete=models.CASCADE,
        related_name="valoraciones"
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="valoraciones"
    )
    puntuacion = models.IntegerField()
    titulo = models.CharField(max_length=100)
    comentario = models.TextField()
    fecha_valoracion = models.DateField()


class ListaDeseos(models.Model):
    cliente = models.OneToOneField(
        Cliente,
        on_delete=models.CASCADE,
        related_name="lista_deseos"
    )
    nombre = models.CharField(max_length=100)
    fecha_creacion = models.DateField()


class ListaDeseosPieza(models.Model):
    lista_deseos = models.ForeignKey(
        ListaDeseos,
        on_delete=models.CASCADE,
        related_name="items"
    )
    pieza = models.ForeignKey(
        Pieza,
        on_delete=models.CASCADE,
        related_name="listas_deseos"
    )
    fecha_agregado = models.DateField()


# ============================================================
# NIVEL 5: MARKETING
# ============================================================

class Descuento(models.Model):
    PORCENTAJE = 1
    FIJO = 2

    TIPO = [
        (PORCENTAJE, "Porcentaje"),
        (FIJO, "Fijo"),
    ]

    tipo  = models.PositiveSmallIntegerField(
        choices=TIPO
    )

    ACTIVO = 1
    INACTIVO = 2

    ESTADO = [
        (ACTIVO, "Activo"),
        (INACTIVO, "Inactivo"),
    ]

    estado  = models.PositiveSmallIntegerField(
        choices=ESTADO
    )

    

    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    usos_maximos = models.IntegerField()
    usos_actuales = models.IntegerField()


class ClienteDescuento(models.Model):
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name="descuentos"
    )
    descuento = models.ForeignKey(
        Descuento,
        on_delete=models.CASCADE,
        related_name="clientes"
    )
    fecha_asignado = models.DateField()
    veces_usado = models.IntegerField()
