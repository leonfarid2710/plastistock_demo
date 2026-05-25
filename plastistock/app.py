from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import sqlite3, os, hashlib
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'leissam-demo-2026-key')
DB = os.environ.get("DB_PATH", "/tmp/plastistock.db")

# ── CREDENCIALES DEMO ────────────────────────────────────────────────────────
USUARIOS = {
    'admin':  hashlib.sha256(b'leissam2026').hexdigest(),
    'demo':   hashlib.sha256(b'demo1234').hexdigest(),
}

def login_requerido(f):
    from functools import wraps
    @wraps(f)
    def decorada(*args, **kwargs):
        if not session.get('usuario'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorada

# ── DB helpers ───────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ref TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            medida TEXT,
            contenido_paquete TEXT,
            contenido_bulto INTEGER,
            costo REAL,
            precio_unitario_iva REAL,
            precio_margen REAL,
            costo_bulto_iva REAL,
            stock INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT NOT NULL,
            contacto TEXT,
            telefono TEXT,
            email TEXT,
            rfc TEXT,
            credito REAL DEFAULT 0,
            activo INTEGER DEFAULT 1,
            creado TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS cotizaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio TEXT UNIQUE NOT NULL,
            cliente_id INTEGER,
            fecha TEXT DEFAULT (datetime('now')),
            vigencia TEXT,
            total REAL DEFAULT 0,
            estado TEXT DEFAULT 'Borrador',
            notas TEXT,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id)
        );
        CREATE TABLE IF NOT EXISTS cotizacion_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cotizacion_id INTEGER,
            producto_id INTEGER,
            cantidad INTEGER,
            precio_unitario REAL,
            subtotal REAL,
            FOREIGN KEY(cotizacion_id) REFERENCES cotizaciones(id),
            FOREIGN KEY(producto_id) REFERENCES productos(id)
        );
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folio TEXT UNIQUE NOT NULL,
            cliente_id INTEGER,
            cotizacion_id INTEGER,
            fecha TEXT DEFAULT (datetime('now')),
            fecha_entrega TEXT,
            total REAL DEFAULT 0,
            estado TEXT DEFAULT 'Pendiente',
            notas TEXT,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id),
            FOREIGN KEY(cotizacion_id) REFERENCES cotizaciones(id)
        );
        CREATE TABLE IF NOT EXISTS pedido_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER,
            producto_id INTEGER,
            cantidad INTEGER,
            precio_unitario REAL,
            subtotal REAL,
            FOREIGN KEY(pedido_id) REFERENCES pedidos(id),
            FOREIGN KEY(producto_id) REFERENCES productos(id)
        );
        """)

        # ── Productos ────────────────────────────────────────────────────────
        count = db.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
        if count == 0:
            productos = [
                ('S-13000','BOLSA HIELO NATURAL 25 X 65 CM','25x65 cm','50 bolsas',30,59.00,68.44,87.60,None),
                ('S-16100','ZIPPER FLEX SANDWICH 15.5 X 17.5 CM','15.5x17.5 cm','50 bolsas',20,30.00,34.80,44.54,None),
                ('S-17036','BOLSA ECOLOGICA RAFIA MEDIANA',None,'1 pieza',1,20.00,23.20,29.70,None),
                ('S-17037','BOLSA ECOLOGICA RAFIA EXTRAGRANDE',None,'1 pieza',1,20.00,23.20,29.70,None),
                ('S-17075','BOLSA RAFIA + BOPP 38 X 32 X 16 CM','38x32x16 cm','1 pieza',1,20.00,23.20,29.70,None),
                ('S-18201','PELICULA STRETCH 18" 1000 PIES','18"','1 rollo',1,140.00,162.40,207.87,None),
                ('S-11024','BASURA COEXTRUIDA NEGRA 50 X 70 CM CAL. 200','50x70 cm','1',25,37.00,42.92,54.94,None),
                ('S-11025','BASURA COEXTRUIDA NEGRA 60 X 90 CM CAL. 260','60x90 cm','1',25,37.00,42.92,54.94,None),
                ('S-11026','BASURA COEXTRUIDA NEGRA 75 X 90 CM CAL. 260','75x90 cm','1',25,37.00,42.92,54.94,None),
                ('S-11027','BASURA COEXTRUIDA NEGRA 90 X 120 CM CAL. 300','90x120 cm','1',25,37.00,42.92,54.94,None),
                ('S-11033','SUPER BOLSA ECONOMICA NARANJA 62 X 85 CM','62x85 cm','18 bolsas',36,24.00,27.84,35.64,None),
                ('S-11035','SUPER BOLSA ECONOMICA NEGRA 62 X 85 CM','62x85 cm','18 bolsas',36,24.00,27.84,35.64,None),
                ('S-11040','SUPER BOLSA ECONOMICA NEGRA 90 X 120 CM','90x120 cm','10 bolsas',27,30.00,34.80,44.54,None),
                ('S-11041','SUPER BOLSA ECONOMICA VERDE 90 X 120 CM','90x120 cm','10 bolsas',27,30.00,34.80,44.54,None),
                ('S-11046','SUPER BOLSA OXO BLANCA 50 X 60 CM','50x60 cm','20 bolsas',40,16.00,18.56,23.76,None),
                ('S-11048','SUPER BOLSA OXO NEGRA 75 X 90 CM','75x90 cm','15 bolsas',20,30.00,34.80,44.54,None),
                ('S-11049','SUPER BOLSA OXO NEGRA 90 X 120 CM','90x120 cm','10 bolsas',20,33.00,38.28,49.00,None),
                ('S-11070','BASURA COEXTRUIDA NEGRA 50 X 70 CM CAL. 144','50x70 cm','30 bolsas',25,40.00,46.40,59.39,None),
                ('S-11071','BASURA COEXTRUIDA NEGRA 60 X 90 CM CAL. 175','60x90 cm','16 bolsas',25,40.00,46.40,59.39,None),
                ('S-11072','BASURA COEXTRUIDA NEGRA 75 X 90 CM CAL. 175','75x90 cm','13 bolsas',25,40.00,46.40,59.39,None),
                ('S-11073','BASURA COEXTRUIDA NEGRA 90 X 120 CM CAL. 200','90x120 cm','7 bolsas',25,40.00,46.40,59.39,None),
                ('S-11100','BASURA COEXTRUIDA NEGRA 50 X 70 CM CAL. 144','50x70 cm','1 paquete',12,600.00,696.00,890.88,None),
            ]
            db.executemany("""
                INSERT INTO productos (ref,nombre,medida,contenido_paquete,contenido_bulto,
                    costo,precio_unitario_iva,precio_margen,costo_bulto_iva,stock)
                VALUES (?,?,?,?,?,?,?,?,?,100)
            """, productos)
            # algunos con stock bajo para el dashboard
            db.execute("UPDATE productos SET stock=12 WHERE ref='S-11049'")
            db.execute("UPDATE productos SET stock=8  WHERE ref='S-17036'")
            db.execute("UPDATE productos SET stock=0  WHERE ref='S-17037'")
            db.execute("UPDATE productos SET stock=25 WHERE ref='S-11046'")

        # ── Clientes ─────────────────────────────────────────────────────────
        cc = db.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        if cc == 0:
            db.executemany("""
                INSERT INTO clientes (empresa,contacto,telefono,email,rfc,credito)
                VALUES (?,?,?,?,?,?)
            """, [
                ('Chedraui Campeche','Ana Solís','981-234-5678','ana@chedraui.com','CHE910302AA1',50000),
                ('Farmacias Cruz Verde','Luis Méndez','981-345-6789','luis@cruzverde.com','FCV020501BB2',30000),
                ('Mercado Central','María Díaz','981-456-7890','maria@mercado.com','MCE870714CC3',15000),
                ('Cocina Don Pepe','José Ramírez','981-567-8901','jose@donpepe.com','CJP951220DD4',8000),
                ('Supermercado Familiar','Roberto Cruz','981-789-0123','roberto@familiar.com','SFM130815FF6',20000),
            ])

        # ── Cotizaciones de ejemplo ───────────────────────────────────────────
        cq = db.execute("SELECT COUNT(*) FROM cotizaciones").fetchone()[0]
        if cq == 0:
            # obtener IDs de clientes y productos
            clientes_ids = {r['empresa']: r['id'] for r in db.execute("SELECT id,empresa FROM clientes")}
            prods_ids    = {r['ref']: r['id'] for r in db.execute("SELECT id,ref FROM productos")}

            cots = [
                ('COT-101', clientes_ids['Chedraui Campeche'],    '2026-06-10', 18400.00, 'Aprobada',  'Entrega en almacén central'),
                ('COT-102', clientes_ids['Farmacias Cruz Verde'],  '2026-06-11', 7200.00,  'Enviada',   ''),
                ('COT-103', clientes_ids['Mercado Central'],       '2026-06-12', 12800.00, 'Pendiente', 'Revisar precios mayoreo'),
                ('COT-104', clientes_ids['Supermercado Familiar'], '2026-06-13', 9500.00,  'Aprobada',  ''),
                ('COT-105', clientes_ids['Cocina Don Pepe'],       '2026-06-14', 3400.00,  'Borrador',  ''),
                ('COT-106', clientes_ids['Chedraui Campeche'],     '2026-06-20', 13500.00, 'Cancelada', 'Cliente pospuso el pedido'),
            ]
            for folio, cid, vig, total, estado, notas in cots:
                db.execute("""INSERT INTO cotizaciones (folio,cliente_id,vigencia,total,estado,notas)
                    VALUES (?,?,?,?,?,?)""", (folio, cid, vig, total, estado, notas))

            cot_ids = {r['folio']: r['id'] for r in db.execute("SELECT id,folio FROM cotizaciones")}

            items_cot = [
                (cot_ids['COT-101'], prods_ids['S-11024'], 200, 54.94, 10988.00),
                (cot_ids['COT-101'], prods_ids['S-11033'], 130, 35.64,  4633.20),
                (cot_ids['COT-101'], prods_ids['S-11046'], 150, 23.76,  3564.00),
                (cot_ids['COT-102'], prods_ids['S-13000'],  50, 87.60,  4380.00),
                (cot_ids['COT-102'], prods_ids['S-16100'],  80, 44.54,  3563.20),
                (cot_ids['COT-103'], prods_ids['S-11040'], 180, 44.54,  8017.20),
                (cot_ids['COT-103'], prods_ids['S-11048'],  80, 44.54,  3563.20),
                (cot_ids['COT-103'], prods_ids['S-11049'],  40, 49.00,  1960.00),
                (cot_ids['COT-104'], prods_ids['S-11025'], 100, 54.94,  5494.00),
                (cot_ids['COT-104'], prods_ids['S-11026'],  80, 54.94,  4395.20),
                (cot_ids['COT-105'], prods_ids['S-11033'],  60, 35.64,  2138.40),
                (cot_ids['COT-105'], prods_ids['S-11035'],  60, 35.64,  2138.40),
                (cot_ids['COT-105'], prods_ids['S-13000'],  15, 87.60,  1314.00),
                (cot_ids['COT-106'], prods_ids['S-18201'],  40,207.87,  8314.80),
                (cot_ids['COT-106'], prods_ids['S-11070'],  90, 59.39,  5345.10),
            ]
            db.executemany("""INSERT INTO cotizacion_items
                (cotizacion_id,producto_id,cantidad,precio_unitario,subtotal)
                VALUES (?,?,?,?,?)""", items_cot)

        # ── Pedidos de ejemplo ────────────────────────────────────────────────
        pq = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        if pq == 0:
            clientes_ids = {r['empresa']: r['id'] for r in db.execute("SELECT id,empresa FROM clientes")}
            prods_ids    = {r['ref']: r['id'] for r in db.execute("SELECT id,ref FROM productos")}
            cot_ids      = {r['folio']: r['id'] for r in db.execute("SELECT id,folio FROM cotizaciones")}

            peds = [
                ('PED-201', clientes_ids['Chedraui Campeche'],    cot_ids.get('COT-101'), '2026-05-16', 18400.00, 'Entregado', ''),
                ('PED-202', clientes_ids['Mercado Central'],       None,                  '2026-05-17', 7600.00,  'En camino', 'Entregar en bodega norte'),
                ('PED-203', clientes_ids['Farmacias Cruz Verde'],  None,                  '2026-05-19', 8500.00,  'En camino', ''),
                ('PED-204', clientes_ids['Cocina Don Pepe'],       None,                  '2026-05-20', 3400.00,  'Pendiente', ''),
                ('PED-205', clientes_ids['Supermercado Familiar'], cot_ids.get('COT-104'), '2026-05-21',15000.00, 'Entregado', ''),
                ('PED-206', clientes_ids['Chedraui Campeche'],     None,                  '2026-05-22', 13500.00, 'Pendiente', 'Cliente solicitó factura'),
            ]
            for folio, cid, cotid, fent, total, estado, notas in peds:
                db.execute("""INSERT INTO pedidos
                    (folio,cliente_id,cotizacion_id,fecha_entrega,total,estado,notas)
                    VALUES (?,?,?,?,?,?,?)""", (folio, cid, cotid, fent, total, estado, notas))

            ped_ids = {r['folio']: r['id'] for r in db.execute("SELECT id,folio FROM pedidos")}

            items_ped = [
                (ped_ids['PED-201'], prods_ids['S-11024'], 200, 54.94, 10988.00),
                (ped_ids['PED-201'], prods_ids['S-11033'], 130, 35.64,  4633.20),
                (ped_ids['PED-201'], prods_ids['S-11046'], 150, 23.76,  3564.00),
                (ped_ids['PED-202'], prods_ids['S-11040'],  80, 44.54,  3563.20),
                (ped_ids['PED-202'], prods_ids['S-11048'],  90, 44.54,  4008.60),
                (ped_ids['PED-203'], prods_ids['S-13000'],  50, 87.60,  4380.00),
                (ped_ids['PED-203'], prods_ids['S-16100'],  90, 44.54,  4008.60),
                (ped_ids['PED-204'], prods_ids['S-11033'],  60, 35.64,  2138.40),
                (ped_ids['PED-204'], prods_ids['S-13000'],  15, 87.60,  1314.00),
                (ped_ids['PED-205'], prods_ids['S-11025'], 100, 54.94,  5494.00),
                (ped_ids['PED-205'], prods_ids['S-11026'],  80, 54.94,  4395.20),
                (ped_ids['PED-205'], prods_ids['S-11027'],  80, 54.94,  4395.20),
                (ped_ids['PED-206'], prods_ids['S-18201'],  40,207.87,  8314.80),
                (ped_ids['PED-206'], prods_ids['S-11070'],  90, 59.39,  5345.10),
            ]
            db.executemany("""INSERT INTO pedido_items
                (pedido_id,producto_id,cantidad,precio_unitario,subtotal)
                VALUES (?,?,?,?,?)""", items_ped)

        db.commit()

# ── LOGIN ────────────────────────────────────────────────────────────────────

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        usuario  = request.form.get('usuario','').strip().lower()
        password = hashlib.sha256(request.form.get('password','').encode()).hexdigest()
        if usuario in USUARIOS and USUARIOS[usuario] == password:
            session['usuario'] = usuario
            return redirect(url_for('dashboard'))
        error = 'Usuario o contraseña incorrectos'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
@login_requerido
def index():
    return redirect(url_for('dashboard'))

# INVENTARIO
@app.route('/inventario')
@login_requerido
def inventario():
    db = get_db()
    q = request.args.get('q','')
    if q:
        prods = db.execute("SELECT * FROM productos WHERE nombre LIKE ? OR ref LIKE ? ORDER BY ref",
                           (f'%{q}%', f'%{q}%')).fetchall()
    else:
        prods = db.execute("SELECT * FROM productos ORDER BY ref").fetchall()
    stats = {
        'total_skus':   db.execute("SELECT COUNT(*) FROM productos").fetchone()[0],
        'total_stock':  db.execute("SELECT SUM(stock) FROM productos").fetchone()[0] or 0,
        'stock_bajo':   db.execute("SELECT COUNT(*) FROM productos WHERE stock < 50 AND stock > 0").fetchone()[0],
        'agotados':     db.execute("SELECT COUNT(*) FROM productos WHERE stock = 0").fetchone()[0],
    }
    return render_template('inventario.html', productos=prods, stats=stats, q=q)

@app.route('/inventario/nuevo', methods=['GET','POST'])
@login_requerido
def nuevo_producto():
    db = get_db()
    if request.method == 'POST':
        try:
            db.execute("""INSERT INTO productos
                (ref,nombre,medida,contenido_paquete,contenido_bulto,
                 costo,precio_unitario_iva,precio_margen,stock)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (request.form['ref'].upper().strip(),
                 request.form['nombre'].upper().strip(),
                 request.form.get('medida',''),
                 request.form.get('contenido_paquete',''),
                 request.form.get('contenido_bulto') or 1,
                 float(request.form.get('costo') or 0),
                 float(request.form.get('precio_unitario_iva') or 0),
                 float(request.form.get('precio_margen') or 0),
                 int(request.form.get('stock') or 0)))
            db.commit()
            flash('Producto agregado correctamente', 'ok')
            return redirect(url_for('inventario'))
        except Exception as e:
            flash(f'Error: la referencia ya existe o hay datos inválidos', 'error')
    return render_template('editar_producto.html', producto=None)

@app.route('/inventario/editar/<int:pid>', methods=['GET','POST'])
@login_requerido
def editar_producto(pid):
    db = get_db()
    if request.method == 'POST':
        db.execute("""UPDATE productos SET nombre=?,medida=?,contenido_paquete=?,
            contenido_bulto=?,costo=?,precio_unitario_iva=?,precio_margen=?,stock=?
            WHERE id=?""",
            (request.form['nombre'], request.form['medida'], request.form['contenido_paquete'],
             request.form['contenido_bulto'], request.form['costo'],
             request.form['precio_unitario_iva'], request.form['precio_margen'],
             request.form['stock'], pid))
        db.commit()
        flash('Producto actualizado correctamente', 'ok')
        return redirect(url_for('inventario'))
    prod = db.execute("SELECT * FROM productos WHERE id=?", (pid,)).fetchone()
    return render_template('editar_producto.html', producto=prod)

# CLIENTES
@app.route('/clientes')
@login_requerido
def clientes():
    db = get_db()
    q = request.args.get('q','')
    if q:
        lista = db.execute("SELECT * FROM clientes WHERE empresa LIKE ? OR contacto LIKE ?",
                           (f'%{q}%', f'%{q}%')).fetchall()
    else:
        lista = db.execute("SELECT * FROM clientes ORDER BY empresa").fetchall()
    stats = {
        'total':   db.execute("SELECT COUNT(*) FROM clientes").fetchone()[0],
        'activos': db.execute("SELECT COUNT(*) FROM clientes WHERE activo=1").fetchone()[0],
    }
    return render_template('clientes.html', clientes=lista, stats=stats, q=q)

@app.route('/clientes/nuevo', methods=['GET','POST'])
@login_requerido
def nuevo_cliente():
    if request.method == 'POST':
        db = get_db()
        db.execute("""INSERT INTO clientes (empresa,contacto,telefono,email,rfc,credito)
            VALUES (?,?,?,?,?,?)""",
            (request.form['empresa'], request.form['contacto'], request.form['telefono'],
             request.form['email'], request.form['rfc'], request.form.get('credito',0)))
        db.commit()
        flash('Cliente creado correctamente', 'ok')
        return redirect(url_for('clientes'))
    return render_template('form_cliente.html', cliente=None)

@app.route('/clientes/editar/<int:cid>', methods=['GET','POST'])
@login_requerido
def editar_cliente(cid):
    db = get_db()
    if request.method == 'POST':
        db.execute("""UPDATE clientes SET empresa=?,contacto=?,telefono=?,email=?,rfc=?,credito=?,activo=?
            WHERE id=?""",
            (request.form['empresa'], request.form['contacto'], request.form['telefono'],
             request.form['email'], request.form['rfc'], request.form.get('credito',0),
             1 if request.form.get('activo') else 0, cid))
        db.commit()
        flash('Cliente actualizado correctamente', 'ok')
        return redirect(url_for('clientes'))
    cliente = db.execute("SELECT * FROM clientes WHERE id=?", (cid,)).fetchone()
    return render_template('form_cliente.html', cliente=cliente)

# COTIZACIONES
@app.route('/cotizaciones')
@login_requerido
def cotizaciones():
    db = get_db()
    lista = db.execute("""
        SELECT c.*, cl.empresa FROM cotizaciones c
        LEFT JOIN clientes cl ON c.cliente_id = cl.id
        ORDER BY c.id DESC
    """).fetchall()
    stats = {
        'total':     len(lista),
        'aprobadas': sum(1 for r in lista if r['estado']=='Aprobada'),
        'pendientes':sum(1 for r in lista if r['estado'] in ('Pendiente','Enviada','Borrador')),
        'monto':     sum(r['total'] for r in lista if r['estado'] != 'Cancelada'),
    }
    return render_template('cotizaciones.html', cotizaciones=lista, stats=stats)

@app.route('/cotizaciones/nueva', methods=['GET','POST'])
@login_requerido
def nueva_cotizacion():
    db = get_db()
    if request.method == 'POST':
        data = request.get_json()
        max_id = db.execute("SELECT COALESCE(MAX(id),0) FROM cotizaciones").fetchone()[0]
        folio = f"COT-{100 + max_id + 1}"
        db.execute("""INSERT INTO cotizaciones (folio,cliente_id,vigencia,total,estado,notas)
            VALUES (?,?,?,?,?,?)""",
            (folio, data['cliente_id'], data['vigencia'], data['total'],
             data.get('estado','Borrador'), data.get('notas','')))
        cot_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        for item in data['items']:
            db.execute("""INSERT INTO cotizacion_items
                (cotizacion_id,producto_id,cantidad,precio_unitario,subtotal)
                VALUES (?,?,?,?,?)""",
                (cot_id, item['producto_id'], item['cantidad'],
                 item['precio_unitario'], item['subtotal']))
        db.commit()
        return jsonify({'ok': True, 'folio': folio})
    clientes_list  = db.execute("SELECT id,empresa FROM clientes WHERE activo=1 ORDER BY empresa").fetchall()
    productos_list = [dict(r) for r in db.execute("SELECT * FROM productos ORDER BY ref").fetchall()]
    return render_template('form_cotizacion.html', clientes=clientes_list, productos=productos_list)

@app.route('/cotizaciones/<int:cid>')
@login_requerido
def ver_cotizacion(cid):
    db = get_db()
    cot   = db.execute("""SELECT c.*,cl.empresa,cl.contacto,cl.telefono,cl.rfc
        FROM cotizaciones c LEFT JOIN clientes cl ON c.cliente_id=cl.id
        WHERE c.id=?""",(cid,)).fetchone()
    items = db.execute("""SELECT ci.*,p.nombre,p.ref,p.medida
        FROM cotizacion_items ci JOIN productos p ON ci.producto_id=p.id
        WHERE ci.cotizacion_id=?""",(cid,)).fetchall()
    return render_template('ver_cotizacion.html', cot=cot, items=items)

@app.route('/cotizaciones/estado/<int:cid>', methods=['POST'])
@login_requerido
def cambiar_estado_cot(cid):
    db = get_db()
    estado = request.json.get('estado')
    db.execute("UPDATE cotizaciones SET estado=? WHERE id=?", (estado, cid))
    db.commit()
    return jsonify({'ok': True})

# PEDIDOS
@app.route('/pedidos')
@login_requerido
def pedidos():
    db = get_db()
    lista = db.execute("""
        SELECT p.*, cl.empresa FROM pedidos p
        LEFT JOIN clientes cl ON p.cliente_id = cl.id
        ORDER BY p.id DESC
    """).fetchall()
    stats = {
        'activos':    sum(1 for r in lista if r['estado'] in ('Pendiente','En camino')),
        'entregados': sum(1 for r in lista if r['estado']=='Entregado'),
        'total_mes':  sum(r['total'] for r in lista),
    }
    return render_template('pedidos.html', pedidos=lista, stats=stats)

@app.route('/pedidos/nuevo', methods=['GET','POST'])
@login_requerido
def nuevo_pedido():
    db = get_db()
    if request.method == 'POST':
        data = request.get_json()
        max_id = db.execute("SELECT COALESCE(MAX(id),0) FROM pedidos").fetchone()[0]
        folio = f"PED-{200 + max_id + 1}"
        db.execute("""INSERT INTO pedidos
            (folio,cliente_id,cotizacion_id,fecha_entrega,total,estado,notas)
            VALUES (?,?,?,?,?,?,?)""",
            (folio, data['cliente_id'], data.get('cotizacion_id') or None,
             data['fecha_entrega'], data['total'],
             data.get('estado','Pendiente'), data.get('notas','')))
        ped_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        for item in data['items']:
            db.execute("""INSERT INTO pedido_items
                (pedido_id,producto_id,cantidad,precio_unitario,subtotal)
                VALUES (?,?,?,?,?)""",
                (ped_id, item['producto_id'], item['cantidad'],
                 item['precio_unitario'], item['subtotal']))
            db.execute("UPDATE productos SET stock=MAX(0,stock-?) WHERE id=?",
                       (item['cantidad'], item['producto_id']))
        db.commit()
        return jsonify({'ok': True, 'folio': folio})
    clientes_list    = db.execute("SELECT id,empresa FROM clientes WHERE activo=1 ORDER BY empresa").fetchall()
    productos_list   = [dict(r) for r in db.execute("SELECT * FROM productos ORDER BY ref").fetchall()]
    cotizaciones_list= db.execute("""SELECT c.id,c.folio,cl.empresa FROM cotizaciones c
        JOIN clientes cl ON c.cliente_id=cl.id
        WHERE c.estado='Aprobada' ORDER BY c.id DESC""").fetchall()
    return render_template('form_pedido.html', clientes=clientes_list,
                           productos=productos_list, cotizaciones=cotizaciones_list)

@app.route('/pedidos/<int:pid>')
@login_requerido
def ver_pedido(pid):
    db = get_db()
    ped   = db.execute("""SELECT p.*,cl.empresa,cl.contacto,cl.telefono
        FROM pedidos p LEFT JOIN clientes cl ON p.cliente_id=cl.id
        WHERE p.id=?""",(pid,)).fetchone()
    items = db.execute("""SELECT pi.*,pr.nombre,pr.ref,pr.medida
        FROM pedido_items pi JOIN productos pr ON pi.producto_id=pr.id
        WHERE pi.pedido_id=?""",(pid,)).fetchall()
    return render_template('ver_pedido.html', ped=ped, items=items)

@app.route('/pedidos/estado/<int:pid>', methods=['POST'])
@login_requerido
def cambiar_estado_ped(pid):
    db = get_db()
    estado = request.json.get('estado')
    db.execute("UPDATE pedidos SET estado=? WHERE id=?", (estado, pid))
    db.commit()
    return jsonify({'ok': True})

# API
@app.route('/api/productos')
@login_requerido
def api_productos():
    db = get_db()
    prods = db.execute("SELECT * FROM productos ORDER BY ref").fetchall()
    return jsonify([dict(p) for p in prods])

# DASHBOARD
@app.route('/dashboard')
@login_requerido
def dashboard():
    db = get_db()
    total_pedidos   = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    pedidos_activos = db.execute("SELECT COUNT(*) FROM pedidos WHERE estado IN ('Pendiente','En camino')").fetchone()[0]
    ingresos_total  = db.execute("SELECT COALESCE(SUM(total),0) FROM pedidos WHERE estado != 'Cancelado'").fetchone()[0]
    total_clientes  = db.execute("SELECT COUNT(*) FROM clientes WHERE activo=1").fetchone()[0]
    cots_pendientes = db.execute("SELECT COUNT(*) FROM cotizaciones WHERE estado IN ('Borrador','Enviada','Pendiente')").fetchone()[0]
    stock_critico   = db.execute("SELECT COUNT(*) FROM productos WHERE stock < 50").fetchone()[0]
    estados_pedido  = db.execute("SELECT estado, COUNT(*) as total FROM pedidos GROUP BY estado").fetchall()
    estados_cot     = db.execute("SELECT estado, COUNT(*) as total FROM cotizaciones GROUP BY estado").fetchall()
    top_productos   = db.execute("""
        SELECT p.nombre, p.ref, SUM(pi.cantidad) as total_vendido
        FROM pedido_items pi JOIN productos p ON pi.producto_id=p.id
        GROUP BY pi.producto_id ORDER BY total_vendido DESC LIMIT 5
    """).fetchall()
    top_clientes    = db.execute("""
        SELECT c.empresa, COALESCE(SUM(pe.total),0) as monto
        FROM clientes c LEFT JOIN pedidos pe ON pe.cliente_id=c.id AND pe.estado!='Cancelado'
        GROUP BY c.id ORDER BY monto DESC LIMIT 5
    """).fetchall()
    stock_bajo_list = db.execute("SELECT ref,nombre,stock FROM productos WHERE stock<50 ORDER BY stock ASC LIMIT 8").fetchall()
    ultimos_pedidos = db.execute("""
        SELECT pe.folio,pe.estado,pe.total,pe.fecha,c.empresa
        FROM pedidos pe LEFT JOIN clientes c ON pe.cliente_id=c.id
        ORDER BY pe.id DESC LIMIT 5
    """).fetchall()
    ultimas_cots    = db.execute("""
        SELECT co.folio,co.estado,co.total,co.fecha,c.empresa
        FROM cotizaciones co LEFT JOIN clientes c ON co.cliente_id=c.id
        ORDER BY co.id DESC LIMIT 5
    """).fetchall()
    return render_template('dashboard.html',
        kpis=dict(total_pedidos=total_pedidos, pedidos_activos=pedidos_activos,
                  ingresos_total=ingresos_total, total_clientes=total_clientes,
                  cots_pendientes=cots_pendientes, stock_critico=stock_critico),
        estados_pedido=[dict(r) for r in estados_pedido],
        estados_cot=[dict(r) for r in estados_cot],
        top_productos=[dict(r) for r in top_productos],
        top_clientes=[dict(r) for r in top_clientes],
        stock_bajo_list=stock_bajo_list,
        ultimos_pedidos=ultimos_pedidos,
        ultimas_cots=ultimas_cots,
    )

# ── INIT ──────────────────────────────────────────────────────────────────────
init_db()

if __name__ == '__main__':
    print("\n✅  Leissam corriendo en http://127.0.0.1:5000")
    print("   Usuario: admin  |  Contraseña: leissam2026")
    print("   Usuario: demo   |  Contraseña: demo1234\n")
    app.run(debug=True)