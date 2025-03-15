# backend/services/google_books.py
import requests
import io
from PIL import Image

def download_and_compress_image(url, max_size=(300, 300), quality=75):
    """Scarica, ridimensiona e comprimi l'immagine"""
    try:
        print(f"Downloading image from: {url}")
        response = requests.get(url, timeout=10)  # Aggiungi un timeout
        if response.status_code != 200:
            print(f"Failed to download image: status code {response.status_code}")
            return None
        
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image'):
            print(f"Response is not an image: {content_type}")
            return None
            
        img = Image.open(io.BytesIO(response.content))
        
        # Converti in RGB se necessario
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Stampa dimensione originale
        print(f"Original image size: {img.size}")
        
        # Ridimensiona mantenendo proporzioni
        img.thumbnail(max_size)
        print(f"Resized to: {img.size}")
        
        # Comprimi l'immagine
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        result = buffer.getvalue()
        print(f"Compressed image size: {len(result)} bytes")
        
        return result
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def fetch_book_metadata(isbn):
    """Fetch book metadata from Google Books API using ISBN."""
    if not isbn:
        return None
    
    print(f"Fetching metadata for ISBN: {isbn}")
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"API error: status code {response.status_code}")
        return None
    
    data = response.json()
    if data.get("totalItems", 0) == 0:
        print(f"No books found for ISBN: {isbn}")
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
        print("Cover image links found in API response")
        img_url = volume_info["imageLinks"].get("thumbnail") or volume_info["imageLinks"].get("smallThumbnail")
        if img_url:
            print(f"Found image URL: {img_url}")
            img_url = img_url.replace("http://", "https://")
            cover_image = download_and_compress_image(img_url)
            print(f"Cover download result: {'Success' if cover_image else 'Failed'}")
            if cover_image:
                print(f"Cover size: {len(cover_image)} bytes")
    else:
        print("No image links found in API response")
    
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

