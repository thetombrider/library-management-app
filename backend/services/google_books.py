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
    
    # Extract publish year from publishedDate if available
    publish_year = None
    published_date = volume_info.get("publishedDate", "")
    if published_date and len(published_date) >= 4:
        try:
            publish_year = int(published_date[:4])
        except ValueError:
            pass
    
    # Prepare metadata dictionary
    metadata = {
        "title": volume_info.get("title", ""),
        "author": ", ".join(volume_info.get("authors", [])),
        "description": volume_info.get("description", ""),
        "isbn": isbn,  # Keep the original ISBN
        "publisher": volume_info.get("publisher", ""),
        "publish_year": publish_year
    }
    
    return metadata