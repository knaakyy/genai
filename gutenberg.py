"""Project Gutenberg 원서 데이터 수집 및 전처리 모듈"""
import requests
import re
from bs4 import BeautifulSoup

GUTENBERG_SEARCH_URL = "https://gutendex.com/books/"

POPULAR_BOOKS = {
    "Pride and Prejudice (Jane Austen)": 1342,
    "Alice's Adventures in Wonderland (Lewis Carroll)": 11,
    "The Adventures of Tom Sawyer (Mark Twain)": 74,
    "Great Expectations (Charles Dickens)": 1400,
    "The Picture of Dorian Gray (Oscar Wilde)": 174,
    "Emma (Jane Austen)": 158,
    "Sense and Sensibility (Jane Austen)": 161,
    "The Scarlet Letter (Nathaniel Hawthorne)": 25344,
    "Frankenstein (Mary Shelley)": 84,
    "Dracula (Bram Stoker)": 345,
}

def search_books(query: str, limit: int = 10) -> list[dict]:
    """책 제목/저자로 Gutenberg 검색"""
    try:
        resp = requests.get(GUTENBERG_SEARCH_URL, params={"search": query, "languages": "en"}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for book in data.get("results", [])[:limit]:
            authors = ", ".join(a["name"] for a in book.get("authors", []))
            results.append({
                "id": book["id"],
                "title": book["title"],
                "authors": authors,
            })
        return results
    except Exception as e:
        return []

def fetch_book_text(book_id: int) -> str:
    """Gutenberg에서 텍스트 다운로드"""
    urls = [
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
        f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
    ]
    for url in urls:
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                text = resp.text
                # Gutenberg 헤더/푸터 제거
                start = re.search(r"\*\*\* START OF (THIS|THE) PROJECT GUTENBERG", text)
                end   = re.search(r"\*\*\* END OF (THIS|THE) PROJECT GUTENBERG", text)
                if start:
                    text = text[start.end():]
                if end:
                    text = text[:end.start()]
                return text.strip()
        except Exception:
            continue
    return ""

def preprocess_text(text: str, max_chars: int = 30000) -> str:
    """불필요한 공백·특수문자 정리 후 길이 제한"""
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text[:max_chars]

def extract_chapters(text: str) -> dict[str, str]:
    """챕터별 분리 (Chapter I, CHAPTER 1 등 패턴)"""
    pattern = re.compile(r"(CHAPTER\s+[IVXLC\d]+[^\n]*)", re.IGNORECASE)
    splits = pattern.split(text)
    chapters = {}
    if len(splits) <= 1:
        chapters["Full Text"] = text
        return chapters
    # splits: [pre, title1, body1, title2, body2, ...]
    for i in range(1, len(splits), 2):
        title = splits[i].strip()
        body  = splits[i+1].strip() if i+1 < len(splits) else ""
        chapters[title] = body
    return chapters
