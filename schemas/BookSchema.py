def book_serializer(book) -> dict:
 return {
    'id':str(book["_id"]),
    'title':book["title"],
    'author':book["author"],
    'description':book["description"],
    'price':book["price"],
    'stock':book["stock"],}

def books_serializer(books) -> list: return [book_serializer(book) for book in books]