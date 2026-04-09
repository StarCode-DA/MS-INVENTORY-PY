from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers.inventarios import router as inventarios_router

# Configuración y base de datos
app = FastAPI(title="MS INVENTORY", redirect_slashes=False)
# Orígenes permitidos
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]
# Middleware de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # dominios que pueden hacer requests
    allow_credentials=True,     # cookies y credenciales
    allow_methods=["*"],        # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],        # headers permitidos
)
# Routers
app.include_router(inventarios_router)