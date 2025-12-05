from rest_framework import permissions #clase base de permisos

#Aqui definimos nuestros propios permisos personalizados
class EsDuenioUsuarioOSoloLectura(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Si la request es de solo lectura (GET), permitimos el acceso
        #if request.method in permissions.SAFE_METHODS:
            #return True

        # Comparamos el usuario de la bd con la peticion
        return (obj == request.user)
    

class EsDuenioOSoloLectura(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Si la request es de solo lectura (GET), permitimos el acceso
        if request.method in permissions.SAFE_METHODS:
            return True

        # Comparamos el usuario de la bd con la peticion
        return (obj.usuario == request.user)
