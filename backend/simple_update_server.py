from fastapi import FastAPI
from fastapi.responses import FileResponse
import json

app = FastAPI()

@app.get("/api/updates/check")
def check():
    return {
        "tag_name": "v1.1.0",
        "body": "Versão de teste\n\n- Correção de bugs\n- Melhorias",
        "assets": [{"browser_download_url": "http://localhost:8000/api/updates/download"}]
    }

@app.get("/api/updates/download")
def download():
    return FileResponse("update_test.zip", filename="update.zip")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)
    