from django.utils import timezone
from .models import Descuento, ClienteDescuento, Pedido

def asignar_descuento_fidelidad(cliente):
    """
    Asigna un descuento fijo de 10€ al cliente si tiene 4 o más pedidos y nunca ha recibido este descuento.
    Solo se asigna si el descuento está vigente (fecha_inicio <= hoy <= fecha_fin).
    Retorna True si se asignó, False si no.
    """
    descuento = Descuento.objects.filter(
        tipo=Descuento.FIJO,
        valor=10,
        estado=Descuento.ACTIVO
    ).first()
    if not descuento:
        return False  # No existe el descuento

    hoy = timezone.now().date()
    # Validar vigencia del descuento de forma explícita
    vigente = descuento.fecha_inicio <= hoy and hoy <= descuento.fecha_fin
    if not vigente:
        return False  # El descuento no está vigente

    pedidos_count = Pedido.objects.filter(cliente=cliente).count()
    ya_tiene = ClienteDescuento.objects.filter(cliente=cliente, descuento=descuento).exists()
    if pedidos_count >= 4 and not ya_tiene:
        ClienteDescuento.objects.create(
            cliente=cliente,
            descuento=descuento,
            fecha_asignado=hoy,
            veces_usado=0
        )
        return True
    return False
