# Imagen base con Python 3.11
FROM python:3.11

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia todo el código del proyecto al contenedor
COPY . .

# Instala las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Comando para ejecutar la aplicación en el puerto 8004
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004"]