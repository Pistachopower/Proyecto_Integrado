from django.utils import timezone
from .models import Descuento, ClienteDescuento, Pedido




def descuento_por_registro(cliente):
    """
    Asigna un descuento del 5% al cliente por registrarse.
    Solo se asigna si el descuento está vigente (fecha_inicio <= hoy <= fecha_fin).
    Retorna True si se asignó, False si no.
    """
    descuento = Descuento.objects.filter(
        tipo=Descuento.PORCENTAJE,
        valor=5,
        estado=Descuento.ACTIVO
    ).first()
    if not descuento:
        return False  # No existe el descuento

    hoy = timezone.now().date()
    # Validar vigencia del descuento de forma explícita
    vigente = descuento.fecha_inicio <= hoy and hoy <= descuento.fecha_fin
    if not vigente:
        return False  # El descuento no está vigente

    ya_tiene = ClienteDescuento.objects.filter(cliente=cliente, descuento=descuento).exists()
    if not ya_tiene:
        ClienteDescuento.objects.create(
            cliente=cliente,
            descuento=descuento,
            fecha_asignado=hoy,
            veces_usado=0
        )
        return True
    return False