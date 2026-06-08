from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
import os
import sys
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.api.inference import process_and_predict_edf

app = FastAPI(title="EEG Seizure Detection API")

# Permitir requests desde React (localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "API is running. Use /predict to upload an EDF file."}

@app.post("/predict")
async def predict_edf(file: UploadFile = File(...)):
    if not file.filename.endswith('.edf'):
        raise HTTPException(status_code=400, detail="Only .edf files are supported.")
        
    try:
        # Save uploaded file to a temporary location
        fd, temp_path = tempfile.mkstemp(suffix=".edf")
        with os.fdopen(fd, "wb") as f_out:
            shutil.copyfileobj(file.file, f_out)
            
        # Run inference pipeline
        results = process_and_predict_edf(temp_path)
        
        # Cleanup
        os.remove(temp_path)
        
        return JSONResponse(content=results)
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        print(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
