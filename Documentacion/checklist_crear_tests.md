# Checklist de tests

## 1) Antes de escribir el test

- [ ] Define 1 sola regla de negocio a probar.
- [ ] Escribe el resultado esperado en una frase.
- [ ] Pon un nombre claro al test: `test_<quien>_<accion>_<resultado>`.

Ejemplo:

- Regla: "Un cliente no puede ver la lista de usuarios".
- Nombre: `test_cliente_no_puede_ver_lista`.

## 2) Estructura del test (AAA)

- [ ] **Arrange**: preparar datos y contexto.
- [ ] **Act**: ejecutar la funcion o metodo.
- [ ] **Assert**: comprobar el resultado.

Plantilla:

```python
# Arrange
# preparar datos

# Act
# ejecutar logica

# Assert
# verificar resultado
```

## 3) Para permisos en DRF

- [ ] Crear request simulado con `APIRequestFactory`.
- [ ] Asignar usuario al request (`request.user = ...`).
- [ ] Simular `view.action` cuando el permiso lo usa.
- [ ] Llamar `has_permission(request, view)`.
- [ ] Verificar con `assertFalse` o `assertTrue`.

Ejemplo real:

```python
from types import SimpleNamespace

request = self.factory.get("/api/v1/usuario/")
request.user = self.cliente
view = SimpleNamespace(action="list")

tiene_permiso = self.permiso.has_permission(request, view)
self.assertFalse(tiene_permiso)
```

## 4) Para pruebas de integración (APIClient)

- [ ] Usa `APIClient` para simular peticiones HTTP reales.
- [ ] Prepara los datos de entrada (usuario, payload, etc.).
- [ ] Envía la petición al endpoint correcto (`post`, `get`, `delete`, etc.).
- [ ] Verifica el código de estado esperado (`assertEqual` o `assertIn`).
- [ ] Comprueba que los datos devueltos sean los esperados (`assertEqual`, `assertIn`, etc.).
- [ ] Si esperas error, verifica que el mensaje o campo esté en la respuesta.
- [ ] Si el test requiere autenticación, usa `force_authenticate` o login previo.
- [ ] Si el test es de acceso restringido, verifica que responde 401 o 403.

Ejemplo:

```python
# Arrange
client = APIClient()
user_data = {...}

# Act
response = client.post('/api/v1/registro_cliente/', {'user_data': user_data}, format='json')

# Assert
self.assertEqual(response.status_code, status.HTTP_201_CREATED)
self.assertEqual(response.data['user_data']['username'], user_data['username'])
```

- [ ] Documenta el objetivo del test en un comentario.
- [ ] Usa nombres claros para los métodos de test.

## 4) Aserciones comunes

- [ ] `self.assertFalse(valor)` cuando esperas `False`.
- [ ] `self.assertTrue(valor)` cuando esperas `True`.
- [ ] `self.assertEqual(a, b)` cuando esperas igualdad.
- [ ] `self.assertIsNone(valor)` cuando esperas `None`.
- [ ] `self.assertIn(x, contenedor)` cuando algo debe existir.

## 5) Ejecutar y validar

- [ ] Ejecutar solo 1 test (iteracion rapida):

```bash
python manage.py test proyecto.tests.EsDuenioUsuarioTests.test_cliente_no_puede_ver_lista --verbosity 2
```

- [ ] Si pasa, ejecutar el archivo completo:

```bash
python manage.py test proyecto.tests --verbosity 2
```

- [ ] Revisar salida: debe decir `OK`.

## 6) Debug rapido (si falla)

- [ ] Leer el mensaje exacto del error.
- [ ] Verificar datos de entrada del test (usuario, action, etc.).
- [ ] Confirmar que la regla en permisos coincide con lo esperado.
- [ ] Si usaste `breakpoint()`, quitarlo al terminar.

## 7) Checklist final antes de cerrar

- [ ] El nombre del test describe claramente la regla.
- [ ] El test prueba solo una cosa.
- [ ] No hay codigo repetido innecesario (usar helper o `setUp`).
- [ ] El test es facil de leer (pasos cortos y claros).
- [ ] Todos los tests relevantes pasan.
