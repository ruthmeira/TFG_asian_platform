from app import app, db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE user ADD COLUMN region VARCHAR(10) DEFAULT NULL"))
        db.session.commit()
        print("✅ Columna 'region' añadida correctamente.")
    except Exception as e:
        if 'Duplicate column name' in str(e):
            print("ℹ️ La columna 'region' ya existía.")
        else:
            print(f"❌ Error al añadir columna: {e}")
