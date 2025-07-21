from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import tempfile
from typing import Dict, List
from parsers import BookParser
from agent import AmbienceAgent

app = FastAPI(title="Sonomancer Ambient E-Reader API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for session management
books_storage: Dict[str, Dict] = {}
agent = AmbienceAgent()

@app.post("/upload")
async def upload_book(file: UploadFile = File(...)):
    """Accept EPUB/PDF file and return book_id"""
    if not file.filename.lower().endswith(('.epub', '.pdf')):
        raise HTTPException(status_code=400, detail="Only EPUB and PDF files are supported")
    
    book_id = str(uuid.uuid4())
    
    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        # Parse the book
        parser = BookParser()
        book_data = parser.parse_book(tmp_path, file.filename)
        
        books_storage[book_id] = {
            "filename": file.filename,
            "chapters": book_data["chapters"],
            "title": book_data.get("title", file.filename),
            "temp_path": tmp_path
        }
        
        return {"book_id": book_id, "title": book_data.get("title", file.filename)}
    
    except Exception as e:
        os.unlink(tmp_path)  # Clean up temp file
        raise HTTPException(status_code=500, detail=f"Error parsing book: {str(e)}")

@app.get("/chapters/{book_id}")
async def get_chapters(book_id: str):
    """List chapter indices + titles"""
    if book_id not in books_storage:
        raise HTTPException(status_code=404, detail="Book not found")
    
    book = books_storage[book_id]
    chapters = [
        {"index": i, "title": chapter["title"]} 
        for i, chapter in enumerate(book["chapters"])
    ]
    
    return {"chapters": chapters, "title": book["title"]}

@app.get("/chapter/{book_id}/{chapter_index}")
async def get_chapter(book_id: str, chapter_index: int):
    """Return plaintext for chapter"""
    if book_id not in books_storage:
        raise HTTPException(status_code=404, detail="Book not found")
    
    book = books_storage[book_id]
    if chapter_index < 0 or chapter_index >= len(book["chapters"]):
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    chapter = book["chapters"][chapter_index]
    return {
        "title": chapter["title"],
        "content": chapter["content"],
        "index": chapter_index
    }

@app.get("/ambience/{book_id}/{chapter_index}")
async def get_ambience(book_id: str, chapter_index: int):
    """Run AI agent and return mood + youtube_id"""
    if book_id not in books_storage:
        raise HTTPException(status_code=404, detail="Book not found")
    
    book = books_storage[book_id]
    if chapter_index < 0 or chapter_index >= len(book["chapters"]):
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    chapter = book["chapters"][chapter_index]
    
    try:
        result = await agent.analyze_chapter_ambience(chapter["content"])
        return result
    except Exception as e:
        import traceback
        print(f"Ambience error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error analyzing chapter: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)