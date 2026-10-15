from fastapi import APIRouter

router = APIRouter()

# Registra GET /health no roteador deste arquivo.
@router.get("/health")
def verificar_saude() -> dict[str, str]:
    return {"status": "ok"}
