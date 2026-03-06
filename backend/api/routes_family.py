"""
Family API routes — group creation, member management, saved items.
"""

import json
from fastapi import APIRouter, HTTPException
from backend.core.db import execute_query, execute_insert
from backend.core.schema import (
    CreateFamilyGroupRequest, CreateFamilyGroupResponse,
    AddFamilyMemberRequest, FamilyMemberResponse,
    FamilyGroupDetailResponse, MemberPreferences,
    SaveItemRequest, SaveItemResponse,
    ContentItemResponse,
)

router = APIRouter()


@router.post("/group", response_model=CreateFamilyGroupResponse)
def create_family_group(req: CreateFamilyGroupRequest):
    """Create a new family group."""
    group_id = execute_insert(
        "INSERT INTO family_groups (name) VALUES (?)",
        (req.name,),
    )
    rows = execute_query(
        "SELECT * FROM family_groups WHERE id = ?", (group_id,)
    )
    row = rows[0]
    return CreateFamilyGroupResponse(
        id=row["id"], name=row["name"], created_at=row["created_at"]
    )


@router.post("/member", response_model=FamilyMemberResponse)
def add_family_member(req: AddFamilyMemberRequest):
    """Add a member to a family group."""
    # Verify group exists
    groups = execute_query(
        "SELECT id FROM family_groups WHERE id = ?", (req.group_id,)
    )
    if not groups:
        raise HTTPException(status_code=404, detail="Family group not found")

    prefs_json = req.preferences.model_dump_json()
    topics_json = json.dumps(req.topics)

    member_id = execute_insert(
        """
        INSERT INTO family_members (group_id, name, age_band, preferences_json, topics_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (req.group_id, req.name, req.age_band, prefs_json, topics_json),
    )

    return FamilyMemberResponse(
        id=member_id,
        group_id=req.group_id,
        name=req.name,
        age_band=req.age_band,
        preferences=req.preferences,
        topics=req.topics,
    )


@router.get("/group/{group_id}", response_model=FamilyGroupDetailResponse)
def get_family_group(group_id: int):
    """Get a family group with all its members."""
    groups = execute_query(
        "SELECT * FROM family_groups WHERE id = ?", (group_id,)
    )
    if not groups:
        raise HTTPException(status_code=404, detail="Family group not found")

    group = groups[0]

    members_rows = execute_query(
        "SELECT * FROM family_members WHERE group_id = ?", (group_id,)
    )

    members = []
    for row in members_rows:
        prefs = _parse_preferences(row.get("preferences_json", "{}"))
        topics = _parse_json_list(row.get("topics_json", "[]"))
        members.append(FamilyMemberResponse(
            id=row["id"],
            group_id=row["group_id"],
            name=row["name"],
            age_band=row["age_band"],
            preferences=prefs,
            topics=topics,
        ))

    return FamilyGroupDetailResponse(
        id=group["id"],
        name=group["name"],
        created_at=group["created_at"],
        members=members,
    )


@router.get("/groups")
def list_family_groups():
    """List all family groups."""
    rows = execute_query("SELECT * FROM family_groups ORDER BY created_at DESC")
    return [
        {"id": r["id"], "name": r["name"], "created_at": r["created_at"]}
        for r in rows
    ]


@router.post("/save", response_model=SaveItemResponse)
def save_item_to_library(req: SaveItemRequest):
    """Save a content item to a family group's library."""
    # Verify group and content exist
    groups = execute_query(
        "SELECT id FROM family_groups WHERE id = ?", (req.group_id,)
    )
    if not groups:
        raise HTTPException(status_code=404, detail="Family group not found")

    items = execute_query(
        "SELECT id FROM content_items WHERE id = ?", (req.content_id,)
    )
    if not items:
        raise HTTPException(status_code=404, detail="Content item not found")

    try:
        save_id = execute_insert(
            "INSERT INTO saved_items (group_id, content_id) VALUES (?, ?)",
            (req.group_id, req.content_id),
        )
    except Exception:
        raise HTTPException(status_code=409, detail="Item already saved")

    rows = execute_query("SELECT * FROM saved_items WHERE id = ?", (save_id,))
    row = rows[0]

    return SaveItemResponse(
        id=row["id"],
        group_id=row["group_id"],
        content_id=row["content_id"],
        saved_at=row["saved_at"],
    )


@router.get("/saved/{group_id}")
def get_saved_items(group_id: int):
    """Get all saved items for a family group."""
    rows = execute_query(
        """
        SELECT ci.id, ci.type, ci.title, ci.url, ci.source_name,
               ci.source_tier, ci.published_at, ci.tags_json,
               ci.summary_json, ci.content_length, si.saved_at
        FROM saved_items si
        JOIN content_items ci ON si.content_id = ci.id
        WHERE si.group_id = ?
        ORDER BY si.saved_at DESC
        """,
        (group_id,),
    )

    items = []
    for row in rows:
        items.append({
            "id": row["id"],
            "type": row["type"],
            "title": row["title"],
            "url": row["url"],
            "source_name": row["source_name"],
            "source_tier": row["source_tier"],
            "published_at": row.get("published_at"),
            "tags": _parse_json_list(row.get("tags_json", "[]")),
            "summary": _parse_json_dict(row.get("summary_json", "{}")),
            "saved_at": row.get("saved_at"),
        })

    return {"group_id": group_id, "items": items, "total": len(items)}


def _parse_preferences(val) -> MemberPreferences:
    try:
        data = json.loads(val) if isinstance(val, str) else val
        return MemberPreferences(**data)
    except Exception:
        return MemberPreferences()


def _parse_json_list(val) -> list:
    try:
        result = json.loads(val) if isinstance(val, str) else val
        return result if isinstance(result, list) else []
    except Exception:
        return []


def _parse_json_dict(val) -> dict:
    try:
        result = json.loads(val) if isinstance(val, str) else val
        return result if isinstance(result, dict) else {}
    except Exception:
        return {}
