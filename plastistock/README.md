# PlastiStock — Demo de Inventarios

Sistema de inventarios para bolsas de plástico.  
Desarrollado con Flask + SQLite + HTML/CSS vanilla.

---

## ▶ Instalación y arranque

### 1. Requisitos
- Python 3.9 o superior
- pip

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Correr el servidor
```bash
python app.py
```

### 4. Abrir en el navegador
```
http://127.0.0.1:5000
```

La base de datos `plastistock.db` se crea automáticamente con todos los
productos cargados de las imágenes y 4 clientes de ejemplo.

---

## 📦 Módulos incluidos

| Módulo       | Funcionalidades                                              |
|------------- |--------------------------------------------------------------|
| Inventario   | Lista todos los SKUs con precios, stock y estado             |
|              | Buscar por nombre o referencia                               |
|              | Editar cualquier campo (nombre, medida, precios, stock)      |
| Clientes     | Directorio completo con RFC y línea de crédito               |
|              | Crear / editar clientes                                      |
|              | Marcar como activo / inactivo                                |
| Cotizaciones | Crear cotizaciones con múltiples productos                    |
|              | Ver detalle de cada cotización                               |
|              | Cambiar estado: Borrador → Enviada → Aprobada / Cancelada    |
| Pedidos      | Crear pedidos (descuenta stock automáticamente)              |
|              | Seguimiento de estado: Pendiente → En camino → Entregado     |
|              | Vincular pedido a una cotización aprobada                    |

---

## 🗂 Estructura del proyecto

```
plastistock/
├── app.py              # Backend Flask + rutas + lógica
├── requirements.txt    # Dependencias
├── plastistock.db      # SQLite (se crea al arrancar)
└── templates/
    ├── base.html           # Layout base (sidebar + estilos)
    ├── inventario.html
    ├── editar_producto.html
    ├── clientes.html
    ├── form_cliente.html
    ├── cotizaciones.html
    ├── form_cotizacion.html
    ├── ver_cotizacion.html
    ├── pedidos.html
    └── form_pedido.html
```

---

## 📱 Próximos pasos (APK / móvil)

Para la versión móvil se recomienda:
- **Kivy + KivyMD** — para generar APK nativo con Python
- **BeeWare (Toga)** — alternativa más moderna
- O mantener Flask como API y construir el frontend con **React Native** / **Flutter**

---

## 🔑 Productos cargados

22 SKUs de las imágenes proporcionadas:
- S-11024 al S-11100 (bolsas de basura coextruidas, super bolsas OXO)
- S-13000, S-16100, S-17036, S-17037, S-17075 (bolsas especiales y ecológicas)
- S-18201 (película stretch)
