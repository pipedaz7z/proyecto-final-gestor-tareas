# Gestor de Tareas API

Proyecto final — Arquitectura Backend Moderna (ADSO - SENA, Ficha 3231102)

**Autor:** Andres Felipe Arcila

## ¿Qué hace?

Es una API para manejar tareas. Cualquiera puede registrarse e iniciar sesión.
Ver las tareas es público, pero crear, editar o eliminar necesita estar
logueado. Cada usuario solo puede modificar sus propias tareas.

## Tecnologías

- Python y FastAPI
- MongoDB Atlas (con PyMongo async)
- Argon2 para guardar las contraseñas
- JWT para el login
- python-dotenv para los secretos

## Cómo correrlo

1. Clonar el proyecto:
   ```bash
   git clone https://github.com/pipedaz7z/proyecto-final-gestor-tareas.git
   cd proyecto-final-gestor-tareas
   ```

2. Crear el entorno virtual e instalar las librerías:
   ```bash
   python -m venv venv
   venv\Scripts\activate        # en Mac/Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Copiar `.env.example` a `.env` y llenarlo con tus datos:
   ```
   MONGO_URI=tu_cadena_de_conexion_de_atlas
   SECRET_KEY=una_clave_larga_y_aleatoria
   ```

4. Arrancar el servidor:
   ```bash
   uvicorn main:app --reload
   ```

5. Abrir la documentación: http://127.0.0.1:8000/docs

## Endpoints

| Método | Ruta | ¿Necesita login? | Qué hace |
|---|---|---|---|
| POST | /registro | No | Crea un usuario |
| POST | /login | No | Devuelve el token |
| GET | /tareas | No | Lista las tareas |
| GET | /tareas/{id} | No | Muestra una tarea |
| POST | /tareas | Sí | Crea una tarea |
| PUT | /tareas/{id} | Sí | Edita una tarea |
| DELETE | /tareas/{id} | Sí | Elimina una tarea |
| GET | /mis-tareas | Sí | Lista solo mis tareas |

## Cómo funciona

- **Registro:** la clave se guarda hasheada con Argon2, nunca en texto.
- **Login:** si el correo y la clave son correctos, la API devuelve un token
  JWT que dura 60 minutos.
- **Rutas protegidas:** sin token responden 401.
- **Tareas por usuario:** al crear una tarea se guarda quién la creó. Si
  alguien intenta editar o borrar la de otro, responde 403.

## Cómo probarlo en /docs

1. Registrarse con `POST /registro`.
2. Probar `POST /tareas` sin login: da 401.
3. Pulsar **Authorize** y entrar con el correo y la clave.
4. Crear una tarea con `POST /tareas`.
5. Ver la tarea con `GET /tareas`.
6. Reiniciar el servidor y volver a listar: la tarea sigue ahí.
