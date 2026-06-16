# Proyecto Integrado - Documentación

# Url de API - 
https://proyectointegrado-production-9570.up.railway.app/api/v1/

## 🚀 Configuración Inicial

### Requisitos Previos
- Python 3.8+
- Docker y Docker Compose
- Git

### Configuración del Entorno

1. **Clonar el repositorio**
   ```bash
   git clone [URL_DEL_REPOSITORIO]
   cd Proyecto_Integrado
   ```

2. **Crear y activar entorno virtual**
   ```bash
   # Linux/Mac
   python -m venv venv
   source venv/bin/activate
   
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

## 🐋 Configuración con Docker

### Iniciar servicios con Docker Compose
```bash
docker-compose up -d
```

### Comandos útiles de Docker
- Ver contenedores en ejecución: `docker ps`
- Iniciar un contenedor: `docker start NOMBRE_CONTENEDOR`
- Detener un contenedor: `docker stop NOMBRE_CONTENEDOR`
- Ver logs: `docker logs NOMBRE_CONTENEDOR`

## 🗄️ Base de Datos PostgreSQL

### Credenciales por defecto
- **Usuario:** postgres
- **Contraseña:** postgres
- **Base de datos:** postgres
- **Puerto:** 5432

### Configuración del proyecto
Crear archivo `.env` en la raíz del proyecto con las siguientes variables:
```env
POSTGRES_NAME=nombre_bd
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### Migraciones
```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Poblar base de datos con datos de prueba
python manage.py shell < proyecto/poblador_datos_falsos.py
```

## 🔄 Actualización de Modelos

Cuando realices cambios en los modelos:
1. Detén los contenedores:
   ```bash
   docker-compose down
   ```
2. Elimina volúmenes (si es necesario):
   ```bash
   docker system prune -a --volumes
   ```
3. Reconstruye e inicia los servicios:
   ```bash
   docker-compose up -d --build
   ```
4. Aplica migraciones:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

## 🛠️ Configuración de Django

### Configuración de la base de datos en `settings.py`
```python
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

**Activar el entorno virtual**
   ```bash
   source myvenv/bin/activate
   ```


## 📝 Recursos Útiles
- [Guía de Docker](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-20-04-es)
- [Guía de Docker Compose](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-ubuntu-20-04-es)
- [Documentación de Django](https://docs.djangoproject.com/)
- [Documentación de PostgreSQL](https://www.postgresql.org/docs/)




TUTORIAL LOGIN
https://www.youtube.com/watch?v=Gr_QsOifaro
