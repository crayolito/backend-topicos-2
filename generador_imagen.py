import mysql.connector
import cloudinary
import cloudinary.uploader
from playwright.sync_api import sync_playwright
import base64
from io import BytesIO

class GeneradorImagen:
    def __init__(self):
        """
        Inicializar el generador de imágenes
        Configura la conexión a la base de datos y Cloudinary
        """
        # Configuración de la base de datos MySQL
        self.db_config = {
            'host': 'localhost',
            'user': 'root',          # Cambia esto por tu usuario de MySQL
            'password': 'clave123',  # Cambia esto por tu contraseña de MySQL
            'database': 'bot_productos_db',
            'charset': 'utf8mb4'
        }
        
        # Configuración de Cloudinary
        cloudinary.config( 
            cloud_name = "da9xsfose", 
            api_key = "422253887739587", 
            api_secret = "h6lb1iQebGIwHMfsoVPBO61dyvI",
            secure = True
        )

    def obtener_intereses_cliente(self, telefono):
        """
        Obtiene todos los intereses del cliente con información de productos
        
        Args:
            telefono (str): Número de teléfono del cliente
        
        Returns:
            list: Lista de productos con nivel de interés, precio e imagen
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
            
            # Obtener intereses con información de productos y precios
            cursor.execute("""
                SELECT 
                    p.nombre as producto_nombre,
                    p.descripcion,
                    p.precio_base,
                    p.imagen,
                    i.nivel_interes,
                    COALESCE(plp.precio, p.precio_base) as precio_final,
                    lp.nombre_lista
                FROM interes i
                JOIN producto p ON i.id_producto = p.id_producto
                LEFT JOIN productolistaprecio plp ON p.id_producto = plp.id_producto
                LEFT JOIN listaprecio lp ON plp.id_lista = lp.id_lista AND lp.activo = TRUE
                WHERE i.id_cliente = %s AND i.activo = TRUE AND p.activo = TRUE
                ORDER BY 
                    CASE i.nivel_interes 
                        WHEN 'alto' THEN 1 
                        WHEN 'medio' THEN 2 
                        WHEN 'bajo' THEN 3 
                    END,
                    p.nombre
            """, (id_cliente,))
            
            intereses = cursor.fetchall()
            conexion.close()
            
            # Procesar y organizar los datos
            productos_procesados = {}
            
            for row in intereses:
                nombre = row['producto_nombre']
                
                if nombre not in productos_procesados:
                    productos_procesados[nombre] = {
                        'nombre': nombre,
                        'descripcion': row['descripcion'],
                        'nivel_interes': row['nivel_interes'],
                        'precio_base': float(row['precio_base']) if row['precio_base'] else 0,
                        'imagen': row['imagen'] if row['imagen'] else '',
                        'precio_final': float(row['precio_final']) if row['precio_final'] else 0,
                        'lista_precio': row['nombre_lista']
                    }
            
            return list(productos_procesados.values())
            
        except Exception as e:
            print(f"Error al obtener intereses del cliente: {e}")
            return []

    def generar_html_lista_productos(self, productos):
        """
        Genera el HTML para mostrar una lista elegante de todos los productos de interés
        Diseño blanco y negro elegante con tabla bonita
        
        Args:
            productos (list): Lista de productos con información
        
        Returns:
            str: HTML generado para la lista de productos
        """
        # Función auxiliar para generar filas de productos
        def generar_fila_producto(producto):
            # Usar imagen por defecto si está vacía
            imagen_url = producto['imagen'] if producto['imagen'] else "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg"
            precio_mostrar = producto['precio_final'] if producto['precio_final'] > 0 else producto['precio_base']
            
            # Emoji según el nivel de interés
            emoji_interes = {
                'alto': '🔥',
                'medio': '👍',
                'bajo': '💡'
            }.get(producto['nivel_interes'], '⭐')
            
            return f"""
            <tr>
                <td class="producto-img">
                    <img src="{imagen_url}" alt="{producto['nombre']}">
                </td>
                <td class="producto-info">
                    <div class="nombre">{producto['nombre']}</div>
                    <div class="interes">{emoji_interes} {producto['nivel_interes'].title()}</div>
                </td>
                <td class="precio">
                    <div class="precio-valor">{precio_mostrar} Bs</div>
                </td>
            </tr>
            """
        
        # Generar todas las filas de productos
        filas_productos = ''.join([generar_fila_producto(p) for p in productos])
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
                
                body {{
                    margin: 0;
                    padding: 20px;
                    width: 800px;
                    min-height: 600px;
                    background: #f8fafc;
                    font-family: 'Inter', sans-serif;
                    color: #1e293b;
                }}
                
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding: 20px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                
                .titulo {{
                    font-size: 28px;
                    font-weight: 700;
                    color: #0f172a;
                    margin: 0 0 8px 0;
                }}
                
                .subtitulo {{
                    font-size: 16px;
                    color: #64748b;
                    margin: 0;
                }}
                
                .tabla-container {{
                    background: white;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                
                .tabla {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                
                .tabla thead {{
                    background: #f1f5f9;
                }}
                
                .tabla th {{
                    padding: 16px;
                    text-align: left;
                    font-weight: 600;
                    font-size: 14px;
                    color: #475569;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                
                .tabla td {{
                    padding: 16px;
                    border-bottom: 1px solid #e2e8f0;
                    vertical-align: middle;
                }}
                
                .tabla tr:last-child td {{
                    border-bottom: none;
                }}
                
                .tabla tr:hover {{
                    background: #f8fafc;
                }}
                
                .producto-img img {{
                    width: 60px;
                    height: 60px;
                    border-radius: 8px;
                    object-fit: cover;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                
                .producto-info .nombre {{
                    font-weight: 600;
                    font-size: 16px;
                    color: #0f172a;
                    margin-bottom: 4px;
                }}
                
                .producto-info .interes {{
                    font-size: 14px;
                    color: #64748b;
                    display: flex;
                    align-items: center;
                    gap: 4px;
                }}
                
                .precio {{
                    text-align: right;
                }}
                
                .precio-valor {{
                    font-size: 18px;
                    font-weight: 700;
                    color: #059669;
                }}
                
                .footer {{
                    text-align: center;
                    margin-top: 20px;
                    padding: 16px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                
                .footer-text {{
                    font-size: 14px;
                    color: #64748b;
                    margin: 0;
                }}
                
                .stats {{
                    display: flex;
                    justify-content: center;
                    gap: 30px;
                    margin-top: 12px;
                }}
                
                .stat {{
                    text-align: center;
                }}
                
                .stat-numero {{
                    font-size: 20px;
                    font-weight: 700;
                    color: #0f172a;
                }}
                
                .stat-label {{
                    font-size: 12px;
                    color: #64748b;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 class="titulo">Productos que te pueden interesar</h1>
                <p class="subtitulo">Basado en tus conversaciones y preferencias</p>
            </div>
            
            <div class="tabla-container">
                <table class="tabla">
                    <thead>
                        <tr>
                            <th>Imagen</th>
                            <th>Producto</th>
                            <th>Precio</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_productos}
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                <p class="footer-text">Recomendaciones personalizadas para ti</p>
                <div class="stats">
                    <div class="stat">
                        <div class="stat-numero">{len(productos)}</div>
                        <div class="stat-label">Productos</div>
                    </div>
                    <div class="stat">
                        <div class="stat-numero">{len([p for p in productos if p['nivel_interes'] == 'alto'])}</div>
                        <div class="stat-label">Alto Interés</div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template

    def generar_imagen_con_playwright(self, html_content):
        """
        Genera la imagen usando Playwright basado en el HTML
        
        Args:
            html_content (str): Contenido HTML para convertir a imagen
        
        Returns:
            bytes: Imagen en bytes
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                # Tamaño para la tabla de productos
                page.set_viewport_size({"width": 800, "height": 1000})
                page.set_content(html_content)
                
                # Esperar a que carguen todas las imágenes
                page.wait_for_load_state('networkidle')
                
                # Tomar screenshot de toda la página
                screenshot_bytes = page.screenshot(full_page=True, type='png')
                browser.close()
                
                return screenshot_bytes
                
        except Exception as e:
            print(f"Error al generar imagen con Playwright: {e}")
            return None

    def subir_imagen_cloudinary(self, imagen_bytes, telefono):
        """
        Sube la imagen a Cloudinary y retorna la URL
        
        Args:
            imagen_bytes (bytes): Imagen en bytes
            telefono (str): Teléfono del cliente para el public_id
        
        Returns:
            str: URL de la imagen subida o None si hay error
        """
        try:
            # Crear un nombre único para el archivo
            public_id = f"lista_intereses_{telefono}"
            
            # Convertir bytes a base64 para Cloudinary
            imagen_base64 = base64.b64encode(imagen_bytes).decode('utf-8')
            data_uri = f"data:image/png;base64,{imagen_base64}"
            
            # Subir a Cloudinary
            upload_result = cloudinary.uploader.upload(
                data_uri,
                public_id=public_id,
                overwrite=True,
                resource_type="image"
            )
            
            return upload_result["secure_url"]
            
        except Exception as e:
            print(f"Error al subir imagen a Cloudinary: {e}")
            return None

    def generar_imagen_cliente(self, telefono):
        """
        Función principal que genera la imagen con LISTA de productos de interés
        
        Args:
            telefono (str): Número de teléfono del cliente
        
        Returns:
            dict: Solo urlImagen y bytesImagen
        """
        try:
            # 1. Obtener TODOS los intereses del cliente
            intereses = self.obtener_intereses_cliente(telefono)
            
            if intereses is None:
                return {
                    'estado': 'error',
                    'mensaje': 'Cliente no encontrado'
                }
            
            if not intereses:
                return {
                    'estado': 'error',
                    'mensaje': 'Cliente sin intereses registrados'
                }
            
            # 2. Generar HTML con LISTA COMPLETA de productos (tabla elegante)
            html_content = self.generar_html_lista_productos(intereses)
            
            # 3. Generar imagen con Playwright
            imagen_bytes = self.generar_imagen_con_playwright(html_content)
            
            if not imagen_bytes:
                return {
                    'estado': 'error',
                    'mensaje': 'Error al generar la imagen'
                }
            
            # 4. Subir imagen a Cloudinary
            url_imagen = self.subir_imagen_cloudinary(imagen_bytes, telefono)
            
            if not url_imagen:
                return {
                    'estado': 'error',
                    'mensaje': 'Error al subir imagen a Cloudinary'
                }
            
            # 5. Convertir bytes a base64 para enviar al cliente
            imagen_base64 = base64.b64encode(imagen_bytes).decode('utf-8')
            
            # RESPUESTA SIMPLE: Solo URL e imagen en bytes
            return {
                'urlImagen': url_imagen,
                'bytesImagen': imagen_base64
            }
            
        except Exception as e:
            print(f"Error en generar_imagen_cliente: {e}")
            return {
                'estado': 'error',
                'mensaje': 'Error interno al generar imagen',
                'detalle': str(e)
            }