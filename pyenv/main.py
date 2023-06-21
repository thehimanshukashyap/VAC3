from fastapi import FastAPI

app = FastAPI()  # creating the instance

@app.get("/")    # decorator, ("/") isten for an HTTP req jo base URL ke Liye aa rhi hi # http://localhost:8000/hello GET
def index():
    return {"message": "Hello World"}

@app.get("/test")    # http://localhost:8000/test GET
def test():
    a = 10
    b = 20
    c = a + b
    return {"message": "Test API", "Total": c}
