import mysql.connector
import json
import requests
from datetime import datetime

class GeneradorIntereses:
    def __init__(self):
        """
        Inicializar el generador de intereses
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

    def obtener_conversaciones_cliente(self, telefono, tipo_conversacion):
        """
        Obtiene las conversaciones del cliente según el tipo solicitado
        
        Args:
            telefono (str): Número de teléfono del cliente
            tipo_conversacion (str): 'inicial_3' o 'final_3'
        
        Returns:
            list: Lista de mensajes de las conversaciones
        """
        try:
            conexion = mysql.connector.connect(**self.db_config)
            cursor = conexion.cursor(dictionary=True)
            
            # Verificar si el cliente existe
            cursor.execute("SELECT id_cliente FROM cliente WHERE telefono = %s", (telefono,))
            cliente = cursor.fetchone()
            
            if not cliente:
                conexion.close()
                return None  # Cliente no existe
            
            id_cliente = cliente['id_cliente']
            
            # Obtener conversaciones según el tipo
            if tipo_conversacion.startswith('inicial'):
                # Extraer número de conversaciones (inicial_3 -> 3)
                numero = int(tipo_conversacion.split('_')[1])
                cursor.execute("""
                    SELECT c.id_conversacion, c.fecha_inicio
                    FROM conversacion c
                    WHERE c.id_cliente = %s
                    ORDER BY c.fecha_inicio ASC
                    LIMIT %s
                """, (id_cliente, numero))
                
            elif tipo_conversacion.startswith('final'):
                # Extraer número de conversaciones (final_3 -> 3)
                numero = int(tipo_conversacion.split('_')[1])
                cursor.execute("""
                    SELECT c.id_conversacion, c.fecha_inicio
                    FROM conversacion c
                    WHERE c.id_cliente = %s
                    ORDER BY c.fecha_inicio DESC
                    LIMIT %s
                """, (id_cliente, numero))
            
            conversaciones = cursor.fetchall()
            
            if not conversaciones:
                conexion.close()
                return []
            
            # Obtener todos los mensajes de estas conversaciones
            ids_conversaciones = [str(conv['id_conversacion']) for conv in conversaciones]
            placeholders = ','.join(['%s'] * len(ids_conversaciones))
            
            cursor.execute(f"""
                SELECT m.contenido, m.emisor, m.fecha_envio, c.fecha_inicio
                FROM mensaje m
                JOIN conversacion c ON m.id_conversacion = c.id_conversacion
                WHERE m.id_conversacion IN ({placeholders})
                ORDER BY c.fecha_inicio, m.fecha_envio
            """, ids_conversaciones)
            
            mensajes = cursor.fetchall()
            conexion.close()
            
            return mensajes
            
        except Exception as e:
            print(f"Error al obtener conversaciones: {e}")
            return []

    def obtener_productos_disponibles(self):
        """
        Obtiene la lista de productos disponibles en la base de datos
        para hacer match con los intereses detectados
        """
        try:
            conexion = mysql.connector.connect(**self.db_config)
            cursor = conexion.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id_producto, nombre, descripcion
                FROM producto
                WHERE activo = TRUE
                ORDER BY nombre
            """)
            
            productos = cursor.fetchall()
            conexion.close()
            
            return {prod['nombre']: prod['id_producto'] for prod in productos}
            
        except Exception as e:
            print(f"Error al obtener productos: {e}")
            return {}

    def analizar_intereses_con_openai(self, mensajes, productos_disponibles):
        """
        Usa OpenAI para analizar las conversaciones y detectar intereses en productos
        
        Args:
            mensajes (list): Lista de mensajes de las conversaciones
            productos_disponibles (dict): Diccionario de productos {nombre: id}
        
        Returns:
            list: Array de objetos con formato [{"nombre": "producto", "nivel_interes": "alto"}]
        """
        try:
            # Construir el contexto de conversación
            contexto_conversacion = []
            for msg in mensajes:
                emisor = "Cliente" if msg['emisor'] == 'usuario' else "Vendedor"
                contexto_conversacion.append(f"{emisor}: {msg['contenido']}")
            
            conversacion_texto = "\n".join(contexto_conversacion)
            productos_lista = list(productos_disponibles.keys())
            
            # Prompt para OpenAI
            prompt = f"""
PRODUCTOS DISPONIBLES EN LA TIENDA:
{', '.join(productos_lista)}

CONVERSACIÓN DEL CLIENTE:
{conversacion_texto}

INSTRUCCIONES:
1. Analiza la conversación y detecta qué productos mencionó o preguntó el cliente
2. SOLO considera productos que están en la lista de productos disponibles
3. Determina el nivel de interés: "bajo", "medio", "alto"
4. DEBES devolver ÚNICAMENTE un array JSON válido con este formato exacto:
[{{"nombre": "nombre_exacto_del_producto", "nivel_interes": "alto"}}]

REGLAS IMPORTANTES:
- Los nombres deben coincidir EXACTAMENTE con los de la lista de productos disponibles
- Si el cliente preguntó precio o características = "alto"
- Si mencionó o mostró curiosidad = "medio"  
- Si solo lo nombró de pasada = "bajo"
- Si no hay interés en ningún producto, devuelve: []

RESPUESTA (solo JSON):
"""
            
            # Llamada a OpenAI
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
                        'content': 'Eres un analizador de intereses de clientes. SIEMPRE responde únicamente con JSON válido.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.1,  # Muy bajo para respuestas consistentes
                'max_tokens': 300
            }
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                print(f"Error en API OpenAI: {response.status_code}")
                return []
            
            data = response.json()
            respuesta_ai = data['choices'][0]['message']['content'].strip()
            
            # Intentar parsear el JSON
            try:
                intereses = json.loads(respuesta_ai)
                # Validar que sea una lista
                if isinstance(intereses, list):
                    return intereses
                else:
                    print(f"Respuesta no es lista: {respuesta_ai}")
                    return []
            except json.JSONDecodeError:
                print(f"Error al parsear JSON: {respuesta_ai}")
                return []
            
        except Exception as e:
            print(f"Error en análisis de intereses: {e}")
            return []

    def guardar_intereses_en_bd(self, telefono, intereses, productos_disponibles):
        """
        Guarda o actualiza los intereses del cliente en la base de datos
        
        Args:
            telefono (str): Teléfono del cliente
            intereses (list): Lista de intereses detectados
            productos_disponibles (dict): Diccionario de productos {nombre: id}
        
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            conexion = mysql.connector.connect(**self.db_config)
            cursor = conexion.cursor()
            
            # Obtener ID del cliente
            cursor.execute("SELECT id_cliente FROM cliente WHERE telefono = %s", (telefono,))
            cliente = cursor.fetchone()
            
            if not cliente:
                conexion.close()
                return False
            
            id_cliente = cliente[0]
            
            # Procesar cada interés detectado
            for interes in intereses:
                nombre_producto = interes.get('nombre')
                nivel_interes = interes.get('nivel_interes')
                
                # Verificar que el producto existe en nuestra BD
                if nombre_producto not in productos_disponibles:
                    print(f"Producto no encontrado: {nombre_producto}")
                    continue
                
                id_producto = productos_disponibles[nombre_producto]
                
                # Verificar si ya existe un interés para este cliente-producto
                cursor.execute("""
                    SELECT nivel_interes FROM interes 
                    WHERE id_cliente = %s AND id_producto = %s AND activo = TRUE
                """, (id_cliente, id_producto))
                
                interes_existente = cursor.fetchone()
                
                if interes_existente:
                    # Si el nivel es diferente, actualizar
                    if interes_existente[0] != nivel_interes:
                        cursor.execute("""
                            UPDATE interes 
                            SET nivel_interes = %s, fecha_interes = CURRENT_TIMESTAMP
                            WHERE id_cliente = %s AND id_producto = %s AND activo = TRUE
                        """, (nivel_interes, id_cliente, id_producto))
                        print(f"Actualizado interés: {nombre_producto} -> {nivel_interes}")
                else:
                    # Insertar nuevo interés
                    cursor.execute("""
                        INSERT INTO interes (id_cliente, id_producto, nivel_interes)
                        VALUES (%s, %s, %s)
                    """, (id_cliente, id_producto, nivel_interes))
                    print(f"Nuevo interés: {nombre_producto} -> {nivel_interes}")
            
            conexion.commit()
            conexion.close()
            return True
            
        except Exception as e:
            print(f"Error al guardar intereses: {e}")
            return False

    def procesar_intereses_cliente(self, telefono, tipo_conversacion):
        """
        Función principal que procesa los intereses de un cliente
        
        Args:
            telefono (str): Número de teléfono del cliente
            tipo_conversacion (str): 'inicial_3', 'final_3', etc.
        
        Returns:
            dict: Respuesta con estado del proceso
        """
        try:
            # 1. Obtener conversaciones del cliente
            mensajes = self.obtener_conversaciones_cliente(telefono, tipo_conversacion)
            
            if mensajes is None:
                return {
                    'estado': 'error',
                    'mensaje': 'No existe el usuario'
                }
            
            if not mensajes:
                return {
                    'estado': 'exito',
                    'mensaje': 'Proceso correctamente',
                    'detalle': 'Sin conversaciones para analizar'
                }
            
            # 2. Obtener productos disponibles
            productos_disponibles = self.obtener_productos_disponibles()
            
            if not productos_disponibles:
                return {
                    'estado': 'error',
                    'mensaje': 'Proceso incorrecto',
                    'detalle': 'No se pudieron obtener productos'
                }
            
            # 3. Analizar intereses con OpenAI
            intereses = self.analizar_intereses_con_openai(mensajes, productos_disponibles)
            
            # 4. Guardar intereses en la base de datos
            if intereses:
                exito = self.guardar_intereses_en_bd(telefono, intereses, productos_disponibles)
                
                if exito:
                    return {
                        'estado': 'exito',
                        'mensaje': 'Proceso correctamente',
                        'intereses_detectados': intereses
                    }
                else:
                    return {
                        'estado': 'error',
                        'mensaje': 'Proceso incorrecto',
                        'detalle': 'Error al guardar intereses'
                    }
            else:
                return {
                    'estado': 'exito',
                    'mensaje': 'Proceso correctamente',
                    'detalle': 'Sin intereses detectados'
                }
            
        except Exception as e:
            print(f"Error en procesar_intereses_cliente: {e}")
            return {
                'estado': 'error',
                'mensaje': 'Proceso incorrecto',
                'detalle': str(e)
            }