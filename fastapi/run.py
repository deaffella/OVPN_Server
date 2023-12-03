import uvicorn as uvicorn
import os

if __name__ == '__main__':
    print("[FastAPI OVPN Control Pannel] is running...")
    uvicorn.run('src.entrypoints.app:app',
                host='127.0.0.1' if os.name=='nt' else '0.0.0.0',
                port=8000,
                reload=True,
                workers=4)
