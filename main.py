"""
==========================================================================
 PROYECTO FINAL DEL TRIMESTRE — Gestor de Tareas API
 Arquitectura Backend Moderna · Ficha 3231102 (ADSO - SENA)
==========================================================================

 Integra TODO el temario del modulo en una sola aplicacion:
   - MongoDB (async) con AsyncMongoClient          -> Clase 5
   - API con FastAPI, Pydantic y /docs             -> Clase 4
   - CRUD completo y persistente                   -> Clases 3 y 5
   - Seguridad: registro, login, JWT, proteccion   -> Clase 6

 COMO ARRANCAR:  ver el archivo  README.md
==========================================================================
"""

import os
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo import AsyncMongoClient
from bson import ObjectId
from bson.errors import InvalidId
from pydantic import BaseModel
from pwdlib import PasswordHash
import jwt
from jwt.exceptions import InvalidTokenError
from dotenv import load_dotenv

# --------------------------------------------------------------------------
#  CONFIGURACION  (los secretos se leen del archivo .env)
# --------------------------------------------------------------------------
load_dotenv()

app = FastAPI(title="Gestor de Tareas API")

hasher = PasswordHash.recommended()                     # hashing con Argon2
SECRET = os.getenv("SECRET_KEY", "CAMBIAME_EN_EL_ARCHIVO_.env")
ALGO = "HS256"
EXPIRA_MINUTOS = 60                                     # vida del token
oauth2 = OAuth2PasswordBearer(tokenUrl="login")

URI = os.getenv("MONGO_URI", "mongodb+srv://admin_sena:Baraya66@cluster0.nidf5qv.mongodb.net/")
db = AsyncMongoClient(URI)["gestor_tareas_db"]
usuarios = db["usuarios"]
tareas = db["tareas"] 


# --------------------------------------------------------------------------
#  MODELOS
# --------------------------------------------------------------------------
class Usuario(BaseModel):
    correo: str
    clave: str

class Tarea(BaseModel):
    titulo: str
    descripcion: str = ""
    completada: bool = False


# --------------------------------------------------------------------------
#  UTILIDAD: convierte texto a ObjectId con seguridad
# --------------------------------------------------------------------------
def a_oid(id):
    try:
        return ObjectId(id)
    except InvalidId:
        return None


# ==========================================================================
#  BLOQUE 1 — SEGURIDAD
# ==========================================================================

# --- 1.1  Registro de usuarios  (POST /registro) --------------------------
@app.post("/registro", status_code=201)
async def registro(u: Usuario):
    # Rechaza si el correo ya existe
    if await usuarios.find_one({"correo": u.correo}):
        raise HTTPException(400, "El correo ya esta registrado")

    # Guarda la clave HASHEADA (nunca en texto plano)
    await usuarios.insert_one({
        "correo": u.correo,
        "clave": hasher.hash(u.clave),
    })
    return {"mensaje": "Usuario creado", "correo": u.correo}


# --- 1.2  Login  (POST /login) --------------------------------------------
@app.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    # OAuth2PasswordRequestForm usa el campo "username": aqui es el correo
    u = await usuarios.find_one({"correo": form.username})

    # Mismo mensaje si el correo no existe o la clave es incorrecta,
    # para no revelar cuales correos estan registrados
    if not u or not hasher.verify(form.password, u["clave"]):
        raise HTTPException(401, "Correo o clave incorrectos")

    token = jwt.encode(
        {
            "sub": u["correo"],
            "exp": datetime.now(timezone.utc) + timedelta(minutes=EXPIRA_MINUTOS),
        },
        SECRET,
        algorithm=ALGO,
    )
    return {"access_token": token, "token_type": "bearer"}


# --- 1.3  Dependencia de autenticacion  (referencia) ----------------------
async def usuario_actual(token: str = Depends(oauth2)):
    try:
        datos = jwt.decode(token, SECRET, algorithms=[ALGO])
        return datos["sub"]
    except InvalidTokenError:
        raise HTTPException(401, "Token invalido o expirado")


# ==========================================================================
#  BLOQUE 2 — CRUD DE TAREAS
#  Regla de acceso: LEER es publico; CREAR/EDITAR/ELIMINAR exige token.
# ==========================================================================

# --- 2.1  Listar todas las tareas  (GET /tareas) --------------------------
@app.get("/tareas")
async def listar():
    resultado = []
    async for t in tareas.find():
        t["_id"] = str(t["_id"])
        resultado.append(t)
    return resultado


# --- 2.2  Una tarea por su id  (GET /tareas/{id}) -------------------------
@app.get("/tareas/{id}")
async def obtener(id: str):
    oid = a_oid(id)
    if oid is None:
        raise HTTPException(400, "El id no es valido")

    t = await tareas.find_one({"_id": oid})
    if t is None:
        raise HTTPException(404, "La tarea no existe")

    t["_id"] = str(t["_id"])
    return t


# --- 2.3  Crear una tarea  (POST /tareas)  [PROTEGIDO] --------------------
@app.post("/tareas", status_code=201)
async def crear(nueva: Tarea, usuario: str = Depends(usuario_actual)):
    doc = nueva.model_dump()
    doc["dueno"] = usuario            # RETO: guarda quien la creo
    r = await tareas.insert_one(doc)
    return {"mensaje": "Tarea creada", "id": str(r.inserted_id)}


# --- 2.4  Actualizar una tarea  (PUT /tareas/{id})  [PROTEGIDO] -----------
@app.put("/tareas/{id}")
async def actualizar(id: str, datos: Tarea, usuario: str = Depends(usuario_actual)):
    oid = a_oid(id)
    if oid is None:
        raise HTTPException(400, "El id no es valido")

    t = await tareas.find_one({"_id": oid})
    if t is None:
        raise HTTPException(404, "La tarea no existe")
    if t.get("dueno") != usuario:     # RETO avanzado: solo el dueno edita
        raise HTTPException(403, "No puedes editar tareas de otro usuario")

    await tareas.update_one({"_id": oid}, {"$set": datos.model_dump()})
    return {"mensaje": "Tarea actualizada"}


# --- 2.5  Eliminar una tarea  (DELETE /tareas/{id})  [PROTEGIDO] ----------
@app.delete("/tareas/{id}")
async def eliminar(id: str, usuario: str = Depends(usuario_actual)):
    oid = a_oid(id)
    if oid is None:
        raise HTTPException(400, "El id no es valido")

    t = await tareas.find_one({"_id": oid})
    if t is None:
        raise HTTPException(404, "La tarea no existe")
    if t.get("dueno") != usuario:     # RETO avanzado: solo el dueno elimina
        raise HTTPException(403, "No puedes eliminar tareas de otro usuario")

    await tareas.delete_one({"_id": oid})
    return {"mensaje": "Tarea eliminada"}


# ==========================================================================
#  BLOQUE 3 — RETO OPCIONAL: "Cada quien ve solo SUS tareas."
# ==========================================================================
@app.get("/mis-tareas")
async def mis_tareas(usuario: str = Depends(usuario_actual)):
    resultado = []
    async for t in tareas.find({"dueno": usuario}):
        t["_id"] = str(t["_id"])
        resultado.append(t)
    return resultado
