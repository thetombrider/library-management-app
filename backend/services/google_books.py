# backend/services/google_books.py
import requests
import io
from PIL import Image
import time
import logging

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_and_compress_image(url, max_size=(300, 300), quality=75):
    """Scarica, ridimensiona e comprimi l'immagine"""
    try:
        logger.info(f"Downloading image from: {url}")
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Failed to download image: status code {response.status_code}")
            return None
        
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image'):
            logger.warning(f"Response is not an image: {content_type}")
            return None
            
        img = Image.open(io.BytesIO(response.content))
        
        # Converti in RGB se necessario
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Stampa dimensione originale
        logger.info(f"Original image size: {img.size}")
        
        # Ridimensiona mantenendo proporzioni
        img.thumbnail(max_size)
        logger.info(f"Resized to: {img.size}")
        
        # Comprimi l'immagine
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        result = buffer.getvalue()
        logger.info(f"Compressed image size: {len(result)} bytes")
        
        return result
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def fetch_book_metadata(isbn):
    """Fetch book metadata using multiple APIs with fallback mechanism."""
    if not isbn:
        return None
    
    logger.info(f"Fetching metadata for ISBN: {isbn}")
    
    # Prima prova con Google Books API
    google_metadata = fetch_from_google_books(isbn)
    if google_metadata and google_metadata.get('title') and google_metadata.get('author'):
        logger.info("Metadata successfully retrieved from Google Books API")
        return google_metadata
    else:
        logger.info("Google Books API returned incomplete data, trying Open Library API...")
    
    # Se Google Books fallisce, prova con Open Library API
    open_library_metadata = fetch_from_open_library(isbn)
    if open_library_metadata:
        logger.info("Metadata successfully retrieved from Open Library API")
        return open_library_metadata
    
    # Se entrambi falliscono, ritorna quanto ottenuto da Google o None
    return google_metadata

def fetch_from_google_books(isbn):
    """Fetch book metadata specifically from Google Books API."""
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"Google Books API error: status code {response.status_code}")
            return None
        
        data = response.json()
        if data.get("totalItems", 0) == 0:
            logger.warning(f"No books found in Google Books for ISBN: {isbn}")
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
            logger.info("Cover image links found in Google Books API response")
            img_url = volume_info["imageLinks"].get("thumbnail") or volume_info["imageLinks"].get("smallThumbnail")
            if img_url:
                logger.info(f"Found image URL from Google Books: {img_url}")
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
    except Exception as e:
        logger.error(f"Error fetching from Google Books API: {str(e)}")
        return None

def fetch_from_open_library(isbn):
    """Fetch book metadata from Open Library API."""
    # Attendi un attimo per non sovraccaricare le API
    time.sleep(1)
    
    # Prima ottieni i metadati generali
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    
    try:
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            logger.warning(f"Open Library API error: status code {response.status_code}")
            return None
        
        data = response.json()
        book_key = f"ISBN:{isbn}"
        
        if book_key not in data:
            logger.warning(f"No book found in Open Library for ISBN: {isbn}")
            return None
        
        book_data = data[book_key]
        
        # Estrai le informazioni necessarie
        title = book_data.get("title", "")
        
        # Estrai autori (potrebbe essere una lista di oggetti)
        authors = []
        if "authors" in book_data:
            for author in book_data["authors"]:
                authors.append(author.get("name", ""))
        author_string = ", ".join(authors) if authors else ""
        
        # Estrai editore
        publisher = ""
        if "publishers" in book_data and book_data["publishers"]:
            publisher = book_data["publishers"][0].get("name", "")
        
        # Estrai anno di pubblicazione
        publish_year = None
        if "publish_date" in book_data:
            pub_date = book_data["publish_date"]
            # Estrai l'anno dalla stringa della data
            import re
            year_match = re.search(r'\d{4}', pub_date)
            if year_match:
                publish_year = int(year_match.group())
        
        # Ottieni la copertina
        cover_image = None
        if "cover" in book_data:
            cover_urls = book_data["cover"]
            # Prova a ottenere la versione medium, altrimenti small o large
            img_url = cover_urls.get("medium") or cover_urls.get("small") or cover_urls.get("large")
            if img_url:
                logger.info(f"Found image URL from Open Library: {img_url}")
                cover_image = download_and_compress_image(img_url)
        
        # Ottieni descrizione (richiede una seconda chiamata API)
        description = ""
        if "identifiers" in book_data and "openlibrary" in book_data["identifiers"]:
            ol_id = book_data["identifiers"]["openlibrary"][0]
            # Richiedi i dettagli del libro per ottenere la descrizione
            details_url = f"https://openlibrary.org/books/{ol_id}.json"
            try:
                details_response = requests.get(details_url, timeout=10)
                if details_response.status_code == 200:
                    details_data = details_response.json()
                    if "description" in details_data:
                        if isinstance(details_data["description"], dict):
                            description = details_data["description"].get("value", "")
                        else:
                            description = details_data["description"]
            except Exception as e:
                logger.error(f"Error fetching book details from Open Library: {str(e)}")
        
        # Prepara dizionario metadati nello stesso formato di Google Books
        metadata = {
            "title": title,
            "author": author_string,
            "description": description,
            "isbn": isbn,
            "publisher": publisher,
            "publish_year": publish_year,
            "cover_image": cover_image
        }
        
        return metadata
    except Exception as e:
        logger.error(f"Error fetching from Open Library API: {str(e)}")
        return None

