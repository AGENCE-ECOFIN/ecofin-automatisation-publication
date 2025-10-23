"""
Modèle pour la gestion des horaires de publication par réseau social
Gestion différenciée semaine/week-end/pauses
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ScheduleConfig(Base):
    __tablename__ = "schedule_configs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Réseau social concerné
    network = Column(String(50), nullable=False, index=True)  # facebook, linkedin, x
    
    # Type de jour
    day_type = Column(String(20), nullable=False, index=True)  # weekday, weekend, holiday
    
    # Horaires de publication (format 24h)
    start_time = Column(String(5), nullable=False)  # "09:00"
    end_time = Column(String(5), nullable=False)    # "18:00"
    
    # Configuration spécifique
    is_active = Column(Boolean, default=True)  # Activer/désactiver ce créneau
    
    # Note: L'intervalle est géré par le délai global du réseau (NetworkConfig)
    # interval_minutes = Column(Integer, default=30)  # SUPPRIMÉ - duplication avec délai réseau
    
    # Maximum de publications par jour dans ce créneau
    max_posts_per_day = Column(Integer, default=5)
    
    # Jours spécifiques si applicable (JSON array des numéros de jour 0-6)
    # 0=Lundi, 1=Mardi, ..., 6=Dimanche
    specific_days = Column(JSON, nullable=True)  # [0, 1, 2, 3, 4] pour semaine
    
    # Dates de début/fin pour les périodes spéciales (vacances, etc.)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ScheduleConfig(network={self.network}, day_type={self.day_type}, {self.start_time}-{self.end_time})>"

    def is_time_in_range(self, hour: int, minute: int = 0) -> bool:
        """Vérifie si une heure donnée est dans le créneau horaire"""
        start_hour = self.start_time.hour
        start_min = self.start_time.minute
        end_hour = self.end_time.hour
        end_min = self.end_time.minute
        
        current_minutes = hour * 60 + minute
        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        
        return start_minutes <= current_minutes <= end_minutes

    def get_available_minutes_in_range(self, interval_minutes: int = 30) -> list:
        """Retourne toutes les minutes disponibles dans le créneau"""
        start_hour = self.start_time.hour
        start_min = self.start_time.minute
        end_hour = self.end_time.hour
        end_min = self.end_time.minute
        
        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min
        
        available_minutes = []
        for minute in range(start_minutes, end_minutes + 1, interval_minutes):
            available_minutes.append(minute)
            
        return available_minutes

    def to_dict(self):
        """Convertit en dictionnaire pour l'API"""
        return {
            'id': self.id,
            'network': self.network,
            'day_type': self.day_type,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'is_active': self.is_active,
            'max_posts_per_day': self.max_posts_per_day,
            'specific_days': self.specific_days,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
