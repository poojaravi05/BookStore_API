from fastapi import FastAPI ,Response,status
from pydantic import BaseModel
from models.BookModel import Book
from schemas.BookSchema import book_serializer, books_serializer
from bson import ObjectId
from bson.errors import InvalidId
from os import getenv   
from typing import List,Optional
import pymongo
from pymongo import MongoClient

app = FastAPI()

db_connection = MongoClient("mongodb://localhost:27017")
db = db_connection.bookstore
collection = db["bookstore_api"]
transaction_collection=db["transaction_log"]

#GET /books: Retrieves a list of all books in the store
@app.get("/books", tags=["Get All Books"])
async def find_all_books():
    books = books_serializer(collection.find())
    return {"status": "Ok","data": books}

#GET /books/{book_id}: Retrieves a specific book by ID
@app.get("/books/{book_id}")
async def get_book_by_id(book_id: str, response: Response):
    try:
        book_id = ObjectId(book_id)
    except InvalidId:
        response.status_code = status.HTTP_406_NOT_ACCEPTABLE
        return {"message": "Invalid Book ID"} 
    _book = books_serializer(collection.find({"_id": ObjectId(book_id)})) 
    return {"status": "Ok","data": _book}

#POST /books: Adds a new book to the store
@app.post("/books")
async def add_book(book: Book):
   _id = collection.insert_one(dict(book))
   book = books_serializer(collection.find({"_id": _id.inserted_id}))
   return {"status": "Ok","data": book}

#PUT /books/{book_id}: Updates an existing book by ID
@app.put("/books/{book_id}")
async def update_book_details(book_id: str, book: Book,response:Response):
    try:
        book_id = ObjectId(book_id)
    except InvalidId:
        response.status_code = status.HTTP_406_NOT_ACCEPTABLE
        return {"message": "Invalid Book ID"} 
    collection.find_one_and_update({"_id": ObjectId(book_id)}, {"$set": dict(book)})
    book = books_serializer(collection.find({"_id": ObjectId(book_id)}))
    return {"status": "Ok","data": book}

#DELETE /books/{book_id}: Deletes a book from the store by ID
@app.delete("/books/{book_id}")
async def delete_book(book_id: str,book:Book,response:Response):
    try:
        book_id = ObjectId(book_id)
    except InvalidId:
        response.status_code = status.HTTP_406_NOT_ACCEPTABLE
    collection.find_one_and_delete({"_id": ObjectId(book_id)})
    books = books_serializer(collection.find())
    return {"status": "Ok","data": []} 

#GET /search?title={}&author={}&min_price={}&max_price={}: Searches for books by title, author, and price range
@app.get("/search", tags=["Find Books"])
async def search_book(title: str = None, author: str = None, min_price: float = None, max_price: float = None):
    # query to search in the database
    booksFound = {}
    if title:
        booksFound["title"] = title
    if author:
        booksFound["author"] = author
    if min_price or max_price:
        booksFound["price"] = {}
    if min_price:
        booksFound["price"]["$gte"] = min_price
    if max_price:
        booksFound["price"]["$lte"] = max_price

    # filtration  of resulting bookx
    bookResult = []
    for book in collection.find(booksFound):
        bookResult.append(
            {
                "id": str(book["_id"]),
                "book": Book(
                    title=book["title"],
                    author=book["author"],
                    description=book["description"],
                    price=book["price"],
                    stock=book["stock"],
                ),
            }
        )

    return bookResult

#The total number of books in the store
@app.get("/totalbooks")
async def total_number_of_books():
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_stock": {"$sum": "$stock"}
            }
        }
    ]
    result = []
    for doc in collection.aggregate(pipeline):
        result.append({"total_stock": doc["total_stock"]})
    return {"total_stock": result[0]["total_stock"]}

#The top 5 bestselling books
@app.get("/topsellingbooks")
async def best_seller_books():
        pipeline=[]
        pipeline = [
        {
            "$group": {
                "_id": "$book_id",
                "name": { "$first": "$name" }, 
                "total_sold": {"$sum": "$total_no_books"}
                
            }
        },
        {
            "$sort": {"total_sold": -1}
        },
        {
            "$limit": 5
        },
        {
        "$project": {
            "_id": 0,
            "book_id": "$_id",
            "name": 1,
            "total_sold": 1
        }
    }
        
    ]

        cursor = transaction_collection.aggregate(pipeline)
        results = []
        for document in cursor:
            results.append(document)
        return results

#The top 5 authors with the most books in the store
@app.get("/topsellingauthors")
async def best_selling_authors():
        pipeline=[]
        pipeline = [
        {
            "$group": {
                "_id": "$author",
                "name": { "$first": "$name" }, 
                "total_sold": {"$sum": "$total_no_books"}
                
            }
        },
        {
            "$sort": {"total_sold": -1}
        },
        {
            "$limit": 5
        },
        {
        "$project": {
            "_id": 0,
            "author": "$_id",
            "name": 1,
            "total_sold": 1
        }
    }
        
    ]

        authors = transaction_collection.aggregate(pipeline)
        results = []
        for author in authors:
            results.append(author)
        return results

#addition of indexes for the MongoDB collection to optimize query performance.
@app.post("/add-mongo-index")
async def add_mongo_index():
    #adding index in bookstore_api collection
    collection.create_index("title")
    collection.create_index("author")
    collection.create_index("price")
    collection.create_index("stock")

    #adding index in transaction_log collection
    transaction_collection.create_index("book_id")

    return {"index":"addition successful"}


