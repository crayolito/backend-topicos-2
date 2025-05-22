# 🤖 Bot Analizador de Contexto - Instalación Rápida

### 2. Crear entorno virtual

````bash
python -m venv venv

# Activar:
# Windows:
venv\Scripts\activate

### 3. Instalar dependencias
```bash
pip install flask flask-cors mysql-connector-python requests
````

````python
# Base de datos
self.db_config = {
    'host': 'localhost',
    'user': 'root',                    # 👈 Tu usuario MySQL
    'password': 'tu_password_aqui',    # 👈 Tu contraseña MySQL
    'database': 'bot_productos_db',
    'charset': 'utf8mb4'
}


### 6. Ejecutar base de datos
Ejecuta el script SQL que ya tienes para crear `bot_productos_db`

### 7. Iniciar servidor
```bash
python app.py
````

## 🧪 Probar API

### Consulta sobre productos:

```bash
curl -X POST http://localhost:5000/api/consulta \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "que laptops tienes?"}'
```

### Consulta fuera de contexto:

```bash
curl -X POST http://localhost:5000/api/consulta \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "como cocinar arroz?"}'
```

## 🔧 Problemas Comunes

**Error MySQL:** Verifica usuario/contraseña en `analizador.py`
**Error OpenAI:** Verifica tu API key
**Puerto ocupado:** Cambia puerto en `app.py` línea final

## 📁 Estructura Final

```
mi_bot_productos/
├── app.py
├── analizador.py
└── venv/
```

¡Listo! 🎉
