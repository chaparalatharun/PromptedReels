# start_server.py (in root)
import uvicorn

def main():
    uvicorn.run(
        "api.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()
