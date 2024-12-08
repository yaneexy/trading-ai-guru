import os
import sys

# Add the src directory to the Python path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.append(src_dir)

# Import and run the server
from server import app
import uvicorn

if __name__ == "__main__":
    print(f"Starting server at http://localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
