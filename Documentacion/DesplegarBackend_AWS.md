# **Documentación: Configuración Backend con Docker y GitHub SSH**

## **1. Preparación inicial de la instancia**

### 1.1. Crear y configurar la instancia
Realiza la creación y configuración inicial según tus criterios (sistema operativo, usuario, etc.).

### 1.2. Actualizar los repositorios internos
```bash
sudo apt update && sudo apt upgrade
```

### 1.3. Instalar Docker y Docker Compose
```bash
sudo apt install docker.io
sudo apt install docker-compose
```

## **2. Configuración de la llave SSH para GitHub**

### 2.1. Crear la llave privada
```bash
ssh-keygen -t rsa -b 4096 -C "correo_Vinculado_GitHub"
```
- **Ruta y nombre:** `/home/ubuntu/.ssh/key-proyectoIntegrado`
- **Contraseña:** `proyectoIntegrado`

### 2.2. Comprobar que la llave se creó correctamente
```bash
cd ~/.ssh
cat key-proyectoIntegrado.pub
```

### 2.3. Registrar la llave SSH en GitHub
1. Copia la llave **pública** (`key-proyectoIntegrado.pub`).
2. Ve a GitHub:  
   Perfil → Settings → SSH and GPG Keys → New SSH key.
3. Pega el contenido y asigna un nombre descriptivo.

### 2.4. Probar conexión con GitHub
```bash
ssh git@github.com
```

### 2.5. Configurar el archivo SSH `config`
```bash
vim ~/.ssh/config
```
Agrega lo siguiente:
```
Host *
    AddKeysToAgent yes
    IdentityFile ~/.ssh/key-proyectoIntegrado
```
Vuelve a probar:
```bash
ssh git@github.com
```
Agrega la contraseña y tu cuenta estará vinculada a la instancia.

## **3. Clonación y preparación del repositorio**

### 3.1. Actualizar tu repositorio con todos los cambios (GitHub)
En GitHub, selecciona clonar vía SSH.

### 3.2. Clonar el repositorio en la instancia
Ubícate en la raíz del directorio y ejecuta:
```bash
git clone git@github.com:<usuario>/<repositorio>.git
```

### 3.3. Preparación del entorno
1. Accede al repositorio clonado:
   ```bash
   cd <repositorio>
   ```
2. Crea el archivo `.env` y añade las claves necesarias.

## **4. Levantar los contenedores Docker**

### 4.1. Build y ejecución inicial
```bash
sudo docker compose up -d --build
```

### 4.2. Verificar contenedores activos
```bash
sudo docker ps
```

### 4.3. Configuración de variables
En el archivo `.env`, asegúrate de tener:  
`POSTGRES_HOST=postgres`  
(Modifica para que apunte correctamente al contenedor).

### 4.4. Reiniciar contenedores tras cambios
```bash
sudo docker compose down  # Apaga los contenedores
sudo docker compose up -d --build  # Reconstruye y levanta contenedores después de cambios
```

### 4.5. Verificar contenedores
```bash
sudo docker ps  # Ver contenedores activos
```
Deberían aparecer los 3 contenedores (web, db y nginx).

### 4.6. Revisar logs
```bash
sudo docker logs tienda_web  # Ver el estado del contenedor web
sudo docker logs tienda_db
sudo docker logs nginxs
```

## **5. Comandos útiles de Docker**

| Comando                                   | Acción                                                     |
|--------------------------------------------|------------------------------------------------------------|
| `sudo docker compose down`                 | Apaga todos los contenedores                               |
| `sudo docker compose up -d --build`        | Construye y levanta contenedores en segundo plano (rebuild)|
| `sudo docker ps`                           | Muestra contenedores activos                               |
| `sudo docker logs tienda_web`              | Muestra el estado/logs del contenedor web                  |

## **6. Configuración de Nginx como Proxy**

### 6.1. Editar archivo `nginx.conf`
Ubicado en el proyecto, copia:
```
server {
    listen 80;
    server_name _;

    # --- API Django ---
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # --- Static ---
    location /static/ {
        alias /app/static/;
    }

    # --- Media ---
    location /media/ {
        alias /app/media/;
    }
}
```

### 6.2. Reiniciar Nginx
```bash
sudo docker-compose restart nginx
```

## **7. Configuración en Django**

### 7.1. Permitir host de la instancia
En `settings.py`:
```python
ALLOWED_HOSTS = ['IP_Instancia']
```

### 7.2. Reiniciar contenedor web
```bash
sudo docker-compose restart web
```

### 7.3. Ajustar rutas API en Django
En `mysite/urls.py`, agrega (al final de `urlpatterns`):
```python
path('', include('proyecto.api_urls')),  # Esto muestra la API en la raíz
```

### 7.4. Guardar cambios y reiniciar web
```bash
sudo docker-compose restart web
```

## **8. Cargar datos del fixture (Django)**

### 8.1. Acceder a la base de datos
```bash
sudo docker exec -it tienda_db psql -U postgres -d tienda
```

### 8.2. Verificar usuarios
```sql
SELECT * FROM proyecto_usuario LIMIT 5;
```
Para salir:  
```
q
```

### 8.3. Editar fixture
- Elimina el fichero `datos.json` anterior y crea uno nuevo exclusivo para los modelos del proyecto.

### 8.4. Cargar datos al proyecto
```bash
sudo docker-compose exec web python manage.py loaddata proyecto/fixtures/datos.json
```

### 8.5. Configurar `STATIC_ROOT` y recolectar estáticos
En `settings.py`, debajo de `STATIC_URL`:
```python
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
```
Ejecuta:
```bash
sudo docker-compose exec web python manage.py collectstatic
```

---

