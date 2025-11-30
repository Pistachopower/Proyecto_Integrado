Cada vez que trabajas con el proyecto
Activar el entorno virtual:
source myvenv/bin/activate

Activar el contenedor:
docker ps
docker start NOMBRE_CONTENEDOR

Ve a la BD de Postgress e inicia el servicio

De acuerdo a los requisitos, se usa PostgreSQL como base de datos para el proyecto Django, porque 
queremos agregar imagenes, pdf y otros tipos de docuementos. 

En Visual Studio Code descargamos la siguiente extension para visualizar y editar datos:
Database Client JDBC

Usamos un contenedor Docker para levantar PostgreSQL de manera sencilla y aislada.


La instalacion de psycopg2-binary~=2.9.9 #conexion con postgresql 
se hizo con esto: 

Docker
https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04-es

Docker Compose
https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-ubuntu-20-04-es

Creamos un archivo docker-compose.yml con las configuraciones necesarias para levantar un contenedor con PostgreSQL.

Borrar BD
En tal caso, que haya que hacer un cambio en los modelos debes hacer los siguientes pasos:
Detener todos los contenedores con el comando:
    docker stop NOMBRE_CONTENEDOR

Eliminamos los contenedores como los volumenes asociados:
    docker system prune -a --volumes

Hay que aplicar este comando cada ves que se quiera aplicar cambios o trabajar de nuevo con ella mediante el archivo de configuracion yml en docker compose:
    docker compose up -d

Para iniciarlo nuevamente
sudo docker start nombreContenedor 

Ejecutar script de poblacion Faker: python manage.python manage.py shell < proyecto/poblador_datos_falsos.py

Usuario Postgres: 
Usuario: postgres
Contraseña: postgres

Otra forma de actualizar cambios en tus modelos con la bd
Vas a todas las tablas y las eliminas 

Abres la terminal y aplicar: 
    python manage.python manage.py shell < proyecto/poblador_datos_falsos.py

Hacer la migracion:
    python manage.py migrate


Crear un entorno virtual
Colocamos el siguiente comando: pip install python-dotenv

En el fichero requirements.txt agregamos la siguiente línea:
python-dotenv~=1.2.1 #manejo de variables de entorno

Creamos un fichero con extensión .env en la raiz del proyecto,
dentro del fichero agregamos los parametros de configuracion de 
de la bd y otros datos como la autenticacion.

Ir a settings.py de mysite y agregar lo siguiente:
Ejemplo de la configuracion personalizada de la BD con Postgres
```{python}
from dotenv import load_dotenv
import os
load_dotenv()

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_NAME'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': os.getenv('POSTGRES_PORT'), 
    }
}
```

Luego agregar los datos de configuración al archivo .env 

