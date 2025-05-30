# app/models/activity.py

from typing import List, Optional
from pydantic import BaseModel


# --- Skill ---
class SkillBase(BaseModel):
    name: str


class SkillCreate(SkillBase):
    pass


class SkillResponse(SkillBase):
    id: int

    class Config:
        from_attributes = True


# --- Activity ---
class ActivityBase(BaseModel):
    name: str
    description: Optional[str] = None
    duration: int
    required_monitors: int = 1


class ActivityCreate(ActivityBase):
    skill_ids: List[int]  # IDs de habilidades a vincular


class ActivityResponse(ActivityBase):
    id: int
    skills: List[SkillResponse] = []

    class Config:
        from_attributes = True


# --- ActivitySkill (solo si quieres exponer la relación como tal) ---
class ActivitySkillCreate(BaseModel):
    activity_id: int
    skill_id: int


class ActivitySkillResponse(BaseModel):
    id: int
    activity_id: int
    skill_id: int

    class Config:
        from_attributes = True
