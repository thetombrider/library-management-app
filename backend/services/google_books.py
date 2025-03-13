# backend/services/google_books.py
import requests

def fetch_book_metadata(isbn):
    """Fetch book metadata from Google Books API using ISBN."""
    if not isbn:
        return None
    
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return None
    
    data = response.json()
    if data.get("totalItems", 0) == 0:
        return None
    
    # Extract the book information
    volume_info = data["items"][0]["volumeInfo"]
    
    # Prepare metadata dictionary
    metadata = {
        "title": volume_info.get("title", ""),
        "author": ", ".join(volume_info.get("authors", [])),
        "description": volume_info.get("description", ""),
        "isbn": isbn  # Keep the original ISBN
    }
    
    return metadata