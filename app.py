from flask import Flask, request, jsonify
from flask_cors import CORS
import json
from analizador import AnalizadorContexto
from generador_intereses import GeneradorIntereses
from generador_imagen import GeneradorImagen

# Crear la aplicación Flask
app = Flask(__name__)

# Habilitar CORS para permitir peticiones desde cualquier origen
# Esto es importante para desarrollo frontend-backend
CORS(app)

# Instanciar los diferentes módulos
# Analizador de contexto para consultas de productos
analizador = AnalizadorContexto()

# Generador de intereses para análisis de conversaciones
generador_intereses = GeneradorIntereses()

# Generador de imágenes personalizadas
generador_imagen = GeneradorImagen()

@app.route('/api/verificar_contexto', methods=['POST'])
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

@app.route('/api/generador_intereses', methods=['POST'])
def generar_intereses():
    """
    Ruta para generar y guardar intereses del cliente basado en sus conversaciones
    
    Recibe:
    - POST request con body JSON que contiene:
      * 'usuario_telefono': número de teléfono del cliente
      * 'conversacion': tipo de conversación ('inicial_3', 'final_3', etc.)
    
    Devuelve:
    - JSON con estado del proceso
    """
    try:
        # Obtener datos del request JSON
        data = request.get_json()
        
        # Validar campos requeridos
        if not data or 'usuario_telefono' not in data or 'conversacion' not in data:
            return jsonify({
                'estado': 'error',
                'mensaje': 'Debes enviar usuario_telefono y conversacion'
            }), 400
        
        usuario_telefono = data['usuario_telefono']
        tipo_conversacion = data['conversacion']
        
        # Validar que los campos no estén vacíos
        if not usuario_telefono.strip() or not tipo_conversacion.strip():
            return jsonify({
                'estado': 'error',
                'mensaje': 'Los campos no pueden estar vacíos'
            }), 400
        
        # Validar formato de conversación
        if not (tipo_conversacion.startswith('inicial_') or tipo_conversacion.startswith('final_')):
            return jsonify({
                'estado': 'error',
                'mensaje': 'Formato de conversación inválido. Use inicial_N o final_N'
            }), 400
        
        # Procesar intereses del cliente
        resultado = generador_intereses.procesar_intereses_cliente(usuario_telefono, tipo_conversacion)
        
        # Retornar resultado
        return jsonify(resultado)
        
    except Exception as e:
        # Manejar errores inesperados
        print(f"Error en generador de intereses: {str(e)}")
        return jsonify({
            'estado': 'error',
            'mensaje': 'Proceso incorrecto',
            'detalle': str(e)
        }), 500

@app.route('/api/generar_imagen', methods=['POST'])
def generar_imagen_personalizada():
    """
    Ruta para generar imagen personalizada basada en los intereses del cliente
    
    Recibe:
    - POST request con body JSON que contiene:
      * 'usuario_telefono': número de teléfono del cliente
    
    Devuelve:
    - JSON con:
      * 'urlImagen': URL de la imagen en Cloudinary
      * 'bytesImagen': imagen en base64
    """
    try:
        # Obtener datos del request JSON
        data = request.get_json()
        
        # Validar campo requerido
        if not data or 'usuario_telefono' not in data:
            return jsonify({
                'error': 'Debes enviar usuario_telefono'
            }), 400
        
        usuario_telefono = data['usuario_telefono']
        
        # Validar que el campo no esté vacío
        if not usuario_telefono.strip():
            return jsonify({
                'error': 'El usuario_telefono no puede estar vacío'
            }), 400
        
        # Generar imagen personalizada
        resultado = generador_imagen.generar_imagen_cliente(usuario_telefono)
        
        # Retornar resultado
        return jsonify(resultado)
        
    except Exception as e:
        # Manejar errores inesperados
        print(f"Error en generador de imagen: {str(e)}")
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
        'message': 'Servidor funcionando correctamente',
        'modulos': {
            'analizador': 'activo',
            'generador_intereses': 'activo',
            'generador_imagen': 'activo'
        }
    })

@app.route('/', methods=['GET'])
def home():
    """
    Ruta principal para mostrar información básica de la API
    """
    return jsonify({
        'message': 'API de Análisis de Contexto y Generación de Contenido',
        'version': '2.0',
        'endpoints': {
            'consulta_productos': '/api/verificar_contexto (POST)',
            'generar_intereses': '/api/generador_intereses (POST)',
            'generar_imagen': '/api/generar_imagen (POST)',
            'health': '/api/health (GET)'
        },
        'descripcion': {
            'verificar_contexto': 'Analiza preguntas sobre productos como un vendedor',
            'generador_intereses': 'Analiza conversaciones y detecta intereses en productos',
            'generar_imagen': 'Genera imagen personalizada basada en intereses del cliente'
        }
    })

if __name__ == '__main__':
    print("🚀 Iniciando servidor Flask...")
    print("📡 Servidor disponible en: http://localhost:5000")
    print("🔗 Endpoints disponibles:")
    print("   • POST /api/verificar_contexto - Consultas de productos")
    print("   • POST /api/generador_intereses - Análisis de intereses")
    print("   • POST /api/generar_imagen - Generación de imágenes")
    print("   • GET  /api/health - Estado del servidor")
    print("💡 Para detener el servidor: Ctrl+C")
    
    # Ejecutar la aplicación en modo debug
    # debug=True permite ver errores detallados y reinicia automáticamente
    # host='0.0.0.0' permite acceso desde otras IPs
    # port=5000 es el puerto por defecto
    app.run(debug=True, host='0.0.0.0', port=5000)