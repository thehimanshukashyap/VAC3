import math
import random
import numpy as np
import pandas as pd
from typing import Annotated, Optional
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from sqlmodel import SQLModel, Field, create_engine, Session, update
from sklearn.metrics.pairwise import cosine_similarity
from fastapi.templating import Jinja2Templates
import warnings

warnings.filterwarnings('ignore')

app = FastAPI()

# postgresql://<username>:<password>@localhost/VAC3
# create user username with encrypted password 'password'
DATABASE_URL = 'postgresql://postgres:admin@localhost/VAC3'    #appuser:appuser connection information, 'VAC3' is our database

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

class Users(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    city: str
    email: str

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/hello") # http://localhost:8000/hello GET
def index():
    return { "message": "Hello World" }

@app.get("/test") # http://localhost:8000/test GET
def test():
    a = 10
    b = 20
    c = a + b
    return { "message": "Test API", "total": c }

# @app.get("/users", status_code=200)
# def get_users(x_api_key: str = None, city: str = None):
#     with Session(engine) as session:
#         users = session.query(Users).all()
#         # print(f'users list {users}')
#         return { "message": "Users list", "data": users, "header": x_api_key }

@app.get("/users/{user_id}") # GET baseUrl/users/1
def get_user_by_id(user_id: int):
    with Session(engine) as session:
        user = session.query(Users).filter(Users.id == user_id).one_or_none()
        return { "message": "User detail", "data": user }

@app.post("/users", status_code=201)
def create_user(user: Users):
    with Session(engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return { "message": "New user", "data": user }

@app.put("/users/{user_id}")
def update_user(user_id: int, user: Users):
    with Session(engine) as session:
        user_exist = session.query(Users).filter(Users.id == user_id).one_or_none()
        if not user_exist:
            raise HTTPException(404, 'Invalid user id')
        
        user_exist.name = user.name
        user_exist.city = user.city
        user_exist.email = user.email
        session.add(user_exist)
        session.commit()
        session.refresh(user_exist)
        return { "message": "User updated successfully", "data": user_exist }

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    with Session(engine) as session:
        user_exist = session.query(Users).filter(Users.id == user_id).one_or_none()
        if not user_exist:
            raise HTTPException(404, 'Invalid user id')
        
        session.delete(user_exist)
        session.commit()
        return { "message": "User deleted successfully", "data": user_exist }
    

df_rating = pd.read_csv('C:/Users/DELL/Downloads/ML_FASTAPI/VAC3/VAC3/src/Netflix_Dataset_Rating.csv')
len(df_rating)
df_movie = pd.read_csv('C:/Users/DELL/Downloads/ML_FASTAPI/VAC3/VAC3/src/Netflix_Dataset_Movie.csv')
len(df_movie)

# Merging into one dataframe for building a Recommendation System
merged_df = pd.merge(df_rating, df_movie, on='Movie_ID')
merged_df.head()

merged_df.shape

# Creating a user-item utility matrix 
utility_matrix = merged_df.pivot_table(index='User_ID', columns='Movie_ID', values='Rating')

# Total number of unique users and 
# print(utility_matrix.shape)

utility_matrix

# Imputing the null entries by 0 for ease in calculations
utility_matrix_filled = utility_matrix.fillna(0)
utility_matrix_filled

# It returns pairwise cosine similarity scores 
def calculate_movie_similarity(matrix, movie_id):
    if movie_id not in matrix.columns:
        return f"Movie ID {movie_id} not found in the utility matrix."
    
    movie_column = matrix[movie_id]
    similarity_scores = cosine_similarity([movie_column.values], matrix.T.values)
    similarity_scores = similarity_scores[0]
    
    similarity_dict = {}
    for i, score in enumerate(similarity_scores):
        if i == movie_column.name or score == 0:
            continue
        similarity_dict[matrix.columns[i]] = round(score, 6)
    
    return similarity_dict

# For calculating weighted avg
def calculate_weighted_rating(matrix, user_id, movie_id, n):
    if movie_id not in matrix.columns:
        return f"Movie ID {movie_id} not found in the utility matrix."
    
    rating = matrix.loc[user_id, movie_id]
    
    if rating == 0:
        similarity_scores = calculate_movie_similarity(matrix, movie_id)
        top_movies = sorted(similarity_scores.items(), key=lambda x: x[1], reverse=True)[:n]
        
        p_values = [score for _, score in top_movies]
        a_values = [movie for movie, _ in top_movies]
        
        valid_movies = all(movie in matrix.columns for movie in a_values)
        if valid_movies:
            r = sum(p * matrix.loc[user_id, a] for p, a in zip(p_values, a_values)) / sum(p_values)
            
            matrix.loc[user_id, movie_id] = r
            return math.ceil(r)
        else:
            return "Unable to calculate weighted rating due to missing movie data."
    
    else:
        return rating


@app.put("/recommendation/{movie_id}/{user_id}")
def get_movie_rating(movie_id: int, user_id: int):
    # Check if the user_id and movie_id are valid
    if user_id not in utility_matrix_filled.index:
        return JSONResponse(content={"rating": None, "error": f"User ID {user_id} not found in the utility matrix."})

    if movie_id not in utility_matrix_filled.columns:
        return JSONResponse(content={"rating": None, "error": f"Movie ID {movie_id} not found in the utility matrix."})

    rating = utility_matrix_filled.loc[user_id, movie_id]

    if rating != 0:
        return JSONResponse(content={"rating": rating, "message": f"The rating of Movie_ID {movie_id} by User_ID {user_id} is {rating}."})

    print("This is after if condition:----------------------------------")
    weighted_rating = calculate_weighted_rating(utility_matrix_filled, user_id, movie_id, 4)
    return JSONResponse(content={"rating": weighted_rating, "message": f"The rating of Movie_ID {movie_id} by User_ID {user_id} would be {weighted_rating}."})
