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
            'password': 'clave123',  # Cambia esto por tu contraseña de MySQL
            'database': 'bot_productos_db',
            'charset': 'utf8mb4'
        }
        
        # Clave API de OpenAI
        self.api_key = ""
        
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
        Solo información necesaria para venta: productos, precios, stock, sucursales
        """
        try:
            # Establecer conexión
            conexion = mysql.connector.connect(**self.db_config)
            cursor = conexion.cursor(dictionary=True)
            
            datos_contexto = {}
            
            # Obtener productos con sus precios (solo productos activos)
            cursor.execute("""
                SELECT p.id_producto, p.nombre, p.descripcion, p.codigo, 
                       p.stock_global, p.precio_base,
                       lp.nombre_lista, plp.precio
                FROM producto p
                LEFT JOIN productolistaprecio plp ON p.id_producto = plp.id_producto
                LEFT JOIN listaprecio lp ON plp.id_lista = lp.id_lista AND lp.activo = TRUE
                WHERE p.activo = TRUE
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
                        'stock_global': row['stock_global'],
                        'precio_base': float(row['precio_base']) if row['precio_base'] else 0,
                        'precios': {}
                    }
                
                # Agregar precios de listas específicas si existen
                if row['nombre_lista'] and row['precio']:
                    productos[nombre]['precios'][row['nombre_lista']] = float(row['precio'])
            
            datos_contexto['productos'] = productos
            
            # Obtener sucursales activas con sus almacenes
            cursor.execute("""
                SELECT s.id_sucursal, s.nombre as sucursal_nombre, s.direccion,
                       a.id_almacen, a.nombre as almacen_nombre
                FROM sucursal s
                LEFT JOIN almacen a ON s.id_sucursal = a.id_sucursal AND a.activo = TRUE
                WHERE s.activo = TRUE
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
            
            # Obtener información de stock por almacén (solo cantidades positivas)
            cursor.execute("""
                SELECT p.nombre as producto_nombre, a.nombre as almacen_nombre, 
                       sa.cantidad, s.nombre as sucursal_nombre
                FROM stockalmacen sa
                JOIN producto p ON sa.id_producto = p.id_producto
                JOIN almacen a ON sa.id_almacen = a.id_almacen
                JOIN sucursal s ON a.id_sucursal = s.id_sucursal
                WHERE sa.cantidad > 0 AND p.activo = TRUE AND a.activo = TRUE AND s.activo = TRUE
                ORDER BY p.nombre, s.nombre
            """)
            stock_info = cursor.fetchall()
            datos_contexto['stock_por_ubicacion'] = stock_info
            
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
            endpoint = 'https://api.openai.com/v1/chat/completions'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
            
            payload = {
                'model': 'gpt-4o-mini',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'Eres un vendedor experto en productos tecnológicos. Responde como un consultor de tienda profesional, amable y servicial. Solo brinda información sobre productos, precios, stock y disponibilidad.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.3,
                'max_tokens': 400
            }
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', 'Error desconocido')
                return f"Disculpa, tengo problemas técnicos. Intenta de nuevo."
            
            data = response.json()
            return data['choices'][0]['message']['content']
            
        except requests.Timeout:
            return "La consulta tardó demasiado en procesarse. Intenta de nuevo."
        except Exception as e:
            return f"Error al procesar la consulta: {str(e)}"

    def analizar_pregunta(self, pregunta):
        """
        Función principal que analiza si la pregunta está en contexto
        y genera una respuesta como vendedor de tienda
        """
        try:
            # Obtener todos los datos de la base de datos
            datos_contexto = self.obtener_datos_base()
            
            if not datos_contexto:
                return {
                    'fuera_de_contexto': True,
                    'respuesta': 'No pude acceder a la información de productos en este momento. Por favor, intenta más tarde.'
                }
            
            # Crear el contexto de productos para el vendedor
            contexto_productos = []
            for nombre, info in datos_contexto['productos'].items():
                # Precio principal (base o de lista)
                precio_principal = info['precio_base']
                precios_adicionales = ""
                
                if info['precios']:
                    precios_lista = [f"{lista}: {precio} Bs" for lista, precio in info['precios'].items()]
                    precios_adicionales = f" | Listas especiales: {', '.join(precios_lista)}"
                
                disponibilidad = "Disponible" if info['stock_global'] > 0 else "Sin stock"
                
                contexto_productos.append(
                    f"- {nombre}: {info['descripcion']} | Precio: {precio_principal} Bs{precios_adicionales} | Stock: {info['stock_global']} unidades ({disponibilidad})"
                )
            
            # Información de sucursales para delivery/retiro
            contexto_sucursales = []
            for nombre, info in datos_contexto['sucursales'].items():
                almacenes = ', '.join(info['almacenes']) if info['almacenes'] else 'Consultar disponibilidad'
                contexto_sucursales.append(
                    f"- {nombre}: {info['direccion']} | Almacenes: {almacenes}"
                )
            
            # Crear prompt para el vendedor
            prompt = f"""
ERES UN VENDEDOR EXPERTO DE TIENDA DE TECNOLOGÍA
INFORMACIÓN DE PRODUCTOS DISPONIBLES:
{chr(10).join(contexto_productos)}

SUCURSALES PARA RETIRO/DELIVERY:
{chr(10).join(contexto_sucursales)}

CONSULTA DEL CLIENTE: "{pregunta}"

INSTRUCCIONES IMPORTANTES:
1. Si la pregunta se relaciona con productos, precios, stock, disponibilidad, sucursales, especificaciones técnicas, comparaciones de productos, o consultas de compra - RESPONDE como un vendedor profesional
2. Si la pregunta NO tiene relación con productos tecnológicos, ventas, tienda o comercio - RESPONDE EXACTAMENTE: "No tengo información sobre eso. ¿Te puedo ayudar con algún producto?"
3. Actúa como vendedor: menciona beneficios, ayuda a decidir, sugiere productos similares si no hay stock
4. Incluye precios y disponibilidad cuando sea relevante
5. Mantén respuestas concisas pero útiles (máximo 4 líneas)
6. Si preguntan por categorías, menciona productos disponibles de esa categoría

RESPUESTA DEL VENDEDOR:
"""
            
            # Procesar con OpenAI
            respuesta_ai = self.procesar_con_openai(prompt)
            
            # Verificar si está fuera de contexto
            frase_fuera_contexto = "No tengo información sobre eso. ¿Te puedo ayudar con algún producto?"
            es_fuera_contexto = frase_fuera_contexto in respuesta_ai
            
            return {
                'fuera_de_contexto': es_fuera_contexto,
                'respuesta': respuesta_ai.strip()
            }
            
        except Exception as e:
            print(f"Error en analizar_pregunta: {e}")
            return {
                'fuera_de_contexto': True,
                'respuesta': 'Error interno al procesar la consulta. Por favor, intenta nuevamente.'
            }