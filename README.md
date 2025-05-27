# 🤖 Bot Analizador de Contexto - Instalación Rápida

## 🚀 Instalación

### 1. Crear entorno virtual

```bash
python -m venv venv
# Activar:
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Instalar dependencias básicas

```bash
pip install flask flask-cors mysql-connector-python requests
```

### 3. Instalar dependencias nuevas

```bash
pip install playwright
pip install cloudinary
playwright install chromium
```

### 4. Configurar base de datos

```python
# En analizador.py, generador_intereses.py, generador_imagen.py
self.db_config = {
    'host': 'localhost',
    'user': 'root',                    # 👈 Tu usuario MySQL
    'password': 'tu_password_aqui',    # 👈 Tu contraseña MySQL
    'database': 'bot_productos_db',
    'charset': 'utf8mb4'
}
```

### 5. Configurar Cloudinary

```python
# En generador_imagen.py línea 24
cloudinary.config(
    cloud_name = "da9xsfose",
    api_key = "422253887739587",
    api_secret = "h6lb1iQebGIwHMfsoVPBO61dyvI",  # 👈 Cambiar por tu API secret
    secure = True
)
```

### 6. Ejecutar base de datos

Ejecuta el script SQL que tienes para crear `bot_productos_db` con todas las tablas

### 7. Iniciar servidor

```bash
python app.py
```

## 🧪 Probar APIs

### 1. Consulta sobre productos:

```bash
curl -X POST http://localhost:5000/api/verificar_contexto \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "que laptops tienes?"}'
```

### 2. Consulta fuera de contexto:

```bash
curl -X POST http://localhost:5000/api/verificar_contexto \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "como cocinar arroz?"}'
```

### 3. Generar intereses del cliente:

```bash
curl -X POST http://localhost:5000/api/generador_intereses \
  -H "Content-Type: application/json" \
  -d '{"usuario_telefono": "78452415", "conversacion": "inicial_3"}'
```

### 4. Generar imagen personalizada:

```bash
curl -X POST http://localhost:5000/api/generar_imagen \
  -H "Content-Type: application/json" \
  -d '{"usuario_telefono": "78452415"}'
```

### 5. Estado del servidor:

```bash
curl http://localhost:5000/api/health
```

## 📋 Endpoints Disponibles

| Método | Endpoint                   | Descripción                           |
| ------ | -------------------------- | ------------------------------------- |
| `POST` | `/api/verificar_contexto`  | Analiza preguntas como vendedor       |
| `POST` | `/api/generador_intereses` | Detecta intereses en conversaciones   |
| `POST` | `/api/generar_imagen`      | Crea imagen personalizada del cliente |
| `GET`  | `/api/health`              | Estado del servidor                   |

## 🔧 Problemas Comunes

**Error MySQL:** Verifica usuario/contraseña en los 3 archivos Python
**Error OpenAI:** Verifica tu API key en `analizador.py` y `generador_intereses.py`  
**Error Cloudinary:** Verifica tu API secret en `generador_imagen.py`
**Error Playwright:** Ejecuta `playwright install chromium`
**Puerto ocupado:** Cambia puerto en `app.py` línea final

## 📁 Estructura Final

```
mi_bot_productos/
├── app.py                    # Servidor principal
├── analizador.py            # Consultas de productos
├── generador_intereses.py   # Análisis de conversaciones
├── generador_imagen.py      # Generación de imágenes
├── requirements.txt         # Dependencias
└── venv/                   # Entorno virtual
```

## 🎯 Funcionalidades

✅ **Análisis de contexto:** Responde como vendedor experto  
✅ **Detección de intereses:** Analiza conversaciones del cliente  
✅ **Imágenes personalizadas:** Genera contenido visual único  
✅ **Base de datos completa:** Productos, stock, precios, clientes  
✅ **API REST:** Endpoints listos para integrar

¡Listo! 🎉
