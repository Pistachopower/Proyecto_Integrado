from django.db import models

class Producto(models.Model):
    nombre= models.CharField(max_length=100)
    version= models.CharField(max_length=100)
    referencia= models.CharField(max_length=100)
    ESTADO = [("N", "Nueva"), ("R", "Recuperada"), ("REC", "Reconstruida")]
    estado = models.CharField(max_length=3, choices=ESTADO)
    descripcion= models.TextField()
    marca= models.CharField(max_length=100)
    precio= models.FloatField(default=1.0) 
    anio= models.IntegerField()
    
    def __str__(self):
        return self.nombre
