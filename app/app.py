import logging
from fastapi import Depends, FastAPI
from fastapi_utils.tasks import repeat_every

from app.models import UserDB
from app.users import auth_backend, current_active_user, fastapi_users
# from db import create_db_and_tables


logger = logging.getLogger(__name__)
app = FastAPI()
counter = 0

app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(fastapi_users.get_register_router(), prefix="/auth", tags=["auth"])
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(fastapi_users.get_users_router(), prefix="/users", tags=["users"])


@app.get("/authenticated-route")
async def authenticated_route(user: UserDB = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}


# Реализация выполнения периодического события
@app.on_event("startup")
@repeat_every(seconds=10, logger=logger, wait_first=True)
def periodic():
    global counter
    print('counter is', counter)
    counter += 1

# @app.on_event("startup")
# async def on_startup():
#    # Not needed if you setup a migration system like Alembic
#     await create_db_and_tables()