"""
Chat API route — RAG-based educational chatbot.
"""

from fastapi import APIRouter
from backend.core.schema import ChatRequest, ChatResponse
from backend.core.db import execute_query
from backend.core.safety import is_advice_seeking, get_refusal_message, DISCLAIMER
from backend.llm.llm_manager import get_llm

router = APIRouter()

SYSTEM_PROMPT = """You are a helpful and extremely knowledgeable primary health educator.
Your task is to answer user questions using the provided context from VERIFIED medical sources. 
When answering:
1. Try to be very natural and helpful.
2. If the user's question cannot be answered by the context, state that you don't have enough verified information to answer safely, but try to answer what you can.
3. NEVER provide definitive medical diagnosis, treatment recommendations, or advice.
4. Keep answers concise but comprehensive.

Here is the context retrieved from verified sources:
{context}
"""

@router.post("", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    """
    RAG-based chat endpoint.
    1. Grabs the last user message.
    2. Uses SQLite text-matching to find relevant content items.
    3. Injects them into the system prompt.
    4. Streams/Generates completion using LLMManager.
    """
    messages = req.messages
    if not messages:
        return ChatResponse(answer="Please provide a message.")

    # Find the last user message to use as the search query
    last_user_idx = -1
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].role == "user":
            last_user_idx = i
            break
            
    if last_user_idx == -1:
         return ChatResponse(answer="No user message found.")
         
    user_query = messages[last_user_idx].content
    
    # Safety Check
    if is_advice_seeking(user_query):
        return ChatResponse(
            answer=get_refusal_message(),
            grounded=False
        )

    # 1. Retrieval (Basic Lexical / Keyword matching for now, relying on tags/titles)
    # We will grab up to 3 highly relevant excerpts
    # In a full production system this would use vector embeddings.
    stop_words = {"what", "when", "where", "which", "who", "whom", "whose", "why", "how", 
                  "are", "the", "has", "have", "had", "can", "could", "should", "would", 
                  "may", "might", "must", "shall", "will", "do", "does", "did", "is", "am", 
                  "was", "were", "be", "being", "been", "this", "that", "these", "those", 
                  "then", "than", "here", "there", "about", "above", "across", "after", 
                  "against", "along", "among", "around", "at", "before", "behind", "below", 
                  "beneath", "beside", "between", "beyond", "but", "by", "with", "from",
                  "tell", "symptoms", "signs", "causes", "treatment", "cure"}

    raw_terms = user_query.replace('?', '').replace('.', '').replace(',', '').split()
    terms = [t for t in raw_terms if len(t) > 3 and t.lower() not in stop_words]
    
    # Very rudimentary keyword search across title, transcript, and tags
    where_clauses = []
    score_clauses = []
    params = []
    for term in terms:
         where_clauses.append("(title LIKE ? OR text LIKE ? OR transcript LIKE ? OR tags_json LIKE ?)")
         params.extend([f"%{term}%", f"%{term}%", f"%{term}%", f"%{term}%"])
         safe_term = term.replace("'", "''")
         score_clauses.append(f"(CASE WHEN title LIKE '%{safe_term}%' OR tags_json LIKE '%{safe_term}%' OR text LIKE '%{safe_term}%' THEN 1 ELSE 0 END)")
         
    if where_clauses:
        score_expr = " + ".join(score_clauses)
        query_sql = f"""
            SELECT id, title, source_name, summary_json, text, transcript 
            FROM content_items 
            WHERE {" OR ".join(where_clauses)}
            ORDER BY ({score_expr}) DESC
            LIMIT 3
        """
        rows = execute_query(query_sql, tuple(params))
    else:
        # Fallback if query is too short or weird - just get recent stuff as generic context
        rows = execute_query("SELECT id, title, source_name, summary_json, text, transcript FROM content_items ORDER BY id DESC LIMIT 2")
        
    context_blocks = []
    citations = []
    
    import json
    for row in rows:
        title = row["title"]
        source = row["source_name"]
        
        # Use text chunks or summary
        content = row.get("text") or row.get("transcript")
        if not content:
            try:
                summary_data = json.loads(row.get("summary_json", "{}"))
                content = summary_data.get("summary", "")
            except:
                content = "No text available."
                
        # Truncate content to roughly 500 characters per source for context window
        context_blocks.append(f"Source: {title} ({source})\nContent: {content[:1000]}...\n")
        citations.append({"id": row["id"], "title": title, "source_name": source})
        
    context_str = "\n\n".join(context_blocks) if context_blocks else "No relevant context found in the knowledge base."
    
    # 2. Augment & Generate
    system_instruction = SYSTEM_PROMPT.format(context=context_str)
    
    # Convert schema messages to dicts for LLMManager
    llm_messages = [{"role": "system", "content": system_instruction}]
    for m in messages:
        llm_messages.append({"role": m.role, "content": m.content})
        
    llm = get_llm()
    
    try:
        answer = llm.chat(llm_messages, temperature=0.3)
    except Exception as e:
        answer = "I'm sorry, I'm having trouble connecting to my brain right now. " + str(e)
        
    grounded = "not have enough verified information" not in answer.lower()
    
    return ChatResponse(
        answer=answer,
        grounded=grounded,
        citations=citations,
        disclaimer=DISCLAIMER
    )
