from pydantic import BaseModel

#Pydantic Models

class Transaction(BaseModel):
    name:str
    book_id:str
    total_no_books:int
    author:str