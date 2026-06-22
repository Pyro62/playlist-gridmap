from fastapi import FastAPI

app = FastAPI()

# world hello
@app.get("/")
def read_root():
    return {"status": "FastAPI is running on Render!"}
