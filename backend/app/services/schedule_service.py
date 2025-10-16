"""
Service pour la gestion des horaires de publication
"""
from typing import List, Optional, Dict
from datetime import datetime, time, timedelta
from sqlalchemy.orm import Session
from app.models.schedule_config import ScheduleConfig
from app.schemas.schedule_config import ScheduleConfigCreate, ScheduleConfigUpdate


class ScheduleService:
    def __init__(self, db: Session):
        self.db = db

    def create_schedule_config(self, config: ScheduleConfigCreate) -> ScheduleConfig:
        """Créer une nouvelle configuration d'horaires"""
        db_config = ScheduleConfig(**config.dict())
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        return db_config

    def get_schedule_configs(self, network: Optional[str] = None) -> List[ScheduleConfig]:
        """Récupérer toutes les configurations d'horaires"""
        query = self.db.query(ScheduleConfig)
        if network:
            query = query.filter(ScheduleConfig.network == network)
        return query.order_by(ScheduleConfig.network, ScheduleConfig.day_type).all()

    def get_schedule_config_by_id(self, config_id: int) -> Optional[ScheduleConfig]:
        """Récupérer une configuration par ID"""
        return self.db.query(ScheduleConfig).filter(ScheduleConfig.id == config_id).first()

    def update_schedule_config(self, config_id: int, config_update: ScheduleConfigUpdate) -> Optional[ScheduleConfig]:
        """Mettre à jour une configuration d'horaires"""
        db_config = self.get_schedule_config_by_id(config_id)
        if not db_config:
            return None

        update_data = config_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_config, field, value)

        self.db.commit()
        self.db.refresh(db_config)
        return db_config

    def delete_schedule_config(self, config_id: int) -> bool:
        """Supprimer une configuration d'horaires"""
        db_config = self.get_schedule_config_by_id(config_id)
        if not db_config:
            return False

        self.db.delete(db_config)
        self.db.commit()
        return True

    def get_active_config_for_network_now(self, network: str) -> Optional[ScheduleConfig]:
        """Récupérer la configuration active pour un réseau à l'heure actuelle"""
        now = datetime.now()
        current_weekday = now.weekday()  # 0=Lundi, 6=Dimanche
        
        # Déterminer le type de jour
        if current_weekday < 5:  # Lundi à Vendredi
            day_type = "weekday"
        else:  # Samedi et Dimanche
            day_type = "weekend"

        # Chercher la configuration active
        config = self.db.query(ScheduleConfig).filter(
            ScheduleConfig.network == network,
            ScheduleConfig.day_type == day_type,
            ScheduleConfig.is_active == True
        ).first()

        return config

    def is_publication_allowed_now(self, network: str) -> Dict[str, any]:
        """Vérifier si la publication est autorisée maintenant pour un réseau"""
        config = self.get_active_config_for_network_now(network)
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute

        result = {
            "allowed": False,
            "network": network,
            "current_time": now.strftime("%H:%M"),
            "reason": "",
            "next_available": None,
            "config": config.to_dict() if config else None
        }

        if not config:
            result["reason"] = f"Aucune configuration active pour {network}"
            return result

        if not config.is_active:
            result["reason"] = "Configuration désactivée"
            return result

        # Vérifier si on est dans la plage horaire
        if config.is_time_in_range(current_hour, current_minute):
            result["allowed"] = True
            result["reason"] = "Dans la plage horaire autorisée"
        else:
            result["reason"] = f"Hors plage horaire ({config.start_time}-{config.end_time})"
            # Calculer le prochain créneau disponible
            next_time = self._calculate_next_available_time(config)
            result["next_available"] = next_time

        return result

    def _calculate_next_available_time(self, config: ScheduleConfig) -> str:
        """Calculer la prochaine heure de publication disponible"""
        now = datetime.now()
        
        # Si on est avant l'heure de début aujourd'hui
        start_hour, start_min = map(int, config.start_time.split(':'))
        today_start = now.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
        
        if now < today_start:
            return today_start.strftime("%H:%M")

        # Si on est après l'heure de fin aujourd'hui, chercher demain
        end_hour, end_min = map(int, config.end_time.split(':'))
        today_end = now.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
        
        if now > today_end:
            # Chercher le prochain jour où cette config est active
            next_day = now + timedelta(days=1)
            return next_day.replace(hour=start_hour, minute=start_min, second=0, microsecond=0).strftime("%H:%M")

        return "Maintenant"
    
    def bulk_update_schedules(self, network: str, configs_data: List[Dict]) -> List[ScheduleConfig]:
        """Mettre à jour en masse les horaires d'un réseau et recalculer les posts"""
        # Delete existing configs for the network
        self.db.query(ScheduleConfig).filter(ScheduleConfig.network == network).delete()
        self.db.commit()

        # Create new configs
        new_configs = []
        for config_data in configs_data:
            new_config = ScheduleConfig(**config_data)
            self.db.add(new_config)
            new_configs.append(new_config)
        self.db.commit()
        for config in new_configs:
            self.db.refresh(config)
        
        # 🔄 REPROGRAMMER AUTOMATIQUEMENT les posts qui sont maintenant hors horaires
        self._recalculate_posts_schedule(network)
        
        return new_configs
    
    def _recalculate_posts_schedule(self, network: str):
        """Recalculer la programmation de tous les posts d'un réseau après changement d'horaires"""
        from app.models.publication_queue import PublicationQueue
        
        print(f"🔄 Recalcul programmation pour {network} après changement d'horaires")
        
        # Récupérer tous les posts programmés pour ce réseau
        posts_to_recalculate = self.db.query(PublicationQueue).filter(
            PublicationQueue.network == network,
            PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS'])
        ).all()
        
        for post in posts_to_recalculate:
            old_time = post.scheduled_at
            new_time = self._adjust_time_to_schedule(network, old_time)
            
            if new_time != old_time:
                post.scheduled_at = new_time
                print(f"   📅 Post #{post.id}: {old_time.strftime('%H:%M')} → {new_time.strftime('%H:%M')}")
                
                # Mettre à jour le statut selon les nouveaux horaires
                config = self.get_active_config_for_network_now(network)
                if config and config.is_active:
                    if config.is_time_in_range(new_time.hour, new_time.minute):
                        post.status = "SCHEDULED"
                    else:
                        post.status = "WAITING_HOURS"
        
        self.db.commit()
        print(f"✅ {len(posts_to_recalculate)} posts recalculés pour {network}")

    def _adjust_time_to_schedule(self, network: str, target_time: datetime) -> datetime:
        """Ajuster une heure cible pour qu'elle soit dans un créneau autorisé"""
        config = self.get_active_config_for_network_now(network)
        
        if not config:
            # Pas de config horaire, utiliser l'heure telle quelle
            return target_time
        
        if not config.is_active:
            # Config désactivée, utiliser l'heure telle quelle
            return target_time
        
        # Vérifier si l'heure cible est dans un créneau autorisé
        if config.is_time_in_range(target_time.hour, target_time.minute):
            return target_time
        
        # L'heure n'est pas autorisée, chercher le prochain créneau
        start_hour, start_min = map(int, config.start_time.split(':'))
        end_hour, end_min = map(int, config.end_time.split(':'))
        
        now = datetime.now()
        
        # Calculer les heures d'aujourd'hui
        today_start = now.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
        today_end = now.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
        
        # Si on est APRÈS l'heure de fermeture aujourd'hui, programmer pour demain
        if now > today_end:
            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
        
        # Si on est AVANT l'heure d'ouverture aujourd'hui, programmer pour aujourd'hui
        if now < today_start:
            return today_start
        
        # Si on est dans les horaires mais l'heure cible n'est pas bonne, programmer au prochain créneau
        # Programmer pour demain à l'heure d'ouverture
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)

    def get_publication_schedule_for_network(self, network: str, network_delay_minutes: int = 60) -> List[Dict]:
        """Générer un planning de publication pour un réseau"""
        configs = self.get_schedule_configs(network)
        schedule = []

        for config in configs:
            if not config.is_active:
                continue

            # Générer les créneaux pour cette configuration en utilisant le délai du réseau
            available_minutes = config.get_available_minutes_in_range(network_delay_minutes)
            
            for minute in available_minutes:
                hour = minute // 60
                min_val = minute % 60
                
                schedule.append({
                    "time": f"{hour:02d}:{min_val:02d}",
                    "day_type": config.day_type,
                    "network": config.network,
                    "interval": network_delay_minutes,  # Utilise le délai du réseau
                    "max_posts": config.max_posts_per_day
                })

        return sorted(schedule, key=lambda x: x["time"])

    def create_default_schedules(self):
        """Créer des configurations par défaut pour tous les réseaux"""
        default_configs = [
            # Facebook - Semaine
            {
                "network": "facebook",
                "day_type": "weekday",
                "start_time": "09:00",
                "end_time": "18:00",
                "max_posts_per_day": 3
            },
            # Facebook - Weekend
            {
                "network": "facebook",
                "day_type": "weekend",
                "start_time": "10:00",
                "end_time": "16:00",
                "max_posts_per_day": 2
            },
            # LinkedIn - Semaine
            {
                "network": "linkedin",
                "day_type": "weekday",
                "start_time": "08:00",
                "end_time": "17:00",
                "max_posts_per_day": 4
            },
            # LinkedIn - Weekend
            {
                "network": "linkedin",
                "day_type": "weekend",
                "start_time": "09:00",
                "end_time": "15:00",
                "max_posts_per_day": 2
            },
            # X (Twitter) - Semaine
            {
                "network": "x",
                "day_type": "weekday",
                "start_time": "07:00",
                "end_time": "20:00",
                "max_posts_per_day": 6
            },
            # X (Twitter) - Weekend
            {
                "network": "x",
                "day_type": "weekend",
                "start_time": "09:00",
                "end_time": "18:00",
                "max_posts_per_day": 4
            }
        ]

        for config_data in default_configs:
            # Vérifier si la config existe déjà
            existing = self.db.query(ScheduleConfig).filter(
                ScheduleConfig.network == config_data["network"],
                ScheduleConfig.day_type == config_data["day_type"]
            ).first()

            if not existing:
                config = ScheduleConfigCreate(**config_data)
                self.create_schedule_config(config)
                print(f"✅ Configuration créée: {config_data['network']} - {config_data['day_type']}")

        self.db.commit()
