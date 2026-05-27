from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.database import SessionLocal
from src.models.inventarios import Inventory
from src.schemas.inventario import InventoryCreate, InventoryUpdate

router = APIRouter(prefix="/inventory", tags=["Inventory"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_inventory(sede_id: int, db: Session = Depends(get_db)):
    items = db.query(Inventory).filter(
        Inventory.sede_id == sede_id,
    ).order_by(Inventory.id).all()
    return items

# GET — detectar productos con stock bajo (algoritmo iterativo)
@router.get("/low-stock")
def get_low_stock(sede_id: int, threshold: float = 5, db: Session = Depends(get_db)):
    items = db.query(Inventory).filter(
        Inventory.sede_id == sede_id,
        Inventory.activo == True
    ).all()

    low_stock_items = []
    for item in items:           # Recorrido iterativo de todos los productos
        if item.stock <= threshold:
            low_stock_items.append(item)

    return {
        "sede_id": sede_id,
        "threshold": threshold,
        "total_reviewed": len(items),
        "low_stock_count": len(low_stock_items),
        "items": low_stock_items
    }
# POST — agregar producto al inventario de una sede
@router.post("/")
def create_inventory(data: InventoryCreate, db: Session = Depends(get_db)):
    existing = db.query(Inventory).filter(
        Inventory.product_id == data.product_id,
        Inventory.sede_id == data.sede_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product already exists in this location")
    item = Inventory(
        product_id=data.product_id,
        sede_id=data.sede_id,
        stock=data.stock
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.put("/{id}")
def update_stock(id: int, data: InventoryUpdate, db: Session = Depends(get_db)):
    item = db.query(Inventory).filter(Inventory.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    item.stock = data.stock
    db.commit()
    db.refresh(item)
    return item

@router.patch("/{id}/toggle-activo")
def toggle_activo(id: int, db: Session = Depends(get_db)):
    item = db.query(Inventory).filter(Inventory.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    item.activo = not item.activo
    db.commit()
    db.refresh(item)
    return {"id": item.id, "activo": item.activo}

# ============================================================
# Backtracking para detectar productos sin rotación
# ============================================================
def backtracking_sin_rotacion(productos, ventas_por_producto, semanas, umbral):
    resultado = []

    def tiene_consecutivos(ventas_semanas, umbral):
        consecutivos = 0
        max_consecutivos = 0
        ultima_venta = None
        for semana in sorted(ventas_semanas.keys()):
            if ventas_semanas[semana] == 0:
                consecutivos += 1
                max_consecutivos = max(max_consecutivos, consecutivos)
            else:
                consecutivos = 0
                ultima_venta = semana

        # Fix: solo reportar si la semana más reciente (0) también es sin ventas
        if ventas_semanas.get(0, 0) > 0:
            return False, 0, ultima_venta

        return max_consecutivos >= umbral, max_consecutivos, ultima_venta

    def explorar(idx):
        if idx >= len(productos):
            return
        producto = productos[idx]
        key = (producto["product_id"], producto["sede_id"])
        ventas_semanas = ventas_por_producto.get(key, {s: 0 for s in range(semanas)})

        # Poda: si tiene ventas en todas las semanas no lo exploramos
        semanas_con_venta = sum(1 for v in ventas_semanas.values() if v > 0)
        if semanas_con_venta == semanas:
            explorar(idx + 1)
            return

        # Poda adicional: si vendió esta semana no lo reportamos como sin rotación
        if ventas_semanas.get(0, 0) > 0:
            explorar(idx + 1)
            return

        cumple, max_consec, ultima_venta = tiene_consecutivos(ventas_semanas, umbral)
        if cumple:
            resultado.append({
                **producto,
                "semanas_sin_rotacion": max_consec,
                "ultima_venta": ultima_venta,
                "alerta": "🔴 Critical" if max_consec >= 4 else "🟠 Warning" if max_consec >= 3 else "🟡 Alert"
            })

        explorar(idx + 1)

    explorar(0)
    return resultado

@router.get("/no-rotation")
def get_no_rotation(sede_id: int, semanas: int = 4, umbral: int = 2, db: Session = Depends(get_db)):
    if sede_id == 0:
        rows_inv = db.execute(
            text("""
                SELECT i.id, i.product_id, i.sede_id, i.stock, i.activo,
                       p.nombre, p.categoria, p.unidad
                FROM inventory i
                JOIN products p ON p.id = i.product_id
                WHERE i.activo = true
            """)
        ).fetchall()
    else:
        rows_inv = db.execute(
            text("""
                SELECT i.id, i.product_id, i.sede_id, i.stock, i.activo,
                       p.nombre, p.categoria, p.unidad
                FROM inventory i
                JOIN products p ON p.id = i.product_id
                WHERE i.sede_id = :sede_id AND i.activo = true
            """),
            {"sede_id": sede_id}
        ).fetchall()

    if not rows_inv:
        return {"sin_rotacion": [], "reactivados": []}

    productos = [
        {
            "inv_id": r[0],
            "product_id": r[1],
            "sede_id": r[2],
            "stock": float(r[3]),
            "activo": r[4],
            "nombre": r[5],
            "categoria": r[6],
            "unidad": r[7]
        }
        for r in rows_inv
    ]

    # Ventas por producto+sede+semana usando fecha_cierre
    rows_ventas = db.execute(
        text("""
            SELECT
                oi.product_id,
                o.sede_id,
                FLOOR(EXTRACT(EPOCH FROM (NOW() - o.fecha_cierre)) / 604800)::int AS semanas_atras,
                SUM(oi.cantidad) AS total_vendido
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.fecha_cierre >= NOW() - INTERVAL '1 week' * :semanas
              AND o.status = 'CERRADO'
            GROUP BY oi.product_id, o.sede_id, semanas_atras
        """),
        {"semanas": semanas}
    ).fetchall()

    ventas_map = {}
    for r in rows_ventas:
        key = (r[0], r[1])
        semana = r[2]
        total = float(r[3])
        if key not in ventas_map:
            ventas_map[key] = {s: 0 for s in range(semanas)}
        ventas_map[key][semana] = total

    ventas_por_producto = {}
    for p in productos:
        key = (p["product_id"], p["sede_id"])
        if key not in ventas_map:
            ventas_map[key] = {s: 0 for s in range(semanas)}
        ventas_por_producto[key] = ventas_map[key]

    sin_rotacion = backtracking_sin_rotacion(productos, ventas_por_producto, semanas, umbral)

    # ============================================================
    # Productos reactivados: vendieron solo en los últimos 7 días
    # pero no en semanas anteriores
    # ============================================================
    rows_reactivados = db.execute(
        text("""
            SELECT
                oi.product_id,
                o.sede_id,
                p.nombre,
                p.categoria,
                p.unidad,
                SUM(oi.cantidad) AS cantidad_vendida,
                SUM(oi.cantidad * oi.precio_unitario) AS total_venta,
                SUM(oi.cantidad * (oi.precio_unitario - p.costo)) AS ganancia
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            JOIN products p ON p.id = oi.product_id
            WHERE o.fecha_cierre >= NOW() - INTERVAL '7 days'
              AND o.status = 'CERRADO'
              AND (:sede_id = 0 OR o.sede_id = :sede_id)
            GROUP BY oi.product_id, o.sede_id, p.nombre, p.categoria, p.unidad
        """),
        {"sede_id": sede_id}
    ).fetchall()

    reactivados = []
    for r in rows_reactivados:
        key = (r[0], r[1])
        ventas_semanas = ventas_por_producto.get(key, {s: 0 for s in range(semanas)})

        # Solo incluir si las semanas anteriores (1 en adelante) no tuvieron ventas
        semanas_anteriores_sin_venta = all(
            ventas_semanas.get(s, 0) == 0 for s in range(1, semanas)
        )

        if semanas_anteriores_sin_venta:
            reactivados.append({
                "product_id": r[0],
                "sede_id": r[1],
                "nombre": r[2],
                "categoria": r[3],
                "unidad": r[4],
                "cantidad_vendida": int(r[5]),
                "total_venta": float(r[6]),
                "ganancia": float(r[7])
            })

    return {
        "sin_rotacion": sorted(sin_rotacion, key=lambda x: x["semanas_sin_rotacion"], reverse=True),
        "reactivados": reactivados
    }
