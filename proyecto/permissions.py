from rest_framework import permissions
from proyecto.models import *


def es_jefe(user):    
    # 1. Usamos getattr por si acaso el usuario no tiene atributo 'rol' 
    es_empleado_admin_tienda = getattr(user, 'rol', None) == Usuario.EMPLEADO or getattr(user, 'rol', None) == Usuario.ADMINISTRADOR
    
    return es_empleado_admin_tienda
    

class SoloAdminOEmpleado(permissions.BasePermission):
    """
    Permite acceso solo a Administradores y Empleados.
    """
    
    def has_permission(self, request, view):
        # Pregunta: ¿Eres jefe?
        return es_jefe(request.user)

    def has_object_permission(self, request, view, obj):
        # Si pasó la primera puerta, verificamos de nuevo por seguridad.
        return es_jefe(request.user)


class EsDuenioUsuario(permissions.BasePermission):
    """
    Sirve para cuando alguien quiere ver/editar su propia cuenta de Login (Usuario).
    """

    def has_permission(self, request, view):
        # 1. Si eres jefe, pasas siempre.
        if es_jefe(request.user):
            return True

        # 2. Si intentas ver la LISTA COMPLETA de usuarios (action='list'),
        # y no eres jefe, no puedes ver a los demás.
        if view.action == 'list':
            return False
        
        # 3. Un usuario normal no puede crear otros usuarios.
        if view.action == 'create':
            return False

        return True

    def has_object_permission(self, request, view, obj):
        # 1. Si eres jefe puede entrar.
        if es_jefe(request.user):
            return True

        # 2. Si no eres jefe, solo puedes entrar si tú eres ese usuario.
        # Comparamos el objeto (obj) con el usuario que hace la petición (request.user).
        return obj == request.user


class EsDuenioDeObjeto(permissions.BasePermission):
    """
    Un Pedido tiene un Cliente, y ese Cliente tiene un Usuario.
    Ruta: Pedido -> Cliente -> Usuario
    """

    def has_permission(self, request, view):
        # (Misma lógica de la puerta principal que arriba)
        if es_jefe(request.user):
            return True
        
        if view.action == 'list':
            return False
            
        return True
     
    def has_object_permission(self, request, view, obj):        
        # 1. El jefe entra donde quiere.
        if es_jefe(request.user):
            return True
        try:
            return obj.cliente.usuario == request.user
        except AttributeError as errorNUevo:
            # Si el objeto no tiene campo 'cliente', prohibimos el paso por seguridad.
            print(f"Error de permiso: {errorNUevo}")
            return False


class EsDuenioDirecto(permissions.BasePermission):
    """
    PROPIEDAD DIRECTA (Ej. Modelo Cliente o Vendedor)
    Sirve para modelos que tienen el campo 'usuario' directamente.
    Ruta: Cliente -> Usuario
    """
    
    def has_permission(self, request, view):
        if es_jefe(request.user): return True
        if view.action == 'list': return False
        return True

    def has_object_permission(self, request, view, obj):
        if es_jefe(request.user): return True
        
        # Aquí 'obj' es directamente el Cliente o el Vendedor.
        # Verificamos si su campo 'usuario' eres tú.
        return obj.usuario == request.user
    

class EsDuenioPorMetodoPago(permissions.BasePermission):
    """
    Para Tarjeta, CuentaBancaria y BilleteraDigital.
    Estos modelos no tienen 'cliente' directamente, sino que van a través de MetodoPago.
    Ruta: Tarjeta -> MetodoPago -> Cliente -> Usuario
    """

    def has_permission(self, request, view):
        if es_jefe(request.user):
            return True
        if view.action == 'list':
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if es_jefe(request.user):
            return True
        try:
            return obj.metodo_pago.cliente.usuario == request.user
        except AttributeError as error:
            print(f"Error de permiso: {error}")
            return False


class EsDuenioPorPedido(permissions.BasePermission):
    """
    Para Pago.
    El Pago no tiene 'cliente' directamente, sino que va a través del Pedido.
    Ruta: Pago -> Pedido -> Cliente -> Usuario
    """

    def has_permission(self, request, view):
        if es_jefe(request.user):
            return True
        if view.action == 'list':
            return False
        return True

    def has_object_permission(self, request, view, obj):
        if es_jefe(request.user):
            return True
        try:
            return obj.pedido.cliente.usuario == request.user
        except AttributeError as error:
            print(f"Error de permiso: {error}")
            return False


class SoloVerPiezasLineaPedido(permissions.BasePermission):
    """
    SOLO VER LÍNEAS DE PEDIDO y Piezas.
    Permite ver las líneas de pedido, pero no modificarlas.
    Los jefes (admin/empleado) tienen acceso completo.
    """

    def has_permission(self, request, view):
        # Los jefes pueden hacer cualquier operación
        if es_jefe(request.user):
            return True
        # Usuarios normales: solo métodos seguros (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if es_jefe(request.user):
            return True
        
        return obj.pedido.cliente.usuario == request.user
    

class PermisoGestionInventario(permissions.BasePermission):
    """
    Permiso para gestión de inventario (Piezas, Categorías, etc.).
    - Cualquier usuario (incluido anónimo): solo lectura (GET, HEAD, OPTIONS)
    - EMPLEADO: lectura + edición (PUT/PATCH), pero NO crear (POST) ni borrar (DELETE)
    - ADMINISTRADOR: acceso total
    """

    def has_permission(self, request, view):
        # 1. Cualquier usuario puede VER (métodos seguros)
        if request.method in permissions.SAFE_METHODS:
            return True

        # 2. Para métodos de escritura, el usuario debe estar autenticado
        if not request.user or not request.user.is_authenticated:
            return False

        # 3. Obtenemos el rol del usuario de forma segura
        rol = getattr(request.user, 'rol', None)

        # 4. Si es ADMINISTRADOR -> Acceso TOTAL
        if rol == Usuario.ADMINISTRADOR:
            return True

        # 5. Si es VENDEDOR (tiene modelo Vendedor asociado) -> acceso total a inventario
        if hasattr(request.user, 'vendedor'):
            return True

        # 6. Si es EMPLEADO -> puede editar pero NO crear ni borrar
        if rol == Usuario.EMPLEADO:
            if request.method in ('POST', 'DELETE'):
                return False
            return True

        # 7. Cualquier otro (Cliente) -> solo lectura (ya pasó arriba)
        return False

    def has_object_permission(self, request, view, obj):
        # 1. Lectura siempre permitida
        if request.method in permissions.SAFE_METHODS:
            return True

        # 2. Obtenemos el rol
        rol = getattr(request.user, 'rol', None)

        # 3. Si es ADMINISTRADOR -> Acceso TOTAL
        if rol == Usuario.ADMINISTRADOR:
            return True

        # 4. Si es VENDEDOR -> acceso total a inventario
        if hasattr(request.user, 'vendedor'):
            return True

        # 5. Si es EMPLEADO -> puede editar pero NO borrar
        if rol == Usuario.EMPLEADO:
            if request.method == 'DELETE':
                return False
            return True

        return False
    

#Permiso comentario y valoracion cliente 
class PuedeEditarValoracion(permissions.BasePermission):
    """
    Permite editar una valoración solo si:
    1. El usuario es el propietario de la valoración
    2. El usuario compró el producto (tiene LineaPedido con esa pieza)
    3. El pedido está en estado ENVIADO (3) o posterior
    Los administradores y empleados pueden gestionar cualquier valoración.
    """
    
    message = "No puedes editar esta valoración. Debes ser el propietario y tener el pedido enviado."

    def has_permission(self, request, view):
        # Los jefes (admin/empleado) pueden gestionar cualquier valoración
        if es_jefe(request.user):
            return True
        # Usuarios normales deben estar autenticados
        if not request.user or not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        # 1. Los jefes pueden gestionar cualquier valoración (ej: borrar ofensivas)
        if es_jefe(request.user):
            return True

        # 2. Verificar que es el dueño de la valoración
        if obj.cliente.usuario != request.user:
            return False
        
        # 3. Verificar que ha comprado el producto Y el pedido está ENVIADO (3) o más
        compra_existe = LineaPedido.objects.filter(
            pieza=obj.pieza,  # La misma pieza que se valora
            pedido__cliente__usuario=request.user,  # Del usuario actual
            pedido__estado__gte=Pedido.ENVIADO  # Estado >= ENVIADO (3)
        ).exists()
        
        return compra_existe
