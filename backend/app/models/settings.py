from typing import Dict, Any, Optional
from beanie import Document
from pydantic import Field

class SystemSettings(Document):
    """Global platform settings and AI configurations"""
    category: str = Field(..., description="Category of settings (e.g., 'ai', 'general')")
    data: Dict[str, Any] = Field(default_factory=dict, description="Configuration key-value pairs")
    
    class Settings:
        name = "system_settings"

    @classmethod
    async def get_by_category(cls, category: str) -> Optional["SystemSettings"]:
        return await cls.find_one(cls.category == category)

    @classmethod
    async def update_settings(cls, category: str, data: Dict[str, Any]):
        settings = await cls.get_by_category(category)
        if settings:
            settings.data.update(data)
            await settings.save()
        else:
            settings = cls(category=category, data=data)
            await settings.insert()
        return settings
