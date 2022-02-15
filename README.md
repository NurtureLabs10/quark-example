## Local Server

```bash
virtualenv env
source env/script/activate
pip install -r requirements.txt
set -o allexport; source ./env.env; set +o allexport
cd app
python -m uvicorn app.asgi:app --debug
```

```bash
virtualenv env
source env/scripts/activate
set -o allexport; source ./env.env; set +o allexport
cd app
uvicorn app.asgi:app --debug
python manage.py shell_plus --notebook
```

```bash
docker-compose -f local.yml up --build
```
