# 🎥 App de Recomendación de Peliculas Similares

## 🚀 Descripción del Proyecto

Este repositorio contiene la arquitectura completa de una App de Recomendación de Peliculas Similares dividida en dos componentes principales:

1.  **Backend (FastAPI - Python):** Una API robusta y escalable que sirve datos, maneja la autenticación de administradores (JWT y bcrypt), implementa las operaciones CRUD para la gestión de películas y proporciona un endpoint público de recomendación aleatoria. La API se conecta a una base de datos MySQL.
2.  **Frontend (React/TypeScript/Vite):** Interfaz de consulta para el usuario final (Búsqueda por Género y da Recomendaciones).

El enfoque principal de este proyecto es la separación de responsabilidades y la seguridad.

## ✨ Características Principales

* **Autenticación Segura:** Inicio de sesión de administrador con **JWT** y contraseñas cifradas con **bcrypt**.
* **Panel Administrativo Protegido:** Operaciones CRUD (Crear, Leer, Actualizar, Eliminar Lógico) de películas disponibles solo para usuarios autenticados.
* **Endpoints Públicos:** Rutas no protegidas para el consumo del usuario final (listado de géneros, recomendación básica).
* **Tecnologías Modernas:** Construido con FastAPI (Python) para el backend y React/TypeScript para el frontend.

## ⚙️ Configuración y Ejecución

### 1. Backend (FastAPI)

#### A. Entorno e Instalación

1.  Crea y activa el entorno virtual de Python:
    ```bash
    python -m venv .venv
    source .venv/Scripts/activate  # En Windows/Git Bash
    # source .venv/bin/activate    # En Linux/macOS
    ```
2.  Instala las dependencias (ejecuta el comando completo):
    ```bash
    pip install fastapi "uvicorn[standard]" mysqlclient sqlalchemy pandas scikit-learn pydantic
    ```

#### B. Base de Datos y Configuración

1.  **MySQL:** Asegúrate de que tu servidor MySQL esté corriendo.
2.  **Configuración:** Edita `config.py` con tus credenciales de MySQL y el hash de la contraseña de administrador.
3.  **Ejecución:** Inicia el servidor de FastAPI:
    ```bash
    uvicorn main:app --reload
    ```
    El API estará disponible en: `http://127.0.0.1:8000`

### 2. Frontend (React)

1.  Navega a la carpeta del frontend.
2.  Instala las dependencias de Node.js:
    ```bash
    npm install
    ```
3.  Inicia la aplicación de React:
    ```bash
    npm run dev
    ```
    El frontend estará disponible en: `http://localhost:5174` (o el puerto que te indique Vite).

TO DO

Una interfaz de usuario para el administrador (Login y Panel CRUD)