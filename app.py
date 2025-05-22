from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from analizador import AnalizadorContexto

# Crear la aplicación Flask
app = Flask(__name__)

# Habilitar CORS para permitir peticiones desde cualquier origen
# Esto es importante para desarrollo frontend-backend
CORS(app)

# Instanciar el analizador de contexto
# Este objeto manejará toda la lógica de análisis
analizador = AnalizadorContexto()

@app.route('/api/consulta', methods=['POST'])
def consulta():
    """
    Ruta principal para analizar consultas de productos
    
    Recibe:
    - POST request con body JSON que contiene 'pregunta'
    
    Devuelve:
    - JSON con 'respuesta' si está en contexto
    - JSON con mensaje de fuera de contexto si no aplica
    """
    try:
        # Obtener datos del request JSON
        data = request.get_json()
        
        # Validar que se envió el campo 'pregunta'
        if not data or 'pregunta' not in data:
            return jsonify({
                'error': 'Debes enviar una pregunta en el campo "pregunta"'
            }), 400
        
        # Extraer la pregunta del usuario
        pregunta = data['pregunta']
        
        # Validar que la pregunta no esté vacía
        if not pregunta.strip():
            return jsonify({
                'error': 'La pregunta no puede estar vacía'
            }), 400
        
        # Procesar la pregunta con el analizador
        respuesta = analizador.analizar_pregunta(pregunta)
        
        # Retornar la respuesta en formato JSON
        return jsonify(respuesta)
        
    except Exception as e:
        # Manejar errores inesperados
        print(f"Error en la consulta: {str(e)}")
        return jsonify({
            'error': 'Error interno del servidor',
            'detalle': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """
    Ruta de salud para verificar que el servidor está funcionando
    """
    return jsonify({
        'status': 'ok',
        'message': 'Servidor funcionando correctamente'
    })

@app.route('/', methods=['GET'])
def home():
    """
    Ruta principal para mostrar información básica de la API
    """
    return jsonify({
        'message': 'API de Análisis de Contexto de Productos',
        'version': '1.0',
        'endpoints': {
            'consulta': '/api/consulta (POST)',
            'health': '/api/health (GET)'
        }
    })

if __name__ == '__main__':
    print("🚀 Iniciando servidor Flask...")
    print("📡 Servidor disponible en: http://localhost:5000")
    print("🔗 Endpoint principal: http://localhost:5000/api/consulta")
    print("💡 Para detener el servidor: Ctrl+C")
    
    # Ejecutar la aplicación en modo debug
    # debug=True permite ver errores detallados y reinicia automáticamente
    # host='0.0.0.0' permite acceso desde otras IPs
    # port=5000 es el puerto por defecto
    app.run(debug=True, host='0.0.0.0', port=5000)