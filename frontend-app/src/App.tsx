// src/App.tsx 
import React, { useState, useEffect } from 'react';

// CÓDIGO CORREGIDO:
interface Recommendation {
  pelicula_id: number; // Usamos el nombre del campo de FastAPI
  titulo: string;
  generos: string;
  director: string | null; // Director puede ser nulo
  actores?: string | null; // Actores puede ser nulo
  anio: number | null; // Año puede ser nulo
  activa: boolean; // El campo activa siempre será true, pero se incluye.
}

const App: React.FC = () => {

  // Estado para guardar la lista de géneros que viene de la BD
  const [generosDisponibles, setGenerosDisponibles] = useState<string[]>([]);
  // Estado para el género seleccionado
  const [genero, setGenero] = useState<string>('');

  const [recomendacion, setRecomendacion] = useState<Pelicula | null>(null);
  const [cargando, setCargando] = useState<boolean>(false);

  // Función para obtener la lista de géneros del backend
    useEffect(() => {
      const fetchGeneros = async () => {
        try {
          // 1. Verificar explícitamente si la respuesta fue exitosa (código 200)
          const response = await fetch('http://127.0.0.1:8000/generos');
          if (!response.ok) {
            // Si el servidor responde con 500 o 404, lanzamos un error claro
            throw new Error('Error al cargar la lista de géneros.');
          }
          // 2. Convertir la respuesta a JSON y tiparla
          const data: string[] = await response.json();
          setGenerosDisponibles(data);

          // 3. Establecer el primer género como la opción por defecto
          if (data.length > 0) {
            setGenero(data[0]); 
          }
        } catch (error) {
          // El error de 'fetch' o el error de 'throw' serán capturados aquí
          console.error("No se pudo obtener la lista de géneros:", error);
        }
      };

      fetchGeneros();
    }, []); // El array vacío asegura que esto se ejecute solo una vez al inicio

  const obtenerRecomendacion = async () => {


        if (!genero) {
                alert("Por favor, selecciona un género.");
                return;
            }

    
    setCargando(true);
    setRecomendacion(null);

  

    try {
      // Nota: El motor (FastAPI) debe estar corriendo en el puerto 8000
    const response = await fetch(`http://127.0.0.1:8000/recomendar?genero_elegido=${genero}`);
      if (!response.ok) {
        throw new Error("Respuesta de red no válida.");
      }
      const data: Recommendation = await response.json(); 
      setRecomendacion(data);
    } catch (error) {
      console.error("Error al obtener recomendación:", error);
      alert("¡Ups! El Motor de Magia (FastAPI) no está encendido o hubo un error.");
    } finally {
      setCargando(false);
    }
  };

  return (
    // Pico.css usa <main> para el contenido principal
   <main style={{ 
        minHeight: '100vh', 
        width: '100vw', // Ocupa el 100% del ancho del viewport
        maxWidth: 'none', // Desactivamos cualquier límite de ancho
        margin: 0, 
        padding: 0 // Quitamos el padding global que podría tener Pico
    }}>
      {/* Pico.css usa <article> para agrupar tarjetas o contenido principal */}
      {/* Aseguramos que el <article> también ocupe todo el ancho y aplicamos nuestro propio padding si es necesario. */}
      <article style={{ 
        margin: 0, 
        padding: '30px', // Añadimos padding interno para que el contenido no se pegue a los bordes
        width: '100%', 
        maxWidth: 'none' 
      }}
      >
        <header>
          <h1>🎥 Buscador de Películas</h1>
        </header>

        <p>
          ¡Elige un género! El sistema te dará una recomendación.
        </p>

        {/* 1. Selector de Género */}
            <label htmlFor="genero-selector">Género Preferido</label>
            <select
              id="genero-selector"
              value={genero}
              onChange={(e) => setGenero(e.target.value)}
              // Desactivar si la lista aún no se ha cargado
              disabled={generosDisponibles.length === 0} 
            >
              {/* Opción de carga mientras se obtienen los datos */}
              {generosDisponibles.length === 0 && <option>Cargando géneros...</option>}

              {/* Mapear la lista de géneros obtenida de la BD */}
              {generosDisponibles.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>

        {/* 2. Botón para pedir la recomendación */}
        {/* Pico usa el atributo 'aria-busy' para mostrar un spinner de carga en botones */}
        <button
          onClick={obtenerRecomendacion}
          aria-busy={cargando ? "true" : "false"}
          disabled={cargando}
        >
          {cargando ? 'Buscando...' : `Recomendar ${genero}`}
        </button>

        {/* 3. Resultado de la recomendación */}
        <hr />
        
        {recomendacion && (

          <div className="recommendation-result">
          <h2>✨ Recomendación para ti ✨</h2>
          <p className="pico-success"><strong>Película:</strong> {recomendacion.titulo} ({recomendacion.anio})</p> 
          <p className="pico-success"><strong>Director:</strong> {recomendacion.director}</p>
          <p className="pico-success"><strong>Géneros:</strong> {recomendacion.generos}</p>
          </div>
        )}
        {!recomendacion && !cargando && (
           <p>Presiona el botón para empezar la magia.</p>
        )}
      </article>
      <footer>
          <div className="footer-container">
              <div className="footer-section">
                  <h4>🤖 Motor de Recomendación</h4>
                  <p>Sistema impulsado por Machine Learning (Similitud de Coseno).</p>
              </div>
              
              <div className="footer-section">
                  <h4>🚀 Tecnologías Clave</h4>
                  <ul>
                      <li>Backend: Python (FastAPI)</li>
                      <li>Frontend: React & TypeScript</li>
                  </ul>
              </div>
              
              <div className="footer-section">
                  <p>&copy; 2025 Santiago Urdaneta</p>
                  <p>Desarrollado con enfoque en velocidad y escalabilidad.</p>
              </div>
          </div>
          
          <div className="footer-bottom">
              <p>Aviso legal | Política de Privacidad</p>
          </div>
      </footer>
    </main>
  );
};

export default App;