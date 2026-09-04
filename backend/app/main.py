from io import BytesIO
from math import cos, radians
from random import Random

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

app = FastAPI(title="RoVibe Test Data Generator", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "https://frontend-vert-three-37.vercel.app",
        "https://ro-vibe-input-3kqd78p9n-ramkrishnas-projects-4048bf14.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOCATIONS = {
    "Lucknow": (26.8467, 80.9462),
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Noida": (28.5355, 77.3910),
}
AVAILABLE_COLUMNS = [
    "Outlet ID", "Outlet Name", "Latitude", "Longitude", "Distributor ID",
    "Distributor Name", "Beat ID", "Beat Name", "Employee ID", "Employee Name",
    "Address", "City", "State", "Revenue", "Visit Frequency",
]
EXPORT_COLUMN_NAMES = {
    column: column.lower().replace(" ", "_")
    for column in AVAILABLE_COLUMNS
}


class LocalFake:
    """Dependency-free provider for the synthetic names and addresses used here."""

    first_names = ("Aarav", "Aditi", "Arjun", "Isha", "Kabir", "Meera", "Rohan", "Zoya")
    last_names = ("Sharma", "Verma", "Gupta", "Singh", "Khan", "Patel", "Mishra", "Joshi")
    company_types = ("General Store", "Mart", "Traders", "Supermarket", "Retail", "Foods")

    def __init__(self, rng: Random) -> None:
        self.rng = rng

    def last_name(self) -> str:
        return self.rng.choice(self.last_names)

    def name(self) -> str:
        return f"{self.rng.choice(self.first_names)} {self.last_name()}"

    def company(self) -> str:
        return f"{self.last_name()} {self.rng.choice(self.company_types)}"

    def address(self) -> str:
        return f"{self.rng.randint(1, 999)}, {self.last_name()} Road, {self.rng.randint(100000, 999999)}"


class GenerationRequest(BaseModel):
    location: str = "Lucknow"
    radius_km: float = Field(default=30, gt=0, le=500)
    distributors: int = Field(default=5, gt=0, le=1000)
    beats_per_distributor: int = Field(default=5, gt=0, le=1000)
    employees_per_distributor: int = Field(default=3, gt=0, le=1000)
    outlets_per_distributor: int = Field(default=100, gt=0, le=1000000)
    min_distance_m: float = Field(default=100, ge=0, le=10000)
    columns: list[str] = AVAILABLE_COLUMNS
    seed: int | None = None


def generate_data(request: GenerationRequest) -> pd.DataFrame:
    if request.location not in LOCATIONS:
        raise HTTPException(400, "Choose a supported location.")
    unknown = set(request.columns) - set(AVAILABLE_COLUMNS)
    if unknown:
        raise HTTPException(400, f"Unsupported columns: {', '.join(sorted(unknown))}")

    total = request.distributors * request.outlets_per_distributor
    if total > 1_000_000:
        raise HTTPException(400, "The V1 limit is 1,000,000 generated rows.")

    rng = Random(request.seed)
    fake = LocalFake(rng)
    center_lat, center_lon = LOCATIONS[request.location]
    rows = []
    outlet_number = 1

    for d in range(1, request.distributors + 1):
        distributor_id = f"D{d:04d}"
        distributor_name = f"Distributor {fake.last_name()} {d}"
        beats = [
            (f"{distributor_id}-B{b:03d}", f"Beat {b:03d}")
            for b in range(1, request.beats_per_distributor + 1)
        ]
        employees = [
            (f"{distributor_id}-E{e:03d}", fake.name())
            for e in range(1, request.employees_per_distributor + 1)
        ]
        for local_index in range(request.outlets_per_distributor):
            beat_id, beat_name = beats[(local_index + rng.randrange(len(beats))) % len(beats)]
            employee_id, employee_name = employees[(local_index + rng.randrange(len(employees))) % len(employees)]
            angle = rng.random() * 6.283185307
            distance_km = request.radius_km * (rng.random() ** 0.5)
            latitude = center_lat + (distance_km / 111.0) * __import__("math").sin(angle)
            longitude = center_lon + (distance_km / (111.0 * cos(radians(center_lat)))) * __import__("math").cos(angle)
            rows.append({
                "Outlet ID": f"O{outlet_number:07d}",
                "Outlet Name": fake.company().replace(",", ""),
                "Latitude": round(latitude, 7),
                "Longitude": round(longitude, 7),
                "Distributor ID": distributor_id,
                "Distributor Name": distributor_name,
                "Beat ID": beat_id,
                "Beat Name": beat_name,
                "Employee ID": employee_id,
                "Employee Name": employee_name,
                "Address": fake.address().replace("\n", ", "),
                "City": request.location,
                "State": "Uttar Pradesh" if request.location in ("Lucknow", "Noida") else "Delhi" if request.location == "Delhi" else "Maharashtra",
                "Revenue": rng.randint(1, 100),
                "Visit Frequency": rng.choice(["1", "2"]),
            })
            outlet_number += 1
    return pd.DataFrame(rows, columns=request.columns)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/locations")
def locations() -> list[str]:
    return list(LOCATIONS)


@app.post("/api/template/analyze")
async def analyze_template(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(400, "Only .xlsx files are supported.")
    content = await file.read()
    try:
        frame = pd.read_excel(BytesIO(content), nrows=1000)
    except Exception as exc:
        raise HTTPException(400, "The uploaded workbook could not be read.") from exc
    return {"columns": [str(column) for column in frame.columns], "rows": len(frame)}


@app.post("/api/generation/preview")
def preview(request: GenerationRequest) -> dict:
    frame = generate_data(request)
    return {
        "statistics": {
            "distributors": request.distributors,
            "beats": request.distributors * request.beats_per_distributor,
            "employees": request.distributors * request.employees_per_distributor,
            "outlets": len(frame),
            "average_outlets_per_beat": round(len(frame) / (request.distributors * request.beats_per_distributor), 2),
            "average_outlets_per_employee": round(len(frame) / (request.distributors * request.employees_per_distributor), 2),
        },
        "records": frame.head(100).fillna("").to_dict(orient="records"),
    }


@app.post("/api/export/excel")
def export_excel(request: GenerationRequest) -> StreamingResponse:
    frame = generate_data(request).rename(columns=EXPORT_COLUMN_NAMES)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name="Generated Data")
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="Generated_Data.xlsx"'},
    )
