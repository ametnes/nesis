alembic -x "url=$NESIS_API_DATABASE_URL" --config nesis/api/alembic.ini upgrade head
python nesis/api/core/main.py
