from fastapi import FastAPI, File, UploadFile, HTTPException
from gradio_client import Client, file
from fastapi.responses import StreamingResponse
from io import BytesIO
import os
import shutil
from huggingface_hub import login
from fastapi.middleware.cors import CORSMiddleware

# Configuracion del token de Hugging Face
HUGGINGFACE_TOKEN = ""
os.environ["HUGGINGFACE_TOKEN"] = HUGGINGFACE_TOKEN
login(HUGGINGFACE_TOKEN)

# Inicializar el cliente de Gradio
client = Client("yisol/IDM-VTON")

# Inicializar la aplicacion FastAPI
app = FastAPI()

#Configuracion CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # permite conexion desde esta direccion
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los metodos
    allow_headers=["*"],
)

@app.post("/model")
async def tryon_api(
    background: UploadFile = File(...), 
    garment: UploadFile = File(...)
):
    try:
    
        # Crear directorio temporal
        TEMP_DIR = "./temp"
        os.makedirs(TEMP_DIR, exist_ok=True)

        # Guardar las imagenes recibidas desde el front temporalmente
        background_path = os.path.join(TEMP_DIR, background.filename)
        garment_path = os.path.join(TEMP_DIR, garment.filename)

        with open(background_path, "wb") as f:
            shutil.copyfileobj(background.file, f)
        
        with open(garment_path, "wb") as f:
            shutil.copyfileobj(garment.file, f)

        # uso del space/modelo
        result = client.predict(
            dict={"background": file(background_path), "layers": [], "composite": None},
            garm_img=file(garment_path),
            garment_des="",  
            is_checked=True,
            is_checked_crop=False,
            denoise_steps=30,
            seed=42,
            api_name="/tryon"
        )
        
        # resultado tupla con las rutas de las imagenes
        generated_image_path, masked_image_path = result

   
        # Enviar imágenes como binarios
        def iterfile(file_path):
            with open(file_path, "rb") as file:
                yield from file


        
        return StreamingResponse(iterfile(generated_image_path), media_type="image/png")


    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando imagenes: {str(e)}")
    finally:
        # Limpiar archivos temporales
        os.remove(background_path)
        os.remove(garment_path)


# Endpoint de prueba
@app.get("/")
def root():
    return {"mensaje": "FastApi funcionando!"}

