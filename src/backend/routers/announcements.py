"""
Endpoints for managing announcements in the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """
    Get all active announcements that haven't expired
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Find announcements where:
    # - expiration_date is today or in the future
    # - start_date is today or in the past (if provided)
    query = {
        "expiration_date": {"$gte": today},
        "$or": [
            {"start_date": {"$lte": today}},
            {"start_date": {"$exists": False}},
            {"start_date": None}
        ]
    }
    
    announcements = []
    for announcement in announcements_collection.find(query).sort("priority", -1):
        announcement["_id"] = str(announcement["_id"])
        announcements.append(announcement)
    
    return announcements


@router.get("/all", response_model=List[Dict[str, Any]])
def get_all_announcements(username: str = Query(None)) -> List[Dict[str, Any]]:
    """
    Get all announcements for management (admin only)
    Requires teacher authentication
    """
    if not username:
        raise HTTPException(
            status_code=401, detail="Authentication required")
    
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")
    
    announcements = []
    for announcement in announcements_collection.find().sort("expiration_date", -1):
        announcement["_id"] = str(announcement["_id"])
        announcements.append(announcement)
    
    return announcements


@router.post("", response_model=Dict[str, Any])
def create_announcement(
    title: str,
    message: str,
    expiration_date: str,
    start_date: Optional[str] = None,
    priority: str = "normal",
    username: str = Query(None)
) -> Dict[str, Any]:
    """
    Create a new announcement (admin only)
    Requires teacher authentication
    
    - title: Announcement title
    - message: Announcement message content
    - expiration_date: Date when announcement expires (YYYY-MM-DD format)
    - start_date: Optional date when announcement starts showing (YYYY-MM-DD format)
    - priority: Priority level (low, normal, high)
    - username: Teacher username for authentication
    """
    if not username:
        raise HTTPException(
            status_code=401, detail="Authentication required")
    
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")
    
    # Validate dates
    try:
        exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            if start > exp_date:
                raise HTTPException(
                    status_code=400, detail="Start date cannot be after expiration date")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Validate priority
    if priority not in ["low", "normal", "high"]:
        raise HTTPException(
            status_code=400, detail="Priority must be low, normal, or high")
    
    announcement = {
        "title": title,
        "message": message,
        "expiration_date": expiration_date,
        "start_date": start_date,
        "priority": priority,
        "active": True,
        "created_at": datetime.now().isoformat(),
        "created_by": username
    }
    
    result = announcements_collection.insert_one(announcement)
    announcement["_id"] = str(result.inserted_id)
    
    return announcement


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    title: str,
    message: str,
    expiration_date: str,
    start_date: Optional[str] = None,
    priority: str = "normal",
    username: str = Query(None)
) -> Dict[str, Any]:
    """
    Update an announcement (admin only)
    Requires teacher authentication
    """
    if not username:
        raise HTTPException(
            status_code=401, detail="Authentication required")
    
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")
    
    # Validate dates
    try:
        exp_date = datetime.strptime(expiration_date, "%Y-%m-%d")
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            if start > exp_date:
                raise HTTPException(
                    status_code=400, detail="Start date cannot be after expiration date")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Validate priority
    if priority not in ["low", "normal", "high"]:
        raise HTTPException(
            status_code=400, detail="Priority must be low, normal, or high")
    
    try:
        obj_id = ObjectId(announcement_id)
    except:
        raise HTTPException(
            status_code=400, detail="Invalid announcement ID")
    
    update_data = {
        "title": title,
        "message": message,
        "expiration_date": expiration_date,
        "start_date": start_date,
        "priority": priority,
        "updated_at": datetime.now().isoformat(),
        "updated_by": username
    }
    
    result = announcements_collection.find_one_and_update(
        {"_id": obj_id},
        {"$set": update_data},
        return_document=True
    )
    
    if not result:
        raise HTTPException(
            status_code=404, detail="Announcement not found")
    
    result["_id"] = str(result["_id"])
    return result


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    username: str = Query(None)
) -> Dict[str, Any]:
    """
    Delete an announcement (admin only)
    Requires teacher authentication
    """
    if not username:
        raise HTTPException(
            status_code=401, detail="Authentication required")
    
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")
    
    try:
        obj_id = ObjectId(announcement_id)
    except:
        raise HTTPException(
            status_code=400, detail="Invalid announcement ID")
    
    result = announcements_collection.find_one_and_delete({"_id": obj_id})
    
    if not result:
        raise HTTPException(
            status_code=404, detail="Announcement not found")
    
    return {"status": "success", "message": "Announcement deleted"}
