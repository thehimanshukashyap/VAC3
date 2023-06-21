from fastapi import FastAPI

app =FastAPI()

@app.get("/hello")
def index():
    return {"messages": "Hello world"}

@app.get("/test")
def test():
    a = 20
    b = 10
    c = a+b
    return {"messages":"Test API","total":c}