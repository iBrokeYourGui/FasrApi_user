import asyncio
import datetime
import logging
from time import sleep
from fastapi import Depends, FastAPI, BackgroundTasks
from fastapi_utils.tasks import repeat_every

from app.models import UserDB
from app.users import auth_backend, current_active_user, fastapi_users
# from db import create_db_and_tables


logging.basicConfig(level=logging.INFO)
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


# Реализация выполнения фонового события
async def some_task_function(params: str):
    """ функция, которую мы хотим запускать в фоне при переходе по заданному маршруту"""
    # sleep(5)
    logger.info("bg_task создан: ")
    await asyncio.sleep(10)
    logger.info(f"bg_task закончил работу: {params}")


@app.get("/get_tasks")
async def get_events():
    main_loop = asyncio.get_running_loop()
    active_tasks = [task.get_name() for task in asyncio.all_tasks(main_loop)]
    return active_tasks


@app.get("/stop_event_by_exceprion")
async def stop_event():
    main_loop = asyncio.get_running_loop()
    current_tasks = asyncio.all_tasks(main_loop)
    for task in current_tasks:
        if task.get_name() == 'bg_task':
            task.set_exception(Exception())
            return f'Task {task.get_name()} stopped by user'
    return 'Task "bg_task" not active'


@app.get("/cancel_bg_task")
async def cancel_event():
    main_loop = asyncio.get_running_loop()
    current_tasks = asyncio.all_tasks(main_loop)
    for task in current_tasks:
        if task.get_name() == 'bg_task':
            task.cancel()
            return f'Task {task.get_name()} cancelled by user'
    return 'Task "bg_task" not active'


@app.get("/background")
# async def bg_task(task: BackgroundTasks, user: UserDB = Depends(current_active_user)):
# async def bg_task(task: BackgroundTasks):
async def bg_task():
    """
    Маршрут для выполнения фоновой функции
    :param task: Параметры передаваемые в фоновую функцию
    :param user: Пользователь который запустил событие
    :return: dict
    """
    loop = asyncio.get_running_loop()
    task = asyncio.create_task(some_task_function("taram-params"), name='bg_task')

    # task.add_task(some_task_function, "taram-params")
    return {"task_result": "success", "user": "C===3"}
    # return {"task_result": "success", "user": user.email}


# Реализация выполнения периодического события
@app.on_event("startup")
@repeat_every(seconds=10, logger=logger, wait_first=False, raise_exceptions=True)
def periodic():
    global counter
    logger.info("Booted up")
    print(f'counter is {counter}: {datetime.datetime.now()}')
    counter += 1
    logger.info("Booted down")


@app.on_event("startup")
@repeat_every(seconds=20, logger=logger, wait_first=True, raise_exceptions=True)
async def periodic_task_function(stop: bool = False):
    """ функция, которую мы хотим запускать в фоне при переходе по заданному маршруту"""
    asyncio.create_task(some_task_function("taram-params"), name='bg_task')


# @app.on_event("startup")
# async def on_startup():
#    # Not needed if you setup a migration system like Alembic
#     await create_db_and_tables()