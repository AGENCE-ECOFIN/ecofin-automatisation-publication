import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service pour envoyer des emails via SMTP"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Envoie un email
        
        Args:
            to_email: Email du destinataire
            subject: Sujet de l'email
            html_content: Contenu HTML de l'email
            text_content: Contenu texte alternatif (optionnel)
            
        Returns:
            True si l'email a été envoyé avec succès
        """
        try:
            # Créer le message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Ajouter le contenu texte si fourni
            if text_content:
                part1 = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(part1)
            
            # Ajouter le contenu HTML
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            # Connexion au serveur SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Activer le chiffrement TLS
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email envoyé avec succès à {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'envoi de l'email à {to_email}: {str(e)}")
            return False
    
    def send_welcome_email(self, to_email: str, username: str, password: str) -> bool:
        """
        Envoie un email de bienvenue avec les identifiants
        
        Args:
            to_email: Email du destinataire
            username: Nom d'utilisateur
            password: Mot de passe temporaire
            
        Returns:
            True si l'email a été envoyé avec succès
        """
        subject = f"Bienvenue sur {settings.APP_NAME}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #6C63FF 0%, #4834DF 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .credentials {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 20px 0;
                    border-left: 4px solid #6C63FF;
                }}
                .button {{
                    display: inline-block;
                    background: #6C63FF;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎉 Bienvenue sur {settings.APP_NAME} !</h1>
            </div>
            <div class="content">
                <p>Bonjour <strong>{username}</strong>,</p>
                
                <p>Votre compte a été créé avec succès ! Vous pouvez maintenant vous connecter à la plateforme.</p>
                
                <div class="credentials">
                    <h3>📧 Vos identifiants de connexion :</h3>
                    <p><strong>Email :</strong> {to_email}</p>
                    <p><strong>Nom d'utilisateur :</strong> {username}</p>
                    <p><strong>Mot de passe temporaire :</strong> {password}</p>
                </div>
                
                <p>⚠️ <strong>Important :</strong> Pour des raisons de sécurité, nous vous recommandons de changer votre mot de passe dès votre première connexion.</p>
                
                <div style="text-align: center;">
                    <a href="{settings.FRONTEND_URL}/login" class="button">Se connecter maintenant</a>
                </div>
                
                <p>Si vous avez des questions, n'hésitez pas à contacter l'administrateur.</p>
            </div>
            <div class="footer">
                <p>Cet email a été envoyé automatiquement par {settings.APP_NAME}</p>
                <p>&copy; 2025 {settings.APP_NAME}. Tous droits réservés.</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Bienvenue sur {settings.APP_NAME} !
        
        Bonjour {username},
        
        Votre compte a été créé avec succès !
        
        Vos identifiants de connexion :
        - Email : {to_email}
        - Nom d'utilisateur : {username}
        - Mot de passe temporaire : {password}
        
        IMPORTANT : Changez votre mot de passe dès votre première connexion.
        
        Connectez-vous sur : {settings.FRONTEND_URL}/login
        
        {settings.APP_NAME}
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_password_reset_email(
        self,
        to_email: str,
        username: str,
        reset_token: str
    ) -> bool:
        """
        Envoie un email de réinitialisation de mot de passe
        
        Args:
            to_email: Email du destinataire
            username: Nom d'utilisateur
            reset_token: Token de réinitialisation
            
        Returns:
            True si l'email a été envoyé avec succès
        """
        subject = f"Réinitialisation de votre mot de passe - {settings.APP_NAME}"
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #6C63FF 0%, #4834DF 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .button {{
                    display: inline-block;
                    background: #6C63FF;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .warning {{
                    background: #fff3cd;
                    border: 1px solid #ffc107;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔐 Réinitialisation de mot de passe</h1>
            </div>
            <div class="content">
                <p>Bonjour <strong>{username}</strong>,</p>
                
                <p>Vous avez demandé la réinitialisation de votre mot de passe sur {settings.APP_NAME}.</p>
                
                <div style="text-align: center;">
                    <a href="{reset_url}" class="button">Réinitialiser mon mot de passe</a>
                </div>
                
                <div class="warning">
                    <p>⚠️ <strong>Important :</strong></p>
                    <ul>
                        <li>Ce lien est valable pendant <strong>1 heure</strong></li>
                        <li>Si vous n'avez pas demandé cette réinitialisation, ignorez cet email</li>
                        <li>Ne partagez jamais ce lien avec qui que ce soit</li>
                    </ul>
                </div>
                
                <p>Si le bouton ne fonctionne pas, copiez ce lien dans votre navigateur :</p>
                <p style="word-break: break-all; background: white; padding: 10px; border-radius: 5px;">{reset_url}</p>
            </div>
            <div class="footer">
                <p>Cet email a été envoyé automatiquement par {settings.APP_NAME}</p>
                <p>&copy; 2025 {settings.APP_NAME}. Tous droits réservés.</p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Réinitialisation de mot de passe - {settings.APP_NAME}
        
        Bonjour {username},
        
        Vous avez demandé la réinitialisation de votre mot de passe.
        
        Cliquez sur ce lien pour réinitialiser votre mot de passe :
        {reset_url}
        
        IMPORTANT :
        - Ce lien est valable pendant 1 heure
        - Si vous n'avez pas demandé cette réinitialisation, ignorez cet email
        
        {settings.APP_NAME}
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_notification_email(
        self,
        to_email: str,
        title: str,
        message: str
    ) -> bool:
        """
        Envoie un email de notification générique
        
        Args:
            to_email: Email du destinataire
            title: Titre de la notification
            message: Message de la notification
            
        Returns:
            True si l'email a été envoyé avec succès
        """
        subject = f"{title} - {settings.APP_NAME}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #6C63FF 0%, #4834DF 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px;
                    border-radius: 0 0 10px 10px;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📧 {title}</h1>
            </div>
            <div class="content">
                {message}
            </div>
            <div class="footer">
                <p>Cet email a été envoyé automatiquement par {settings.APP_NAME}</p>
                <p>&copy; 2025 {settings.APP_NAME}. Tous droits réservés.</p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content, message)

