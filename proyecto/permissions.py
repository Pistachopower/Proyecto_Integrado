from rest_framework import permissions
from proyecto.models import Usuario

#Permisos empleados
class PermisoSoloVerPieza(permissions.BasePermission):
    """
    - ADMINISTRADOR: acceso total a piezas.
    - EMPLEADO, CLIENTE y cualquier usuario: solo puede ver piezas (GET, HEAD, OPTIONS).
    """

    def has_permission(self, request, view):
        rol = getattr(request.user, 'rol', None)

        # ADMINISTRADOR: acceso total
        if rol == Usuario.ADMINISTRADOR:
            return True

        # EMPLEADO, CLIENTE y cualquier usuario: solo métodos seguros (ver)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Para cualquier otro caso: denegar
        return False

    def has_object_permission(self, request, view, obj):
        # Misma lógica que has_permission
        return self.has_permission(request, view)
    
class PermisoSoloVerEditarPropioUsuario(permissions.BasePermission):
    """
    - ADMINISTRADOR: acceso total a usuarios.
    - EMPLEADO y CLIENTE: solo pueden ver, editar o borrar su propio usuario.
    - Otros: sin acceso.
    """

    def has_permission(self, request, view):
        rol = getattr(request.user, 'rol', None)

        # ADMINISTRADOR: acceso total
        if rol == Usuario.ADMINISTRADOR:
            return True

        # EMPLEADO y CLIENTE: pueden acceder a la vista, el objeto se controla abajo
        if rol in [Usuario.EMPLEADO, Usuario.CLIENTE]:
            return True

        # Otros: sin acceso
        return False

    def has_object_permission(self, request, view, obj):
        rol = getattr(request.user, 'rol', None)

        # ADMINISTRADOR: acceso total
        if rol == Usuario.ADMINISTRADOR:
            return True

        # EMPLEADO y CLIENTE: solo pueden ver/editar/borrar su propio usuario
        if rol in [Usuario.EMPLEADO, Usuario.CLIENTE]:
            return obj == request.user

        # Otros: sin acceso
        return False
    
class PermisoSoloVerEditarPropioEmpleado(permissions.BasePermission):
    """
    - ADMINISTRADOR: acceso total a empleados.
    - EMPLEADO: solo puede ver y editar sus propios datos.
    - Otros: sin acceso.
    """

    def has_permission(self, request, view):
        rol = getattr(request.user, 'rol', None)
        if rol == Usuario.ADMINISTRADOR:
            return True
        if rol == Usuario.EMPLEADO:
            # Puede ver y editar, pero el objeto se controla abajo
            return request.method in permissions.SAFE_METHODS or request.method in ['PUT', 'PATCH']
        return False

    def has_object_permission(self, request, view, obj):
        rol = getattr(request.user, 'rol', None)
        if rol == Usuario.ADMINISTRADOR:
            return True
        if rol == Usuario.EMPLEADO:
            # Solo puede ver/editar su propio objeto
            return obj.usuario == request.user
        return False


class PermisoSoloVerTienda(permissions.BasePermission):
    """
    - ADMINISTRADOR: acceso total a tiendas.
    - EMPLEADO y CLIENTE: solo pueden ver tiendas (GET, HEAD, OPTIONS), no crear ni eliminar.
    - Otros: sin acceso.
    """

    def has_permission(self, request, view):
        rol = getattr(request.user, 'rol', None)

        # ADMINISTRADOR: acceso total
        if rol == Usuario.ADMINISTRADOR:
            return True

        # EMPLEADO y CLIENTE: solo métodos seguros (ver)
        if rol in [Usuario.EMPLEADO, Usuario.CLIENTE] and request.method in permissions.SAFE_METHODS:
            return True

        # Otros: sin acceso
        return False

    def has_object_permission(self, request, view, obj):
        # Misma lógica que has_permission
        return self.has_permission(request, view)
    

class EsDuenioLineaPedido(permissions.BasePermission):
    """
    - ADMIN y EMPLEADO: Pueden ver todas las líneas.
    - CLIENTE: Solo puede ver las líneas de sus propios pedidos.
    """

    def has_permission(self, request, view):
        # 1. Dejamos entrar a cualquier usuario autenticado a la vista.
        # (El filtro real de seguridad se hará en get_queryset en la vista)
        if request.user.is_authenticated:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        rol = getattr(request.user, 'rol', None)

        # 1. Admin y Empleado tienen pase libre para ver detalles
        if rol in [Usuario.ADMINISTRADOR, Usuario.EMPLEADO]:
            return True

        # 2. Cliente: Verificamos la cadena de relación
        # LineaPedido -> Pedido -> Cliente -> Usuario
        return obj.pedido.cliente.usuario == request.user
    

class PermisoEmpleadoClienteEditarEstadoDireccionPedido(permissions.BasePermission):
    """
    - ADMINISTRADOR: acceso total a pedidos.
    - EMPLEADO: puede ver pedidos y editar solo el estado y dirección.
    - CLIENTE: puede ver solo sus propios pedidos.
    - Otros: sin acceso.
    """

    def has_permission(self, request, view):
        rol = getattr(request.user, 'rol', None)
        # ADMINISTRADOR: acceso total
        if rol == Usuario.ADMINISTRADOR:
            return True
        # EMPLEADO y CLIENTE: pueden ver (GET, HEAD, OPTIONS)
        if rol in [Usuario.EMPLEADO, Usuario.CLIENTE] and request.method in permissions.SAFE_METHODS:
            return True
        # EMPLEADO: puede editar (PUT/PATCH) (ajusta según tu lógica)
        if rol == Usuario.EMPLEADO and request.method in ['PUT', 'PATCH']:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        rol = getattr(request.user, 'rol', None)
        # ADMINISTRADOR: acceso total
        if rol == Usuario.ADMINISTRADOR:
            return True
        # CLIENTE: solo puede ver su propio pedido
        if rol == Usuario.CLIENTE and request.method in permissions.SAFE_METHODS:
            return obj.cliente.usuario == request.user
        # EMPLEADO: puede ver todos, editar solo estado/dirección (ajusta según tu lógica)
        if rol == Usuario.EMPLEADO and request.method in permissions.SAFE_METHODS:
            return True
        # Otros: sin acceso
        return False
    

#class PermisoEliminarMetodoPagoSoloAdmin(permissions.BasePermission):
#    """
#    - ADMINISTRADOR: acceso total a métodos de pago.
#    - EMPLEADO y CLIENTE: solo pueden ver métodos de pago (GET, HEAD, OPTIONS), no pueden eliminar, crear ni editar.
#    """
#
#    def has_permission(self, request, view):
#        rol = getattr(request.user, 'rol', None)
#
#        # ADMINISTRADOR: acceso total
#        if rol == Usuario.ADMINISTRADOR:
#            return True
#
#        # EMPLEADO y CLIENTE: solo métodos seguros (ver)
#        if rol in [Usuario.EMPLEADO, Usuario.CLIENTE] and request.method in permissions.SAFE_METHODS:
#            return True
#
#        # Otros: sin acceso
#        return False
#
#    def has_object_permission(self, request, view, obj):
#        # Misma lógica que has_permission
#        return self.has_permission(request, view)

#class PermisoEliminarTarjetaSoloAdmin(permissions.BasePermission):
#    """
#    - ADMINISTRADOR: acceso total a tarjetas.
#    - EMPLEADO y CLIENTE: solo pueden ver tarjetas (GET, HEAD, OPTIONS), no pueden eliminar, crear ni editar.
#    """
#
#    def has_permission(self, request, view):
#        rol = getattr(request.user, 'rol', None)
#
#        if rol == Usuario.ADMINISTRADOR:
#            return True
#        if rol in [Usuario.EMPLEADO, Usuario.CLIENTE] and request.method in permissions.SAFE_METHODS:
#            return True
#        return False
#
#    def has_object_permission(self, request, view, obj):
#        return self.has_permission(request, view)




class EsDuenioMetodoPago(permissions.BasePermission):
    """
    Controla el acceso a Métodos de Pago, Tarjetas, Cuentas y Billeteras.
    - ADMINISTRADOR: Acceso total.
    - CLIENTE: Solo puede acceder si el método de pago le pertenece.
    """

    def has_permission(self, request, view):
        # 1. Autenticación obligatoria
        if not request.user.is_authenticated:
            return False
        
        # 2. Permitimos entrar a la vista (el filtro real se hace en get_queryset)
        return True

    def has_object_permission(self, request, view, obj):
        rol = getattr(request.user, 'rol', None)

        # 1. El Admin entra siempre
        if rol == Usuario.ADMINISTRADOR:
            return True
        
        # 2. El Cliente solo entra si el objeto (Tarjeta/Cuenta) es suyo
        # Asumimos que el modelo tiene el campo 'cliente' o lo hereda
        return obj.cliente.usuario == request.user




class PermisoEliminarCuentaBancariaSoloAdmin(permissions.BasePermission):
    """
    - ADMINISTRADOR: acceso total a cuentas bancarias.
    - EMPLEADO y CLIENTE: solo pueden ver cuentas bancarias (GET, HEAD, OPTIONS), no pueden eliminar, crear ni editar.
    """

    def has_permission(self, request, view):
        rol = getattr(request.user, 'rol', None)

        if rol == Usuario.ADMINISTRADOR:
            return True
        if rol in [Usuario.EMPLEADO, Usuario.CLIENTE] and request.method in permissions.SAFE_METHODS:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)


class PermisoEliminarBilleteraDigitalSoloAdmin(permissions.BasePermission):
    """
    - ADMINISTRADOR: acceso total a billeteras digitales.
    - EMPLEADO y CLIENTE: solo pueden ver billeteras digitales (GET, HEAD, OPTIONS), no pueden eliminar, crear ni editar.
    """

    def has_permission(self, request, view):
        rol = getattr(request.user, 'rol', None)

        if rol == Usuario.ADMINISTRADOR:
            return True
        if rol in [Usuario.EMPLEADO, Usuario.CLIENTE] and request.method in permissions.SAFE_METHODS:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)

class PermisoEmpleadoEditarEstadoPago(permissions.BasePermission):
    """
    - ADMINISTRADOR: acceso total a pagos.
    - EMPLEADO: puede ver pagos (GET, HEAD, OPTIONS) y editar solo el campo 'estado'.
    - Otros: sin acceso.
    """

    def has_permission(self, request, view):
        rol = getattr(request.user, 'rol', None)

        # ADMINISTRADOR: acceso total
        if rol == Usuario.ADMINISTRADOR:
            return True

        # EMPLEADO: puede ver y editar (PATCH/PUT) pagos, edición se controla abajo
        if rol == Usuario.EMPLEADO:
            if request.method in permissions.SAFE_METHODS:
                return True
            if request.method in ['PUT', 'PATCH']:
                return True
            # No puede crear ni borrar
            return False

        # Otros: sin acceso
        return False

    def has_object_permission(self, request, view, obj):
        rol = getattr(request.user, 'rol', None)

        # ADMINISTRADOR: acceso total
        if rol == Usuario.ADMINISTRADOR:
            return True

        # EMPLEADO: solo puede editar el campo 'estado'
        if rol == Usuario.EMPLEADO:
            if request.method in permissions.SAFE_METHODS:
                return True
            if request.method in ['PUT', 'PATCH']:
                allowed_fields = {'estado'}
                fields = set(request.data.keys())
                return fields.issubset(allowed_fields)
            return False

        # Otros: sin acceso
        return False
    


#Permisos clientes
class PermisoSoloVerEditarPropioCliente(permissions.BasePermission):
    """
    - ADMINISTRADOR: acceso total a clientes.
    - CLIENTE: solo puede ver, editar o borrar sus propios datos de cliente.
    - Otros: sin acceso.
    """

    def has_permission(self, request, view):
        rol = getattr(request.user, 'rol', None)

        # ADMINISTRADOR: acceso total
        if rol == Usuario.ADMINISTRADOR:
            return True

        # CLIENTE: puede acceder, el objeto se controla abajo
        if rol == Usuario.CLIENTE:
            return True

        # Otros: sin acceso
        return False

    def has_object_permission(self, request, view, obj):
        rol = getattr(request.user, 'rol', None)

        # ADMINISTRADOR: acceso total
        if rol == Usuario.ADMINISTRADOR:
            return True

        # CLIENTE: solo puede ver/editar/borrar su propio objeto cliente
        if rol == Usuario.CLIENTE:
            # Suponiendo que el modelo Cliente tiene un campo 'usuario' que es ForeignKey a Usuario
            return obj.usuario == request.user

        # Otros: sin acceso
        return False

class PermisoInventarioSinAccesoCliente(permissions.BasePermission):
    """
    - CLIENTE: no puede acceder a inventario.
    - Otros: acceso total.
    """

    def has_permission(self, request, view):
        rol = getattr(request.user, 'rol', None)
        if rol == Usuario.CLIENTE:
            return False
        return True


class EsDuenioDevolucion(permissions.BasePermission):
    """
    - ADMINISTRADOR y EMPLEADO: Ven todo.
    - CLIENTE: Solo ve sus propias devoluciones.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        rol = getattr(request.user, 'rol', None)

        # 1. Admin y Empleado (gestión) tienen acceso total
        if rol in [Usuario.ADMINISTRADOR, Usuario.EMPLEADO]:
            return True

        # 2. Cliente: Verificamos el campo directo 'cliente'
        return obj.cliente.usuario == request.user
    



class EsDuenioListaDeseos(permissions.BasePermission):
    """
    - ADMIN: Acceso total.
    - CLIENTE: Solo ve su propia ListaDeseos (cabecera).
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # 1. Admin entra siempre
        rol = getattr(request.user, 'rol', None)
        if rol == Usuario.ADMINISTRADOR:
            return True

        # 2. Cliente: Verificamos si la lista es suya
        # Ruta: ListaDeseos -> Cliente -> Usuario
        return obj.cliente.usuario == request.user


class EsDuenioItemListaDeseos(permissions.BasePermission):
    """
    - ADMIN: Acceso total.
    - CLIENTE: Solo ve/edita items dentro de SU lista de deseos.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        rol = getattr(request.user, 'rol', None)
        if rol == Usuario.ADMINISTRADOR:
            return True

        # 2. Cliente: Verificamos la cadena de propiedad
        # Ruta: ListaDeseosPieza -> ListaDeseos -> Cliente -> Usuario
        return obj.lista_deseos.cliente.usuario == request.user
    
from rest_framework import permissions
from proyecto.models import Usuario

class PermisoGestionDescuentos(permissions.BasePermission):
    """
    Controla el acceso al modelo 'Descuento' (La configuración global).
    - ADMIN: Control total (CRUD).
    - EMPLEADO: Solo lectura (para saber qué promos existen).
    - CLIENTE: SIN ACCESO. El cliente no debe ver la lista de todos los códigos posibles.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        rol = getattr(request.user, 'rol', None)

        # Admin total
        if rol == Usuario.ADMINISTRADOR:
            return True
        
        # Empleado solo lectura
        if rol == Usuario.EMPLEADO and request.method in permissions.SAFE_METHODS:
            return True

        # Cliente (y otros): Bloqueado
        return False

    def has_object_permission(self, request, view, obj):
        # Misma lógica que has_permission
        return self.has_permission(request, view)


class PermisoClienteDescuento(permissions.BasePermission):
    """
    Controla el acceso a 'ClienteDescuento' (La billetera de cupones).
    - ADMIN: Total.
    - EMPLEADO: Solo lectura (para verificar si un cliente tiene descuento).
    - CLIENTE: Solo puede ver SUS propios descuentos asignados.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return True

    def has_object_permission(self, request, view, obj):
        rol = getattr(request.user, 'rol', None)

        if rol == Usuario.ADMINISTRADOR:
            return True
        
        if rol == Usuario.EMPLEADO:
            return request.method in permissions.SAFE_METHODS
            
        if rol == Usuario.CLIENTE:
            # Solo puede ver, y solo si es SU descuento
            if request.method in permissions.SAFE_METHODS:
                return obj.cliente.usuario == request.user
        
        return False