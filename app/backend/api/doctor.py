from fastapi import APIRouter

from app.backend.services.doctor_service import run_doctor

router = APIRouter()


@router.get("/doctor")
def get_doctor() -> dict:
    checks = run_doctor()
    return {"checks": checks, "all_ok": all(c["ok"] for c in checks)}
