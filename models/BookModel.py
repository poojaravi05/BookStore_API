from pydantic import BaseModel

#Pydantic Models

class Book(BaseModel):
    title:str
    author: str
    description: str
    price: float
    stock: int