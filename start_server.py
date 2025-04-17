# start_server.py

import uvicorn

def main():
    uvicorn.run(
        "api:app",              # Module:App reference
        host="0.0.0.0",         # Bind to all interfaces
        port=8000,              # Change if needed
        reload=True,            # Auto-reload on file changes (dev only)
    )

if __name__ == "__main__":
    main()
