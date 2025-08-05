"""Code Review Controller"""

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from middlewares import auth_middleware
from services.code_review_service import generate_code_review

router = APIRouter()


@router.post("/api/overview", dependencies=[Depends(auth_middleware.verify_internal_auth_token)])
async def generate_repository_overview():
    """Generate repository overview and save to BLAMEGPT.md"""

    await generate_code_review()

    return {
        "message": "Repository overview generated successfully",
        "file": "BLAMEGPT.md",
    }


@router.get("/api/overview", dependencies=[Depends(auth_middleware.verify_internal_auth_token)])
async def get_repository_overview():
    """Get the generated repository overview"""

    try:
        with open("BLAMEGPT.md") as f:
            content = f.read()

        return Response(content=content, media_type="text/markdown")

    except FileNotFoundError:
        return {"error": "Repository overview not generated yet. Call /generate-overview first."}
