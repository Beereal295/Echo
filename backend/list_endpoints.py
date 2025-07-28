import sys
sys.path.append(".")

from app.main import app

def list_endpoints():
    """List all available API endpoints"""
    print("Echo Journal API - Available Endpoints")
    print("=" * 50)
    
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"{methods:<10} {route.path}")
    
    print("\n" + "=" * 50)
    print("API Documentation:")
    print("- Swagger UI: http://localhost:8000/docs")
    print("- ReDoc: http://localhost:8000/redoc")
    print("- Health Check: http://localhost:8000/api/v1/health/")

if __name__ == "__main__":
    list_endpoints()