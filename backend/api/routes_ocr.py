"""
OCR and Prescription Analysis API.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import base64
import json
import logging
import httpx
from backend.core.schema import ContentItemResponse
from backend.core.settings import settings
from backend.core.db import execute_query
from backend.llm.chaining import PromptChain

logger = logging.getLogger(__name__)

router = APIRouter()


async def extract_text_sarvam(image_bytes: bytes) -> str | None:
    """Extract text from image using Sarvam AI Vision API if key exists."""
    if not settings.sarvam_api_key:
        return None
        
    try:
        url = "https://api.sarvam.ai/vision" # Placeholder URL if the actual endpoint varies, check docs.
        headers = {
            "api-subscription-key": settings.sarvam_api_key,
            "Content-Type": "application/json"
        }
        
        # Typically Sarvam/Vision APIs expect base64 or multipart
        b64_img = base64.b64encode(image_bytes).decode('utf-8')
        
        payload = {
            "image": b64_img,
            "task": "ocr"
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers, timeout=30.0)
            if resp.status_code == 200:
                 data = resp.json()
                 return data.get("text", "") # Adjust parsing based on exact response schema
            else:
                 logger.error(f"Sarvam API error: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"Failed calling Sarvam API: {e}")
        
    return None


async def extract_text_gemini(image_bytes: bytes) -> str | None:
    """Extract text from image using Gemini 1.5 Flash Vision."""
    if not settings.gemini_api_key:
         return None
         
    import google.generativeai as genai
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Gemini requires specific data structure for inline data
    b64_img = base64.b64encode(image_bytes).decode('utf-8')
    prompt = "Extract all text from this image exactly as written. If it looks like a medical prescription, make sure to clearly write out the medications and any diagnosed conditions."
    
    try:
        response = model.generate_content([
            prompt,
             {
                "mime_type": "image/jpeg", # Defaulting, will work for most
                "data": b64_img
             }
        ])
        return response.text
    except Exception as e:
        logger.error(f"Gemini Vision error: {e}")
        return None

def find_content_for_entities(entities: dict) -> list[dict]:
    """Search for relevant content based on extracted entities."""
    # Build search terms
    terms = []
    
    # Prioritize conditions/diagnoses for searching videos
    diagnoses = entities.get("diagnoses", [])
    if diagnoses:
         terms.extend(diagnoses)
         
    medications = entities.get("medications", [])
    if medications:
         terms.extend(medications)
         
    if not terms:
        return []

    # Take top 3 strong terms
    search_terms = terms[:3]
    
    where_clauses = []
    params = []
    
    for term in search_terms:
         # Rough search broadly across titles and tags
         where_clauses.append("(title LIKE ? OR tags_json LIKE ?)")
         params.extend([f"%{term}%", f"%{term}%"])
         
    query_sql = f"""
        SELECT id, type, title, url, source_name, source_tier,
               published_at, tags_json, summary_json, content_length
        FROM content_items 
        WHERE {" OR ".join(where_clauses)}
        ORDER BY (type='video') DESC, id DESC
        LIMIT 5
    """
    
    rows = execute_query(query_sql, tuple(params))
    
    items = []
    for row in rows:
        import json as _json
        try:
             tags = _json.loads(row.get("tags_json", "[]"))
        except:
             tags = []
        try:
             summary = _json.loads(row.get("summary_json", "{}"))
        except:
             summary = {}
             
        items.append({
            "id": row["id"],
            "type": row["type"],
            "title": row["title"],
            "url": row["url"],
            "source_name": row["source_name"],
            "source_tier": row["source_tier"],
            "published_at": row.get("published_at"),
            "tags": tags,
            "summary": summary,
            "content_length": row.get("content_length", 0),
        })
        
    return items


@router.post("")
async def analyze_prescription(file: UploadFile = File(...)):
    """
    1. Extracts text from prescription image (Sarvam API -> Gemini Fallback).
    2. Chains to an LLM extraction prompt to structure medications & diagnoses.
    3. Triggers search based on structured entities.
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
        
    image_bytes = await file.read()
    
    # 1. OCR Step
    ocr_text = await extract_text_sarvam(image_bytes)
    
    ocr_method = "Sarvam AI"
    if not ocr_text:
        ocr_text = await extract_text_gemini(image_bytes)
        ocr_method = "Gemini Flash Vision"
        
    if not ocr_text:
        return {
             "error": "Failed to extract text using OCR providers. Please check API keys or try again later.",
             "extracted": {},
             "recommendations": []
        }
        
    # 2. Extract Entities using Prompt Chaining
    extraction_prompt = """
    Below is raw text extracted from a medical document or prescription via OCR.
    Extract the diagnosed conditions, symptoms, and prescribed medications.
    
    Return a STRICT JSON object in this format:
    {{
        "diagnoses": ["list of conditions or symptoms found", "or empty"],
        "medications": ["list of medications or drug names found", "or empty"]
    }}
    
    Raw OCR Text:
    {prev_output}
    """
    
    chain = PromptChain()
    chain.add_step(
         name="entity_extraction",
         prompt_template=extraction_prompt,
         expected_json=True
    )
    
    results = chain.run({"prev_output": ocr_text})
    entities = results.get("entity_extraction", {})
    
    if not entities or (not entities.get("diagnoses") and not entities.get("medications")):
         # Fallback empty structure
         entities = {"diagnoses": [], "medications": []}
         
    # 3. Search for content
    recommendations = find_content_for_entities(entities)
    
    return {
        "ocr_method": ocr_method,
        "extracted_text_preview": ocr_text[:200] + "..." if len(ocr_text) > 200 else ocr_text,
        "extracted_entities": entities,
        "recommendations": recommendations,
    }
