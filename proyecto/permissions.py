from rest_framework import permissions
from proyecto.models import Usuario


def es_jefe(user):    
    # 1. Usamos getattr por si acaso el usuario no tiene atributo 'rol' 
    es_empleado_admin_tienda = getattr(user, 'rol', None) == Usuario.EMPLEADO or getattr(user, 'rol', None) == Usuario.ADMINISTRADOR
    
    return es_empleado_admin_tienda
    

class SoloAdmin(permissions.BasePermission):
    """
    Nadie entra aquí a menos que sea Admin, Staff o Empleado.
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
    

class SoloVerPiezasLineaPedido(permissions.BasePermission):
    """
    SOLO VER LÍNEAS DE PEDIDO y Piezas.
    Permite ver las líneas de pedido, pero no modificarlas.
    """

    def has_permission(self, request, view):
        # Permitir solo métodos seguros (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        # Permitir solo métodos seguros (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        return False
    



class PermisoGestionInventario(permissions.BasePermission):
    """
    - ADMINISTRADOR: 
    """

    def has_permission(self, request, view):
        # 1. Obtenemos el rol del usuario de forma segura
        rol = getattr(request.user, 'rol', None)

        # 2. Si es ADMINISTRADOR -> Acceso TOTAL
        if rol == Usuario.ADMINISTRADOR:
            return True

        # 3. Si es EMPLEADO -> Revisamos qué quiere hacer
        if rol == Usuario.EMPLEADO:
            
            # Si intenta CREAR (POST) -> PROHIBIDO 
            if request.method == 'POST':
                return False
            # Si intenta BORRAR (DELETE) -> PROHIBIDO 
            # (Aunque DELETE suele ir a has_object_permission, lo paramos aquí también por si acaso)
            if request.method == 'DELETE':
                return False
            
            # Si es GET (Ver), PUT o PATCH (Editar) -> ADELANTE 
            return True

        # 4. Cualquier otro (Cliente) -> FUERA
        return False

    def has_object_permission(self, request, view, obj):
        # 1. Obtenemos el rol
        rol = getattr(request.user, 'rol', None)

        # 2. Si es ADMINISTRADOR -> Acceso TOTAL
        if rol == Usuario.ADMINISTRADOR:
            return True

        # 3. Si es EMPLEADO
        if rol == Usuario.EMPLEADO:
            # Si intenta BORRAR (DELETE) -> PROHIBIDO 
            if request.method == 'DELETE':
                return False
            
            # Si es Editar (PUT/PATCH) o Ver (GET) -> ADELANTE 
            return True

        return False