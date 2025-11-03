"""
Service pour la gestion des horaires de publication
"""
from typing import List, Optional, Dict
from datetime import datetime, time, timedelta
from sqlalchemy.orm import Session
from app.models.schedule_config import ScheduleConfig
from app.schemas.schedule_config import ScheduleConfigCreate, ScheduleConfigUpdate
from app.services.audit_service import AuditService


class ScheduleService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def create_schedule_config(self, config: ScheduleConfigCreate) -> ScheduleConfig:
        """Créer une nouvelle configuration d'horaires"""
        config_dict = config.dict()
        
        # Convertir day_type en day_of_week si nécessaire
        if config_dict.get('day_type') and config_dict.get('day_of_week') is None:
            config_dict['day_of_week'] = None  # Toujours global maintenant
        
        db_config = ScheduleConfig(**config_dict)
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

    def update_schedule_config(self, config_id: int, config_update: ScheduleConfigUpdate, user_id: Optional[int] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[ScheduleConfig]:
        """Mettre à jour une configuration d'horaires"""
        db_config = self.get_schedule_config_by_id(config_id)
        if not db_config:
            return None

        # Sauvegarder les anciennes valeurs pour l'audit
        old_values = {
            "network": db_config.network,
            "start_time": str(db_config.start_time) if db_config.start_time else None,
            "end_time": str(db_config.end_time) if db_config.end_time else None,
            "is_active": db_config.is_active
        }

        update_data = config_update.dict(exclude_unset=True)
        modified_fields = list(update_data.keys())
        for field, value in update_data.items():
            setattr(db_config, field, value)

        self.db.commit()
        self.db.refresh(db_config)
        
        # Logger la mise à jour de la config horaire
        if user_id:
            self.audit_service.log_action(
                action="CONFIG_UPDATE",
                entity_type="schedule_config",
                user_id=user_id,
                entity_id=config_id,
                description=f"Modification de la configuration horaire pour '{db_config.network}'",
                metadata={
                    "network": db_config.network,
                    "modified_fields": modified_fields,
                    "old_values": old_values,
                    "new_values": {field: str(getattr(db_config, field, None)) if hasattr(db_config, field) else None for field in modified_fields}
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
        
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
        from datetime import datetime
        
        now = datetime.now()
        current_weekday = now.weekday()  # 0=lundi, 6=dimanche
        
        # Déterminer si c'est un jour de semaine ou week-end
        if current_weekday < 5:  # Lundi à Vendredi
            day_type = 'weekday'
        else:  # Samedi et Dimanche
            day_type = 'weekend'
        
        # Chercher la configuration pour le type de jour actuel
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
        if not config:
            return "Maintenant"  # Si pas de config, permettre immédiatement
            
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
    
    def bulk_update_schedules(self, network: str, configs_data: List[Dict], user_id: Optional[int] = None, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> List[ScheduleConfig]:
        """Mettre à jour en masse les horaires d'un réseau et recalculer les posts"""
        # Delete existing configs for the network
        self.db.query(ScheduleConfig).filter(ScheduleConfig.network == network).delete()
        self.db.commit()

        # Create new configs
        new_configs = []
        for config_data in configs_data:
            # Convertir l'objet Pydantic en dictionnaire
            config_dict = config_data.dict() if hasattr(config_data, 'dict') else config_data
            
            # Convertir day_type en day_of_week si nécessaire
            if config_dict.get('day_type') and config_dict.get('day_of_week') is None:
                config_dict['day_of_week'] = None  # Toujours None maintenant
            
            new_config = ScheduleConfig(**config_dict)
            self.db.add(new_config)
            new_configs.append(new_config)
        self.db.commit()
        for config in new_configs:
            self.db.refresh(config)
        
        # 🔄 REPROGRAMMER AUTOMATIQUEMENT les posts qui sont maintenant hors horaires
        self._recalculate_posts_schedule(network)
        
        # Logger la mise à jour en masse
        if user_id:
            self.audit_service.log_action(
                action="CONFIG_UPDATE",
                entity_type="schedule_config",
                user_id=user_id,
                entity_id=None,  # Mise à jour en masse, pas d'ID spécifique
                description=f"Mise à jour en masse des configurations horaires pour '{network}'",
                metadata={
                    "network": network,
                    "configs_count": len(new_configs),
                    "configs": [{"id": config.id, "start_time": str(config.start_time), "end_time": str(config.end_time)} for config in new_configs]
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
        
        return new_configs
    
    def _recalculate_posts_schedule(self, network: str):
        """Recalculer la programmation de tous les posts d'un réseau après changement d'horaires"""
        from app.models.publication_queue import PublicationQueue
        from datetime import datetime, timezone, timedelta
        
        print(f"🔄 Recalcul programmation pour {network} après changement d'horaires")
        
        # Récupérer tous les posts programmés pour ce réseau (y compris en pause)
        posts_to_recalculate = self.db.query(PublicationQueue).filter(
            PublicationQueue.network == network,
            PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS'])
        ).all()
        
        # Récupérer aussi les posts en pause qui pourraient être affectés
        paused_posts = self.db.query(PublicationQueue).filter(
            PublicationQueue.network == network,
            PublicationQueue.is_paused == True,
            PublicationQueue.status.in_(['SCHEDULED', 'WAITING_HOURS', 'PENDING'])
        ).all()
        
        posts_to_recalculate.extend(paused_posts)
        
        # Grouper par feed pour respecter le FIFO par feed
        posts_by_feed = {}
        for post in posts_to_recalculate:
            if post.feed_id not in posts_by_feed:
                posts_by_feed[post.feed_id] = []
            posts_by_feed[post.feed_id].append(post)
        
        for feed_id, feed_posts in posts_by_feed.items():
            print(f"   📊 Feed #{feed_id}: {len(feed_posts)} posts à recalculer")
            
            # Trier par ancienne scheduled_at pour maintenir l'ordre
            feed_posts.sort(key=lambda p: p.scheduled_at or datetime.min)
            
            # Calculer la nouvelle heure de base (maintenant)
            base_time = datetime.now(timezone.utc)
            
            for i, post in enumerate(feed_posts):
                old_time = post.scheduled_at
                
                # Calculer la nouvelle heure en respectant les délais entre posts du même feed
                if i == 0:
                    # Premier post du feed
                    new_time = self._adjust_time_to_schedule(network, base_time)
                else:
                    # Posts suivants avec délai
                    from app.models.network_config import NetworkConfig
                    network_config = self.db.query(NetworkConfig).filter(
                        NetworkConfig.network == network
                    ).first()
                    delay_minutes = network_config.default_publication_delay if network_config else 60
                    
                    # Heure du post précédent + délai
                    prev_post_time = posts_by_feed[feed_id][i-1].scheduled_at
                    base_time_with_delay = prev_post_time + timedelta(minutes=delay_minutes)
                    new_time = self._adjust_time_to_schedule(network, base_time_with_delay)
                
                # Mettre à jour
                post.scheduled_at = new_time
                print(f"   📅 Post #{post.id}: {old_time.strftime('%d/%m %H:%M')} → {new_time.strftime('%d/%m %H:%M')}")
                
                # Mettre à jour le statut selon les nouveaux horaires
                config = self.get_active_config_for_network_now(network)
                if config and config.is_active:
                    if config.is_time_in_range(new_time.hour, new_time.minute):
                        # Si le post était en pause, le remettre en pause avec la nouvelle heure
                        if post.is_paused:
                            print(f"   ⏸️ Post #{post.id} en pause - heure mise à jour: {new_time.strftime('%H:%M')}")
                        post.status = "SCHEDULED"
                    else:
                        post.status = "WAITING_HOURS"
                else:
                    post.status = "SCHEDULED"
        
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

    def calculate_optimal_schedule_time(self, network: str, base_time: datetime = None, delay_minutes: int = None) -> Dict:
        """
        Calcule l'heure optimale de publication en tenant compte des horaires d'ouverture et des délais
        
        Args:
            network: Réseau social (facebook, linkedin, x)
            base_time: Heure de base pour le calcul (par défaut maintenant)
            delay_minutes: Délai en minutes (par défaut depuis NetworkConfig)
            
        Returns:
            Dict avec l'heure optimale et les détails du calcul
        """
        from app.models.network_config import NetworkConfig
        
        if base_time is None:
            base_time = datetime.now()
        
        # Récupérer le délai depuis NetworkConfig si non fourni
        if delay_minutes is None:
            network_config = self.db.query(NetworkConfig).filter(
                NetworkConfig.network == network,
                NetworkConfig.is_active == True
            ).first()
            delay_minutes = network_config.default_publication_delay if network_config else 30
        
        # Récupérer la configuration d'horaires active
        schedule_config = self.get_active_config_for_network_now(network)
        
        if not schedule_config:
            # Pas de config horaire, programmer immédiatement avec délai
            optimal_time = base_time + timedelta(minutes=delay_minutes)
            return {
                "optimal_time": optimal_time,
                "reason": "Aucune configuration horaire - délai appliqué",
                "delay_minutes": delay_minutes,
                "schedule_config": None,
                "adjusted": False
            }
        
        # Calculer l'heure cible avec délai
        target_time = base_time + timedelta(minutes=delay_minutes)
        
        # Vérifier si l'heure cible est dans les horaires d'ouverture
        if schedule_config.is_time_in_range(target_time.hour, target_time.minute):
            return {
                "optimal_time": target_time,
                "reason": f"Heure cible dans les horaires d'ouverture ({schedule_config.start_time}-{schedule_config.end_time})",
                "delay_minutes": delay_minutes,
                "schedule_config": schedule_config.to_dict(),
                "adjusted": False
            }
        
        # L'heure cible n'est pas dans les horaires, ajuster
        adjusted_time = self._adjust_time_to_schedule(network, target_time)
        
        return {
            "optimal_time": adjusted_time,
            "reason": f"Heure ajustée aux horaires d'ouverture ({schedule_config.start_time}-{schedule_config.end_time})",
            "delay_minutes": delay_minutes,
            "schedule_config": schedule_config.to_dict(),
            "adjusted": True,
            "original_time": target_time
        }

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

        created_count = 0
        existing_count = 0
        
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
                created_count += 1
            else:
                print(f"ℹ️  Configuration déjà existante: {config_data['network']} - {config_data['day_type']}")
                existing_count += 1

        self.db.commit()
        
        if created_count == 0 and existing_count > 0:
            print(f"\n✅ Toutes les configurations ({existing_count}) existent déjà - Aucune modification nécessaire")
        elif created_count > 0:
            print(f"\n✅ Initialisation terminée: {created_count} créée(s), {existing_count} déjà existante(s)")

    def recalculate_queue_for_network(self, network: str) -> int:
        """Recalculer les horaires des posts en attente pour un réseau"""
        from app.models.publication_queue import PublicationQueue
        from datetime import datetime, timezone
        
        # Récupérer tous les posts en attente pour ce réseau
        pending_posts = self.db.query(PublicationQueue).filter(
            PublicationQueue.network == network,
            PublicationQueue.status.in_(['SCHEDULED', 'PENDING'])
        ).all()
        
        updated_count = 0
        
        for post in pending_posts:
            try:
                # Recalculer le scheduled_at avec la nouvelle configuration
                new_scheduled_at = self._calculate_next_available_datetime(network)
                
                if new_scheduled_at and new_scheduled_at != post.scheduled_at:
                    post.scheduled_at = new_scheduled_at
                    updated_count += 1
                    print(f"🔄 Post {post.id} recalculé: {post.scheduled_at}")
                
            except Exception as e:
                print(f"❌ Erreur lors du recalcul du post {post.id}: {e}")
                continue
        
        if updated_count > 0:
            self.db.commit()
            print(f"✅ {updated_count} posts recalculés pour {network}")
        
        return updated_count

    def _calculate_next_available_datetime(self, network: str) -> datetime:
        """Calculer le prochain créneau disponible comme datetime"""
        from datetime import datetime, timezone, timedelta
        
        # Récupérer la configuration active
        config = self.get_active_config_for_network_now(network)
        
        if not config:
            # Si pas de config, programmer dans 1 heure
            return datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Parser les horaires
        start_hour, start_min = map(int, config.start_time.split(':'))
        end_hour, end_min = map(int, config.end_time.split(':'))
        
        now = datetime.now(timezone.utc)
        
        # Si on est dans les horaires, programmer maintenant
        current_hour = now.hour
        current_min = now.minute
        
        if (start_hour < current_hour < end_hour) or \
           (current_hour == start_hour and current_min >= start_min) or \
           (current_hour == end_hour and current_min <= end_min):
            return now
        
        # Sinon, programmer au début des horaires du jour suivant
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
