from django.contrib import admin

# Register your models here.
from .models import *
admin.site.register(Usuario)
admin.site.register(Cliente)
admin.site.register(Tienda)
admin.site.register(Vendedor)
admin.site.register(Pieza)
admin.site.register(Inventario)
admin.site.register(Pedido)
admin.site.register(LineaPedido)
admin.site.register(MetodoPago)
admin.site.register(Tarjeta)
admin.site.register(CuentaBancaria)
admin.site.register(BilleteraDigital)
admin.site.register(Pago)
admin.site.register(Devolucion)
admin.site.register(Valoracion)
admin.site.register(ListaDeseos)
admin.site.register(ListaDeseosPieza)
admin.site.register(Descuento)
admin.site.register(ClienteDescuento)



