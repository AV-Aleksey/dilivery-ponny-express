# dilivery-ponny-express

uvicorn app.main:app --reload

python -m venv .venv
source .venv/bin/activate
pip install uv
uv init
uv add fastapi uvicorn httpx
