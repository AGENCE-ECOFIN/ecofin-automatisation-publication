"""
Schémas Pydantic pour la gestion des horaires de publication
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


class ScheduleConfigBase(BaseModel):
    network: str = Field(..., description="Réseau social (facebook, linkedin, x)")
    day_type: Optional[str] = Field(None, description="Type de jour (weekday, weekend, holiday)")
    day_of_week: Optional[int] = Field(None, description="Jour de la semaine (0=Lundi, 6=Dimanche)")
    start_time: str = Field(..., description="Heure de début (format HH:MM)")
    end_time: str = Field(..., description="Heure de fin (format HH:MM)")
    is_active: bool = Field(True, description="Activer/désactiver ce créneau")
    specific_days: Optional[List[int]] = Field(None, description="Jours spécifiques (0-6, 0=Lundi)")
    period_start: Optional[datetime] = Field(None, description="Début de période spéciale")
    period_end: Optional[datetime] = Field(None, description="Fin de période spéciale")

    @validator('start_time', 'end_time')
    def validate_time_format(cls, v):
        """Valide le format HH:MM ou convertit un objet time"""
        try:
            # Si c'est déjà un objet time, le convertir en string
            if hasattr(v, 'hour') and hasattr(v, 'minute'):
                return v.strftime('%H:%M')
            
            # Si c'est une chaîne, la valider
            hour, minute = map(int, v.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Heure invalide")
            return v
        except:
            raise ValueError("Format invalide, utilisez HH:MM")

    @validator('end_time')
    def validate_end_after_start(cls, v, values):
        """Valide que end_time > start_time"""
        if 'start_time' in values:
            start_hour, start_min = map(int, values['start_time'].split(':'))
            end_hour, end_min = map(int, v.split(':'))
            
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min
            
            if end_minutes <= start_minutes:
                raise ValueError("L'heure de fin doit être après l'heure de début")
        return v

    @validator('day_of_week')
    def validate_day_of_week(cls, v):
        """Valide le jour de la semaine"""
        if v is not None and not (0 <= v <= 6):
            raise ValueError("Le jour de la semaine doit être entre 0 (Lundi) et 6 (Dimanche)")
        return v

    @validator('specific_days')
    def validate_specific_days(cls, v):
        """Valide les jours spécifiques"""
        if v is not None:
            for day in v:
                if not (0 <= day <= 6):
                    raise ValueError("Les jours doivent être entre 0 (Lundi) et 6 (Dimanche)")
        return v

    @validator('day_type')
    def validate_day_type(cls, v):
        """Valide le type de jour"""
        if v is None:
            return v
        allowed_types = ['weekday', 'weekend', 'holiday', 'specific', 'global']
        if v not in allowed_types:
            raise ValueError(f"Type de jour invalide. Utilisez: {', '.join(allowed_types)}")
        return v

    @validator('network')
    def validate_network(cls, v):
        """Valide le réseau social"""
        allowed_networks = ['facebook', 'linkedin', 'x']
        if v not in allowed_networks:
            raise ValueError(f"Réseau invalide. Utilisez: {', '.join(allowed_networks)}")
        return v


class ScheduleConfigCreate(ScheduleConfigBase):
    pass


class ScheduleConfigUpdate(BaseModel):
    network: Optional[str] = None
    day_type: Optional[str] = None
    day_of_week: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_active: Optional[bool] = None
    max_posts_per_day: Optional[int] = Field(None, ge=1, le=50)
    specific_days: Optional[List[int]] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class ScheduleConfigResponse(ScheduleConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduleConfigBulkUpdate(BaseModel):
    """Pour mettre à jour plusieurs configurations en une fois"""
    network: str
    configs: List[ScheduleConfigCreate]


class ScheduleStatusResponse(BaseModel):
    """Statut actuel des horaires pour un réseau"""
    network: str
    is_active_now: bool
    current_config: Optional[ScheduleConfigResponse]
    next_available_time: Optional[str]
    reason: str


class PaginatedScheduleConfigResponse(BaseModel):
    items: List[ScheduleConfigResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
