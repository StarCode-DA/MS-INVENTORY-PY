from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models.inventarios import Inventory
from src.schemas.inventario import InventoryCreate, InventoryUpdate

router = APIRouter(prefix="/inventory", tags=["Inventory"])

# Dependecia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# GET — lista inventario por sede
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
# PUT — actualizar stock
@router.put("/{id}")
def update_stock(id: int, data: InventoryUpdate, db: Session = Depends(get_db)):
    item = db.query(Inventory).filter(Inventory.id == id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    item.stock = data.stock
    db.commit()
    db.refresh(item)
    return item

# PATCH — toggle activo
@router.patch("/{id}/toggle-activo")
def toggle_activo(id: int, db: Session = Depends(get_db)):
    item = db.query(Inventory).filter(Inventory.id == id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    item.activo = not item.activo
    db.commit()
    db.refresh(item)
    return {"id": item.id, "activo": item.activo}
