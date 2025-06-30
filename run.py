from app import create_app
from app.backup import monthly_reset

app = create_app()
monthly_reset(app)
if __name__ == "__main__":
    app.run(debug=True)
    
