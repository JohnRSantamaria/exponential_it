# app/db/models/activity.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy.schema import Index


class Activity(Base):
    __tablename__ = "activities_activity"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    duration = Column(Integer, nullable=False)  # minutos
    required_monitors = Column(Integer, default=1)

    skills = relationship(
        "ActivitySkill", back_populates="activity", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Activity(name={self.name})>"


class Skill(Base):
    __tablename__ = "activities_skill"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    activities = relationship(
        "ActivitySkill", back_populates="skill", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Skill(name={self.name})>"


class ActivitySkill(Base):
    __tablename__ = "activities_activityskill"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(
        Integer, ForeignKey("activities_activity.id", ondelete="CASCADE")
    )
    skill_id = Column(Integer, ForeignKey("activities_skill.id", ondelete="CASCADE"))

    activity = relationship("Activity", back_populates="skills")
    skill = relationship("Skill", back_populates="activities")

    __table_args__ = (
        UniqueConstraint("activity_id", "skill_id", name="unique_activity_skill"),
        Index("idx_activity_skill", "activity_id", "skill_id"),
    )

    def __repr__(self):
        return (
            f"<ActivitySkill(activity_id={self.activity_id}, skill_id={self.skill_id})>"
        )
