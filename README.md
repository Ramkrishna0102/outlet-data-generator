# FMCG Synthetic Outlet Data Generator

## Run locally

Start the API:

```powershell
cd "C:\Outlet Data Generator\backend"
C:\Python314\python.exe -m uvicorn app.main:app --reload
```

Start the frontend in a second terminal:

```powershell
cd "C:\Outlet Data Generator\frontend"
npm run dev
```

Open the URL printed by Vite, usually `http://localhost:5173`.

The API also exposes interactive documentation at `http://localhost:8000/docs`.
