# main.py

from fastapi import FastAPI, HTTPException, Query, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
import pandas as pd
from typing import Optional, List
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer

# Importamos la configuración y el hash de la contraseña
from config import DATABASE_URL, ADMIN_PASSWORD_HASH

# --- CONFIGURACIÓN DE SEGURIDAD ---
SECRET_KEY = "$2a$12$qViZVikxOktKRXgTUha8QOHnhpDZZNN81MxcjUMypkxFwXkgfp9u." # 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # Endpoint para obtener el token

# Funciones de Hashing y Verificación
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependencia para Proteger Endpoints
async def get_current_admin(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la credencial",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username != "admin":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return "admin" 

# --- MODELOS PYDANTIC ---

class LoginData(BaseModel):
    username: str
    password: str

class PeliculaBase(BaseModel):
    titulo: str
    generos: str
    director: Optional[str] = None
    actores: Optional[str] = None
    anio: Optional[int] = None

class Pelicula(PeliculaBase):
    pelicula_id: int
    activa: bool
    
    class Config:
        from_attributes = True

class PaginatedMovies(BaseModel):
    items: List[Pelicula]
    total_items: int
    pages: int
    current_page: int

# --- CONFIGURACIÓN DE FASTAPI Y CORS ---
app = FastAPI()

origins = [
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ----------------------------------------

# Conexión al motor de BD
try:
    engine = create_engine(DATABASE_URL)
    print("✅ Conexión a MySQL establecida con éxito.")
except Exception as e:
    print(f"❌ Error al conectar a MySQL. Asegúrate de que MySQL esté corriendo: {e}")
    raise Exception("No se pudo establecer la conexión a la base de datos.")

# ----------------------------------------
# ENDPOINT PÚBLICO: GÉNEROS (Para el usuario final)
# ----------------------------------------

@app.get("/generos", response_model=list[str])
def obtener_generos_publico():
    """
    Ruta pública que el frontend llama para poblar el selector de géneros.
    NOTA: Las películas deben cargarse con un estado activa=TRUE para asegurar la eficiencia.
    """
    
    # 1. Consulta para obtener todos los géneros
    # Utilizamos el campo 'generos' (que es una cadena como "Acción, Comedia")
    # y solo consideramos películas activas
    query_genres = text("SELECT generos FROM peliculas WHERE activa = TRUE;")
    
    try:
        with engine.connect() as connection:
            # Leemos los datos de la columna 'generos'
            result = connection.execute(query_genres).fetchall()
            
    except Exception as e:
        print(f"Error al leer géneros de MySQL: {e}")
        raise HTTPException(status_code=503, detail="No se pudo conectar a la base de datos para obtener géneros.")

    # 2. Procesamiento de la lista: Explode y Uniques
    generos_set = set()
    
    for row in result:
        # La base de datos devuelve (generos='Acción, Drama')
        genre_string = row[0]
        
        # Dividimos por coma y espacio, y agregamos al conjunto
        for genre in genre_string.split(', '):
            genre = genre.strip()
            if genre:
                generos_set.add(genre)
    
    # 3. Convertir el conjunto a una lista ordenada
    generos_list = sorted(list(generos_set))
    
    if not generos_list:
        raise HTTPException(status_code=404, detail="No hay géneros definidos en las películas activas.")
        
    return generos_list    

@app.get("/peliculas", response_model=PaginatedMovies)
async def list_movies_public(
    page: int = 1,
    per_page: int = 20, 
    search: Optional[str] = Query(None, description="Búsqueda por título o director"),
    genero: Optional[str] = Query(None, description="Filtrar por género")
):
    """
    Lista películas activas con paginación y filtros para el usuario final.
    """
    offset = (page - 1) * per_page
    
    # PASO CLAVE DE SEGURIDAD: Solo se buscan películas activas (activa = TRUE)
    where_clauses = ["activa = TRUE"] 
    params = {"limit": per_page, "offset": offset}
    
    if search:
        # Búsqueda por título o director.
        where_clauses.append("(titulo LIKE :search OR director LIKE :search)")
        params["search"] = f"%{search}%"
        
    if genero:
        # Filtro de género.
        where_clauses.append("generos LIKE :genero")
        params["genero"] = f"%{genero}%"
        
    where_sql = " AND ".join(where_clauses)
    
    # Consulta de ITEMS (datos de la página)
    items_query = text(f"""
        SELECT pelicula_id, titulo, generos, director, actores, anio, activa
        FROM peliculas
        WHERE {where_sql}
        ORDER BY anio DESC 
        LIMIT :limit OFFSET :offset;
    """)
    
    # Consulta de TOTAL (para paginación)
    count_query = text(f"""
        SELECT COUNT(*) FROM peliculas WHERE {where_sql};
    """)
    
    try:
        with engine.connect() as connection:
            # Ejecución de consultas parametrizadas (Seguridad: Prevención de SQL Injection)
            items_result = connection.execute(items_query, params).fetchall()
            items_list = [Pelicula.model_validate(row, from_attributes=True) for row in items_result]
            
            total_items = connection.execute(count_query, params).scalar_one()
            
            pages = (total_items + per_page - 1) // per_page
            
            return PaginatedMovies(
                items=items_list,
                total_items=total_items,
                pages=pages,
                current_page=page
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la consulta pública: {e}")    

@app.get("/recomendar", response_model=Pelicula)
async def recomendar_pelicula_basica(genero_elegido: str = Query(..., description="Género elegido por el usuario")):
    """
    Devuelve una película activa aleatoria que coincide con el género elegido.
    """
    
    # Parámetros y filtro de seguridad
    params = {"genero": f"%{genero_elegido}%"}
    
    # Consulta SQL para seleccionar una película aleatoria
    # LIMIT 1 asegura que solo se traiga una. 
    # ORDER BY RAND() es lento pero simple para una recomendación aleatoria.
    query = text("""
        SELECT pelicula_id, titulo, generos, director, actores, anio, activa
        FROM peliculas
        WHERE activa = TRUE AND generos LIKE :genero
        ORDER BY RAND()
        LIMIT 1;
    """)
    
    try:
        with engine.connect() as connection:
            result = connection.execute(query, params).fetchone()
            
            if result is None:
                raise HTTPException(status_code=404, detail=f"No se encontraron películas activas para el género '{genero_elegido}'.")
            
            # Devuelve el objeto Pelicula
            return Pelicula.model_validate(result, from_attributes=True)
            
    except Exception as e:
        # Aquí atrapamos posibles errores de conexión o ejecución
        raise HTTPException(status_code=500, detail=f"Error interno al obtener recomendación: {e}")
        
# ----------------------------------------
# ENDPOINTS DE AUTENTICACIÓN
# ----------------------------------------

@app.post("/token")
async def login_for_access_token(form_data: LoginData):
    # 1. Validar el usuario (hardcoded para "admin")
    if form_data.username != "admin":
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")

    # 2. Verificar la contraseña hasheada contra el valor en config.py
    if not verify_password(form_data.password, ADMIN_PASSWORD_HASH):
        raise HTTPException(status_code=400, detail="Credenciales incorrectas")

    # 3. Generar el Token JWT
    access_token = create_access_token(data={"sub": "admin"})
    
    return {"access_token": access_token, "token_type": "bearer"}

# ----------------------------------------
# ENDPOINTS DE ADMINISTRACIÓN (CRUD)
# ----------------------------------------

@app.post("/admin/peliculas", response_model=Pelicula)
async def create_movie(pelicula: PeliculaBase, admin: str = Depends(get_current_admin)):
    """Crea una nueva película."""
    insert_query = text("""
        INSERT INTO peliculas (titulo, generos, director, actores, anio, activa)
        VALUES (:titulo, :generos, :director, :actores, :anio, TRUE);
    """)
    
    try:
        with engine.connect() as connection:
            result = connection.execute(insert_query, pelicula.model_dump())
            connection.commit()
            
            new_id = result.lastrowid
            return Pelicula(pelicula_id=new_id, activa=True, **pelicula.model_dump())
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear película: {e}")

@app.put("/admin/peliculas/{pelicula_id}", response_model=Pelicula)
async def update_movie(pelicula_id: int, pelicula: PeliculaBase, admin: str = Depends(get_current_admin)):
    """Actualiza la información de una película existente."""
    update_query = text("""
        UPDATE peliculas SET 
        titulo = :titulo, generos = :generos, director = :director, 
        actores = :actores, anio = :anio
        WHERE pelicula_id = :id;
    """)
    
    try:
        with engine.connect() as connection:
            result = connection.execute(update_query, {**pelicula.model_dump(), "id": pelicula_id})
            connection.commit()
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Película no encontrada.")
            
            # Devolvemos el estado de la película (activa o no)
            select_query = text("SELECT activa FROM peliculas WHERE pelicula_id = :id;")
            activa_status = connection.execute(select_query, {"id": pelicula_id}).scalar_one()

            return Pelicula(pelicula_id=pelicula_id, activa=activa_status, **pelicula.model_dump())
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar película: {e}")

@app.delete("/admin/peliculas/{pelicula_id}")
async def deactivate_movie(pelicula_id: int, admin: str = Depends(get_current_admin)):
    """Desactiva (Eliminación Lógica) una película."""
    delete_query = text("UPDATE peliculas SET activa = FALSE WHERE pelicula_id = :id;")
    
    try:
        with engine.connect() as connection:
            result = connection.execute(delete_query, {"id": pelicula_id})
            connection.commit()
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Película no encontrada.")
            
            return {"message": f"Película {pelicula_id} desactivada (eliminación lógica)."}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al desactivar película: {e}")

# --- Búsqueda, Filtrado y Paginación ---

@app.get("/admin/peliculas", response_model=PaginatedMovies)
async def list_movies(
    page: int = 1,
    per_page: int = 20, 
    search: Optional[str] = Query(None, description="Búsqueda por título o director"),
    genero: Optional[str] = Query(None, description="Filtrar por género"),
    activa: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo")
):
    """
    Lista películas con paginación, búsqueda y filtros.
    """
    offset = (page - 1) * per_page
    
    where_clauses = ["1=1"]
    params = {"limit": per_page, "offset": offset}
    
    if search:
        where_clauses.append("(titulo LIKE :search OR director LIKE :search)")
        params["search"] = f"%{search}%"
        
    if genero:
        where_clauses.append("generos LIKE :genero")
        params["genero"] = f"%{genero}%"

    if activa is not None:
        where_clauses.append("activa = :activa")
        params["activa"] = activa
        
    where_sql = " AND ".join(where_clauses)
    
    # Consulta de ITEMS y TOTAL
    items_query = text(f"""
        SELECT pelicula_id, titulo, generos, director, actores, anio, activa
        FROM peliculas
        WHERE {where_sql}
        ORDER BY pelicula_id DESC
        LIMIT :limit OFFSET :offset;
    """)
    
    count_query = text(f"""
        SELECT COUNT(*) FROM peliculas WHERE {where_sql};
    """)
    
    try:
        with engine.connect() as connection:
            items_result = connection.execute(items_query, params).fetchall()
            # Usamos Pelicula.model_validate para mapear las filas de SQL a Pydantic
            items_list = [Pelicula.model_validate(row, from_attributes=True) for row in items_result]
            
            total_items = connection.execute(count_query, params).scalar_one()
            
            pages = (total_items + per_page - 1) // per_page
            
            return PaginatedMovies(
                items=items_list,
                total_items=total_items,
                pages=pages,
                current_page=page
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la consulta: {e}")