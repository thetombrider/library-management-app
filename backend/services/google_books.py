# backend/services/google_books.py
import requests
import io
from PIL import Image

def download_and_compress_image(url, max_size=(300, 300), quality=75):
    """Scarica, ridimensiona e comprimi l'immagine"""
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return None
        
        img = Image.open(io.BytesIO(response.content))
        
        # Converti in RGB se necessario
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Ridimensiona mantenendo proporzioni
        img.thumbnail(max_size)
        
        # Comprimi l'immagine
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        
        return buffer.getvalue()
    except Exception as e:
        print(f"Errore nell'elaborazione dell'immagine: {e}")
        return None

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
    
    # Ottieni la copertina e comprimila
    cover_image = None
    if "imageLinks" in volume_info:
        img_url = volume_info["imageLinks"].get("thumbnail") or volume_info["imageLinks"].get("smallThumbnail")
        if img_url:
            img_url = img_url.replace("http://", "https://")
            cover_image = download_and_compress_image(img_url)
    
    # Prepare metadata dictionary
    metadata = {
        "title": volume_info.get("title", ""),
        "author": ", ".join(volume_info.get("authors", [])),
        "description": volume_info.get("description", ""),
        "isbn": isbn,
        "publisher": volume_info.get("publisher", ""),
        "publish_year": publish_year,
        "cover_image": cover_image
    }
    
    return metadata

