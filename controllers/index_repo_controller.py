from fastapi import APIRouter, Request

index_repo_router = APIRouter()


@index_repo_router.post("/index-repo")
async def index_repo(request: Request):
    db = request.app.state.db
    # index_repo_service.process_file()
