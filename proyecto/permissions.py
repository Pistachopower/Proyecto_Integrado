from rest_framework import permissions
from proyecto.models import Usuario

# ==============================================================================
# 🛠️ HERRAMIENTA DE AYUDA (Para no repetir código)
# ==============================================================================

def es_jefe(user):
    """
    Función simple que nos dice si el usuario es un 'Jefe' (Admin, Staff o Empleado).
    Devuelve True si tiene poder, False si es un mortal.
    """
    # 1. ¿Es superusuario (Dios) o Staff (Admin de Django)?
    es_admin_django = user.is_staff or user.is_superuser
    
    # 2. ¿Es un empleado de la tienda (según tu modelo Usuario)?
    # Usamos getattr por si acaso el usuario no tiene atributo 'rol' (seguridad extra)
    es_empleado_tienda = getattr(user, 'rol', None) == Usuario.EMPLEADO
    
    return es_admin_django or es_empleado_tienda


# ==============================================================================
# 🔒 PERMISOS (Los Porteros de tu Discoteca/API)
# ==============================================================================

class SoloAdmin(permissions.BasePermission):
    """
    ⛔ PORTERO NIVEL 1: SOLO PERSONAL AUTORIZADO
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
    👤 PORTERO NIVEL 2: PARA EL MODELO 'USUARIO'
    Sirve para cuando alguien quiere ver/editar su propia cuenta de Login (Usuario).
    """

    def has_permission(self, request, view):
        # --- PUERTA PRINCIPAL (Entrada al edificio) ---
        
        # 1. Si eres jefe, pasas siempre.
        if es_jefe(request.user):
            return True

        # 2. Si intentas ver la LISTA COMPLETA de usuarios (action='list'),
        # y no eres jefe, ¡FUERA! No puedes ver a los demás.
        if view.action == 'list':
            return False

        # 3. Si quieres ver un detalle, editar o borrar, te dejo pasar a la siguiente puerta
        # para verificar si es TU cuenta.
        return True

    def has_object_permission(self, request, view, obj):
        # --- PUERTA DE LA HABITACIÓN (El objeto específico) ---
        # 'obj' aquí es el USUARIO que intentan tocar.

        # 1. Si eres jefe, tienes llave maestra.
        if es_jefe(request.user):
            return True

        # 2. Si no eres jefe, solo puedes entrar si TÚ eres ese usuario.
        # Comparamos el objeto (obj) con el usuario que hace la petición (request.user).
        return obj == request.user


class EsDuenioDeObjeto(permissions.BasePermission):
    """
    📦 PORTERO NIVEL 3: PARA COSAS TUYAS (Pedidos, Tarjetas, Direcciones...)
    Sirve para modelos que están conectados al usuario a través de un Cliente.
    Ejemplo: Un Pedido tiene un Cliente, y ese Cliente tiene un Usuario.
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
        # --- PUERTA DE LA HABITACIÓN ---
        
        # 1. El jefe entra donde quiere.
        if es_jefe(request.user):
            return True

        # 2. Verificamos la propiedad.
        # Aquí asumimos que el objeto (ej. Pedido) tiene un campo 'cliente',
        # y ese 'cliente' tiene un campo 'usuario'.
        try:
            return obj.cliente.usuario == request.user
        except AttributeError:
            # Si el objeto no tiene campo 'cliente', prohibimos el paso por seguridad.
            return False


class EsDuenioDirecto(permissions.BasePermission):
    """
    🏷️ PORTERO NIVEL 4: PROPIEDAD DIRECTA (Ej. Modelo Cliente o Vendedor)
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