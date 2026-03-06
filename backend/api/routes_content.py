"""
Content API routes — search, detail, Q&A, and explain endpoints.
"""

import json
from fastapi import APIRouter, HTTPException, Query
from backend.core.db import execute_query
from backend.core.safety import is_advice_seeking, get_refusal_message, DISCLAIMER
from backend.core.schema import (
    ContentSearchResponse, ContentItemResponse, ContentDetailResponse,
    ContentQARequest, ContentQAResponse, ContentExplainResponse,
)
from backend.core.utils import get_source_tier_badge

router = APIRouter()


@router.get("/search", response_model=ContentSearchResponse)
def search_content(
    q: str = Query(default="", description="Search keyword"),
    topic: str = Query(default="", description="Filter by topic tag"),
    content_type: str = Query(default="", description="Filter by type: article, video"),
    limit: int = Query(default=5, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """
    Search verified content items by keyword and/or topic.
    Returns only content from trusted, allowlisted sources.
    Uses LLM search expansion when keyword yields few results.
    """
    # Safety check on search query
    if q and is_advice_seeking(q):
        return ContentSearchResponse(
            items=[],
            total=0,
            disclaimer=get_refusal_message(),
        )

    # Build query
    filter_conditions = []
    filter_params = []

    if topic:
        filter_conditions.append("tags_json LIKE ?")
        filter_params.append(f"%{topic}%")

    if content_type:
        if content_type == "short-form":
            filter_conditions.append("(type IN ('short_video', 'instagram_reel') OR (type = 'video' AND (url LIKE '%instagram.com/reel%' OR url LIKE '%youtube.com/shorts%')))")
        elif content_type == "video":
            filter_conditions.append("type = 'video' AND type != 'instagram_reel' AND url NOT LIKE '%instagram.com/reel%' AND url NOT LIKE '%youtube.com/shorts%'")
        else:
            filter_conditions.append("type = ?")
            filter_params.append(content_type)

    search_conditions = []
    search_params = []
    if q:
        search_conditions.append("(title LIKE ? OR text LIKE ?)")
        search_params.extend([f"%{q}%", f"%{q}%"])

    def build_where_clause(search_cond, search_prm):
        all_conds = []
        all_prms = []
        if search_cond:
            all_conds.append(f"({search_cond})")
            all_prms.extend(search_prm)
        if filter_conditions:
            all_conds.extend(filter_conditions)
            all_prms.extend(filter_params)
        
        clause = " AND ".join(all_conds) if all_conds else "1=1"
        return clause, all_prms

    base_search_cond = " OR ".join(search_conditions) if search_conditions else ""
    where_clause, params = build_where_clause(base_search_cond, search_params)

    # Count
    count_query = f"SELECT COUNT(*) as cnt FROM content_items WHERE {where_clause}"
    count_result = execute_query(count_query, tuple(params))
    total = count_result[0]["cnt"] if count_result else 0

    # Use LLM expansion when keyword search finds few results
    # (symptom queries like "chest pain" won't keyword-match, but "lupus" will)
    if q and total < 5:
        try:
            from backend.llm.search_enhancer import expand_search_query
            expansion = expand_search_query(q)

            if expansion.get("expanded_terms") or expansion.get("matched_topics"):
                # Build expanded search
                expanded_conditions = []
                expanded_params = []

                # Search expanded terms in title/text
                for term in expansion.get("expanded_terms", []):
                    expanded_conditions.append("(title LIKE ? OR text LIKE ?)")
                    expanded_params.extend([f"%{term}%", f"%{term}%"])

                # Search matched topics in tags
                for matched_topic in expansion.get("matched_topics", []):
                    expanded_conditions.append("tags_json LIKE ?")
                    expanded_params.append(f"%{matched_topic}%")

                if expanded_conditions:
                    expanded_search = " OR ".join(expanded_conditions)

                    # Combine original + expanded
                    if base_search_cond:
                        combined_search = f"({base_search_cond}) OR ({expanded_search})"
                        combined_search_params = search_params + expanded_params
                    else:
                        combined_search = expanded_search
                        combined_search_params = expanded_params

                    combined_where, combined_params = build_where_clause(combined_search, combined_search_params)

                    # Re-count
                    count_result = execute_query(
                        f"SELECT COUNT(*) as cnt FROM content_items WHERE {combined_where}",
                        tuple(combined_params),
                    )
                    new_total = count_result[0]["cnt"] if count_result else 0

                    if new_total > total:
                        where_clause = combined_where
                        params = combined_params
                        total = new_total
        except Exception:
            pass  # Fallback to original search silently

    # Layer 5: Reliability & Relevance Ranker
    # Rank by source tier (org > creator), then recency.
    # We assign higher base weight to verified_org (98) vs verified_creator (85).
    #
    # To fix "random" search and improve exact match relevance:
    # If a query is provided, we compute a basic exact-match relevance score:
    # matching the query in the title gets highest priority, then text, then tags.

    if q:
        safe_q = q.replace("'", "''")
        relevance_score = f"""
            (CASE WHEN title LIKE '%{safe_q}%' THEN 50 ELSE 0 END) +
            (CASE WHEN tags_json LIKE '%{safe_q}%' THEN 30 ELSE 0 END) +
            (CASE WHEN text LIKE '%{safe_q}%' THEN 10 ELSE 0 END) DESC,
        """
    else:
        relevance_score = ""

    reliability_sort = f"""
        {relevance_score}
        CASE WHEN source_tier = 'verified_org' THEN 98 ELSE 85 END DESC,
        published_at DESC,
        id DESC
    """
    order_clause = reliability_sort
    
    if q and ("video" in q.lower() or "short" in q.lower()) and not content_type:
        order_clause = f"(type IN ('video', 'short_video')) DESC, {reliability_sort}"

    query = f"""
        SELECT id, type, title, url, source_name, source_tier,
               published_at, tags_json, summary_json, content_length
        FROM content_items
        WHERE {where_clause}
        ORDER BY {order_clause}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    rows = execute_query(query, tuple(params))

    items = []
    for row in rows:
        items.append(ContentItemResponse(
            id=row["id"],
            type=row["type"],
            title=row["title"],
            url=row["url"],
            source_name=row["source_name"],
            source_tier=row["source_tier"],
            published_at=row.get("published_at"),
            tags=_parse_json_list(row.get("tags_json", "[]")),
            summary=_parse_json_dict(row.get("summary_json", "{}")),
            content_length=row.get("content_length", 0),
        ))

    return ContentSearchResponse(items=items, total=total)


@router.get("/{item_id}", response_model=ContentDetailResponse)
def get_content_detail(item_id: int):
    """Get full detail for a single content item with proof-of-trust card and related topics."""
    rows = execute_query(
        "SELECT * FROM content_items WHERE id = ?", (item_id,)
    )

    if not rows:
        raise HTTPException(status_code=404, detail="Content item not found")

    row = rows[0]
    summary = _parse_json_dict(row.get("summary_json", "{}"))
    tags = _parse_json_list(row.get("tags_json", "[]"))

    trust_card = {
        "source_tier_badge": get_source_tier_badge(row["source_tier"]),
        "why_trusted": f"From allowlisted source: {row['source_name']}",
        "published_at": row.get("published_at"),
        "summary": summary.get("summary", ""),
        "key_points": summary.get("key_points", []),
        "warnings": summary.get("warnings", []),
    }

    # Get related topic suggestions
    related_topics = []
    try:
        from backend.llm.related_topics import suggest_related_topics
        related_topics = suggest_related_topics(
            title=row["title"],
            current_tags=tags,
            text=row.get("text") or row.get("transcript") or "",
        )
    except Exception:
        pass  # Gracefully skip if LLM unavailable

    return ContentDetailResponse(
        id=row["id"],
        type=row["type"],
        title=row["title"],
        url=row["url"],
        source_name=row["source_name"],
        source_tier=row["source_tier"],
        published_at=row.get("published_at"),
        tags=tags,
        summary=summary,
        content_length=row.get("content_length", 0),
        text=row.get("text"),
        transcript=row.get("transcript"),
        trust_card=trust_card,
        related_topics=related_topics,
    )


@router.post("/{item_id}/ask", response_model=ContentQAResponse)
def ask_about_content(item_id: int, req: ContentQARequest):
    """
    Ask a question about a specific content item.
    Answer is grounded ONLY in the article's source text.
    """
    # Safety check
    if is_advice_seeking(req.question):
        return ContentQAResponse(
            answer=get_refusal_message(),
            grounded=False,
            source_title="",
            source_name="",
        )

    rows = execute_query(
        "SELECT title, source_name, text, transcript FROM content_items WHERE id = ?",
        (item_id,),
    )

    if not rows:
        raise HTTPException(status_code=404, detail="Content item not found")

    row = rows[0]
    content_text = row.get("text") or row.get("transcript") or ""

    if not content_text:
        return ContentQAResponse(
            answer="This content item does not have extractable text to answer questions from.",
            grounded=False,
            source_title=row["title"],
            source_name=row["source_name"],
        )

    from backend.llm.content_qa import answer_question

    result = answer_question(
        question=req.question,
        title=row["title"],
        source_name=row["source_name"],
        text=content_text,
    )

    return ContentQAResponse(**result)


@router.get("/{item_id}/explain", response_model=ContentExplainResponse)
def explain_content(
    item_id: int,
    level: str = Query(default="standard", pattern=r"^(simple|standard|detailed)$"),
):
    """
    Get an explanation of the content at a specific reading level.
    Levels: simple (kids/teens), standard (default), detailed (in-depth).
    """
    rows = execute_query(
        "SELECT title, source_name, text, transcript, summary_json FROM content_items WHERE id = ?",
        (item_id,),
    )

    if not rows:
        raise HTTPException(status_code=404, detail="Content item not found")

    row = rows[0]
    content_text = row.get("text") or row.get("transcript") or ""
    summary = _parse_json_dict(row.get("summary_json", "{}"))
    summary_text = summary.get("summary", "")

    from backend.llm.explain import explain_content as llm_explain

    result = llm_explain(
        title=row["title"],
        source_name=row["source_name"],
        text=content_text,
        summary=summary_text,
        level=level,
    )

    return ContentExplainResponse(**result)


def _parse_json_list(val) -> list:
    if isinstance(val, list):
        return val
    try:
        result = json.loads(val) if val else []
        return result if isinstance(result, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _parse_json_dict(val) -> dict:
    if isinstance(val, dict):
        return val
    try:
        result = json.loads(val) if val else {}
        return result if isinstance(result, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}
