import mysql.connector
import json
import requests
from datetime import datetime

class AnalizadorContexto:
    def __init__(self):
        """
        Inicializar el analizador de contexto
        Configura la conexión a la base de datos y la API de OpenAI
        """
        # Configuración de la base de datos MySQL
        self.db_config = {
            'host': 'localhost',
            'user': 'root',          # Cambia esto por tu usuario de MySQL
            'password': 'clave123',          # Cambia esto por tu contraseña de MySQL
            'database': 'bot_productos_db',
            'charset': 'utf8mb4'
        }
        
        # Clave API de OpenAI (la misma que usabas antes)
        self.api_key = "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"
        
        # Verificar conexión inicial
        self.verificar_conexion()

    def verificar_conexion(self):
        """
        Verifica que la conexión a la base de datos funcione correctamente
        """
        try:
            conexion = mysql.connector.connect(**self.db_config)
            cursor = conexion.cursor()
            cursor.execute("SELECT 1")
            conexion.close()
            print("✅ Conexión a base de datos establecida correctamente")
        except Exception as e:
            print(f"❌ Error al conectar a la base de datos: {e}")
            print("💡 Verifica que MySQL esté corriendo y las credenciales sean correctas")

    def obtener_datos_base(self):
        """
        Obtiene todos los datos relevantes de la base de datos
        para usar como contexto en el análisis
        """
        try:
            # Establecer conexión
            conexion = mysql.connector.connect(**self.db_config)
            cursor = conexion.cursor(dictionary=True)
            
            datos_contexto = {}
            
            # Obtener productos con sus precios
            cursor.execute("""
                SELECT p.id_producto, p.nombre, p.descripcion, p.codigo, p.stock_global,
                       lp.nombre_lista, plp.precio
                FROM producto p
                LEFT JOIN productolistaprecio plp ON p.id_producto = plp.id_producto
                LEFT JOIN listaprecio lp ON plp.id_lista = lp.id_lista
                ORDER BY p.nombre, lp.nombre_lista
            """)
            productos_raw = cursor.fetchall()
            
            # Organizar productos por nombre
            productos = {}
            for row in productos_raw:
                nombre = row['nombre']
                if nombre not in productos:
                    productos[nombre] = {
                        'id': row['id_producto'],
                        'descripcion': row['descripcion'],
                        'codigo': row['codigo'],
                        'stock': row['stock_global'],
                        'precios': {}
                    }
                
                if row['nombre_lista'] and row['precio']:
                    productos[nombre]['precios'][row['nombre_lista']] = float(row['precio'])
            
            datos_contexto['productos'] = productos
            
            # Obtener sucursales y almacenes
            cursor.execute("""
                SELECT s.id_sucursal, s.nombre as sucursal_nombre, s.direccion,
                       a.id_almacen, a.nombre as almacen_nombre
                FROM sucursal s
                LEFT JOIN almacen a ON s.id_sucursal = a.id_sucursal
                ORDER BY s.nombre, a.nombre
            """)
            sucursales_raw = cursor.fetchall()
            
            sucursales = {}
            for row in sucursales_raw:
                nombre_sucursal = row['sucursal_nombre']
                if nombre_sucursal not in sucursales:
                    sucursales[nombre_sucursal] = {
                        'direccion': row['direccion'],
                        'almacenes': []
                    }
                
                if row['almacen_nombre']:
                    sucursales[nombre_sucursal]['almacenes'].append(row['almacen_nombre'])
            
            datos_contexto['sucursales'] = sucursales
            
            # Obtener información de stock por almacén
            cursor.execute("""
                SELECT p.nombre as producto_nombre, a.nombre as almacen_nombre, 
                       sa.cantidad, s.nombre as sucursal_nombre
                FROM stockalmacen sa
                JOIN producto p ON sa.id_producto = p.id_producto
                JOIN almacen a ON sa.id_almacen = a.id_almacen
                JOIN sucursal s ON a.id_sucursal = s.id_sucursal
                WHERE sa.cantidad > 0
                ORDER BY p.nombre, s.nombre
            """)
            stock_info = cursor.fetchall()
            datos_contexto['stock_por_ubicacion'] = stock_info
            
            # Obtener clientes recientes (para referencia)
            cursor.execute("""
                SELECT nombre, email, fecha_registro
                FROM cliente
                ORDER BY fecha_registro DESC
                LIMIT 10
            """)
            clientes_recientes = cursor.fetchall()
            datos_contexto['clientes_recientes'] = len(clientes_recientes)
            
            conexion.close()
            return datos_contexto
            
        except Exception as e:
            print(f"Error al obtener datos de la base: {e}")
            return {}

    def procesar_con_openai(self, prompt):
        """
        Procesa la consulta usando la API de OpenAI
        """
        try:
            # Configuración para la API de OpenAI
            endpoint = 'https://api.openai.com/v1/chat/completions'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            payload = {
                'model': 'gpt-4o-mini',  # Modelo más económico pero efectivo
                'messages': [
                    {
                        'role': 'system',
                        'content': 'Eres un asistente especializado en productos tecnológicos. Responde de manera clara y concisa.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.3,  # Respuestas más consistentes
                'max_tokens': 500    # Respuestas concisas
            }
            
            # Realizar la petición HTTP
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            
            # Verificar si la respuesta es exitosa
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', 'Error desconocido')
                return f"Error en API: {error_msg}"
            
            # Procesar la respuesta
            data = response.json()
            return data['choices'][0]['message']['content']
            
        except requests.Timeout:
            return "La consulta tardó demasiado en procesarse. Intenta de nuevo."
        except Exception as e:
            return f"Error al procesar con OpenAI: {str(e)}"

    def analizar_pregunta(self, pregunta):
        """
        Función principal que analiza si la pregunta está en contexto
        y genera una respuesta apropiada
        """
        try:
            # Obtener todos los datos de la base de datos
            datos_contexto = self.obtener_datos_base()
            
            if not datos_contexto:
                return {
                    'fuera_de_contexto': True,
                    'respuesta': 'No pude acceder a la información de productos en este momento.'
                }
            
            # Crear el contexto para el prompt
            contexto_productos = []
            for nombre, info in datos_contexto['productos'].items():
                precios_texto = ""
                if info['precios']:
                    precios_lista = [f"{lista}: {precio} Bs" for lista, precio in info['precios'].items()]
                    precios_texto = f" - Precios: {', '.join(precios_lista)}"
                
                contexto_productos.append(
                    f"- {nombre}: {info['descripcion']} (Stock: {info['stock']}){precios_texto}"
                )
            
            contexto_sucursales = []
            for nombre, info in datos_contexto['sucursales'].items():
                almacenes = ', '.join(info['almacenes']) if info['almacenes'] else 'Sin almacenes'
                contexto_sucursales.append(
                    f"- {nombre} ({info['direccion']}): {almacenes}"
                )
            
            # Construir el prompt para OpenAI
            prompt = f"""
INFORMACIÓN DE LA TIENDA DE PRODUCTOS TECNOLÓGICOS:

PRODUCTOS DISPONIBLES:
{chr(10).join(contexto_productos)}

SUCURSALES:
{chr(10).join(contexto_sucursales)}

CLIENTES REGISTRADOS: {datos_contexto.get('clientes_recientes', 0)} clientes recientes

INSTRUCCIONES:
1. La pregunta del usuario es: "{pregunta}"
2. Si la pregunta se relaciona con productos, precios, stock, sucursales, disponibilidad o cualquier información de la tienda, responde de manera útil y concisa.
3. Si la pregunta NO se relaciona con productos tecnológicos, ventas, stock, precios o información de la tienda, responde EXACTAMENTE: "No tengo información sobre eso. Alguna otra consulta relacionada a los productos?"
4. Mantén las respuestas breves pero informativas (máximo 3-4 líneas).
5. Si preguntan por un producto específico, incluye precio y disponibilidad si los tienes.
6. Si preguntan por categorías generales (ej: "laptops", "teclados"), menciona las opciones disponibles.

RESPUESTA:
"""
            
            # Procesar con OpenAI
            respuesta_ai = self.procesar_con_openai(prompt)
            
            # Verificar si está fuera de contexto
            fuera_contexto_phrases = [
                "Si se sale fuera de lo que hay en mi base de datos",
                "no tiene esa información",
                "fuera del contexto"
            ]
            
            es_fuera_contexto = any(phrase in respuesta_ai for phrase in fuera_contexto_phrases)
            
            return {
                'fuera_de_contexto': es_fuera_contexto,
                'respuesta': respuesta_ai.strip()
            }
            
        except Exception as e:
            print(f"Error en analizar_pregunta: {e}")
            return {
                'fuera_de_contexto': True,
                'respuesta': 'Error interno al procesar la consulta.'
            }