## О проекте

Реализация тестового примера FastApi_users SQLAlchemy на базе системы миграции alembic.  
Источник: https://fastapi-users.github.io/fastapi-users/configuration/full-example/

Цели:
- Освоить alembic
- Реализовать систему авторизации и пощупать на практике все функции из коробки, в рамках обучения FastApi
- Реализовать пример выполнения периодического события (потребуется в будущих проектах)
- Научится пользоваться PowerShell в части работы с curl


### Настройка и использование миграции (alembic)  

В первую очередь описываем классами таблицы и обязательно наследуемся в каждом классе от Base, чтобы заработала автомиграция.   

```python
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
Base: DeclarativeMeta = declarative_base()

class UserTable(Base, SQLAlchemyBaseUserTable):
    pass
```

Чтобы заработали асинхронные адаптеры (типа aiosqlite) необходимо инициализировать миграцию с помощью шаблона async.  
Если этого не сделать, то при обращении к базе сервис будет осыпать невнятными ошибками. 
Если вы работаете с базой синхронно, то можно инициализировать без "-t async"

```shell
 alembic init -t async migration
```
В проекте появится папка "migration" и файл "alembic.ini "

Сделаем базовые настройки

migration/env.py  
```python
from app.db import Base

target_metadata = Base.metadata
```

alembic.ini  
```ini
sqlalchemy.url = sqlite+aiosqlite:///./database/test.db
```

Далее сделаем первую ревизию

```shell
alembic revision --autogenerate -m 'initial'
```

В папке migration/versions появится файл миграции
Если внутри файла видим что создаются таблицы и поля, то все нормально, миграция подтягивается автоматически. 
В противном случае проверяйте настройки

Далее обновляемся или откатываемся когда нам это необходимо.
```shell
alembic upgrade(downgreade) head
```


### Создание БД и таблиц при запуске сервиса 

Эта функция изначальна отсутствовала в базовом примере. Автор ее любезно дописал.  

example (app.py):
``` shell
@app.on_event("startup")
async def on_startup():
    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()
```

В данном проекте я использую миграцию от alembic, поэтому функцию закомментировал


### Реализация выполнения периодического события
Ставим утилиты fastapi_utils и на базe Starlette запускам в том же потоке, что и веб-сервер периодические задачи. 
https://fastapi-utils.davidmontague.xyz/user-guide/repeated-tasks/

Решение подсмотрел вот тут:
https://github.com/tiangolo/fastapi/issues/520


example (app.py):
```python
from fastapi_utils.tasks import repeat_every

@app.on_event("startup")
@repeat_every(seconds=10, logger=logger, wait_first=True)
def periodic():
    global counter
    print('counter is', counter)
    counter += 1
```


### Система авторизации на базе FastApi_users

#### 1) **Регистрация**  /auth/registration

#### 2) **Авторизация**  /auth/

Вводим логи+пароль - получаем токен авторизации, далее пихаем его во все запросы. 

#### 3) **Получить свой профиль**  

На винде это работает вот так:
```shell
Invoke-WebRequest -Uri http://127.0.0.1:8080/users/me -Headers @{"accept"="application/json"; "Authorization" = "Bearer $TOKEN1"} 
```
С ответом 200 получаем:
```json
Content: {"id":"d164ebb0-61ab-43f6-a96a-e9737811cae8","email":"archy@ya.ru","is_active":true,"is_superuser":false,"is_verified":false}
```

#### 4) **Обновляем профиль**  

ПРИМЕЧАНИЕ: is_active и is_superuser могут обновлять только суперюзер  
```shell
Invoke-WebRequest -Uri http://127.0.0.1:8080/users/me -Headers @{"accept"="application/json"; "Authorization"="Bearer $TOKEN"} -Method PATCH -Body "{`"password`":`"54321`"}" -UseBasicParsing
```
С ответом 200 получаем:
```json
Content: {"id":"d164ebb0-61ab-43f6-a96a-e9737811cae8","email":"archy@ya.ru","is_active":true,"is_superuser":false,"is_verified":false}
```

#### 5) **[Только суперюзер] Получить информацию о пользователе.**  

Все оcтальные будут получать "422 Forbidden"
```shell
Invoke-WebRequest -Uri http://127.0.0.1:8080/users/d164ebb0-61ab-43f6-a96a-e9737811cae8 -Headers @{"accept"="application/json"; "Authorization"="Bearer $TOKEN"} -Method GET -UseBasicParsing
```

#### 6) **[Только суперюзер] Изменить данные любого пользователя, промотить и демотить (даже себя).**  

Если снять с себя сюперюзера, то обратно восстановить можно либо через базу либо от другого суперюзера. 
```shell
Invoke-WebRequest -Uri http://127.0.0.1:8080/users/a08dc5a8-f075-4b5c-932a-c6a5858a49e4 -Headers @{"accept"="application/json"; "Authorization"="Bearer $TOKEN"} -Method PATCH -Body "{`"is_superuser`":`"true`"}" -UseBasicParsing
```

#### 7) **[Только суперюзер] Удаление пользователя**  
```shell
Invoke-WebRequest -Method DELETE -Uri http://127.0.0.1:8080/users/a08dc5a8-f075-4b5c-932a-c6a5858a49e4 -Headers @{"accept"="application/json"; "Authorization"="Bearer $TOKEN"} -UseBasicParsing
```
204 в случае успешного удаления.  

#### 8) **Logout**  

Примечание: Токен после логаута остается активным до истечения своего срока. 
```shell
Invoke-WebRequest -Method POST -Uri http://127.0.0.1:8080/auth/jwt/logout -Headers @{"accept"="application/json"; "Authorization"="Bearer $TOKEN"} -UseBasicParsing
```

#### 9) **Верификация email пользователя**  

С начала делается запрос временного токена для конкретного email с помощью /auth/request-verify-token 
В любом случае вернется 202 код
```shell
Invoke-WebRequest -Method POST -Uri http://127.0.0.1:8080/auth/request-verify-token -Headers @{"accept"="application/json";"Content-Type"="application/json"} -Body "{`"email`":`"archy@ya.ru`"}" -UseBasicParsing
```

Полученный токен передаем в функцию /auth/verify
```shell
Invoke-WebRequest -Method POST -Uri http://127.0.0.1:8080/auth/verify -Headers @{"accept"="application/json"; "Content-Type"="application/json"} -Body "{`"token`":`"TEMP_TOKEN`"}" -UseBasicParsing
```

#### 10) **Восстановление пароля по почте**  

С начала генерится временный токен для email c помощью /forgot-password
В любом случае вернется 202 код
```shell
Invoke-WebRequest -Method POST -Uri http://127.0.0.1:8080/auth/forgot-password -Headers @{"accept"="application/json";"Content-Type"="application/json"} -Body "{`"email`":`"archy@ya.ru`"}" -UseBasicParsing
```
Полученный токен передаем в функцию /auth/reset-password
```shell
Invoke-WebRequest -Method POST -Uri http://127.0.0.1:8080/auth/reset-password -Headers @{"accept"="application/json";"Content-Type"="application/json"} -Body "{`"token`":`"TEMP_TOKEN`",`"password`":`"12345`"}" -UseBasicParsing
```
