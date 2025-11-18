from .models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework.decorators import api_view



@api_view(["GET"])
def mostrar_productos(request):
    productos = Producto.objects.all()

    
    serializer = ProductoSerializer(
        productos, many=True
    )  # parámetro many=True, para indicar que serializamos muchos valores
    return Response(serializer.data)