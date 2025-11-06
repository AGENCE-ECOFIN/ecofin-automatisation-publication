import openai
import re
from app.core.config import settings
from typing import Dict, Any, List, Optional


class LLMService:
    # Mapping des variables disponibles dans les prompts
    VARIABLES_MAPPING = {
        '{titre}': 'title',
        '{contenu}': 'content',
        '{url}': 'source_url'
    }
    def __init__(self):
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY

    def generate_social_media_posts(self, article_content: str, custom_prompt: str = None, network_prompts: Dict[str, str] = None, target_networks: List[str] = None, source_url: str = None, title: str = None, source_image: str = None) -> Dict[str, Any]:
        """
        Génère des posts pour différents réseaux sociaux à partir du contenu d'un article
        """
        # Définir les réseaux cibles par défaut si non spécifiés
        if target_networks is None:
            target_networks = ["facebook", "linkedin", "x"]
        
        # Mode test sans OpenAI - génération de contenu simple
        if not settings.OPENAI_API_KEY:
            return self._generate_test_posts(article_content, target_networks, source_url)
        
        # DEBUG: Afficher les prompts reçus
        print(f"🔍 [LLM] generate_social_media_posts - network_prompts reçus: {network_prompts}")
        print(f"🔍 [LLM] network_prompts est None: {network_prompts is None}")
        if network_prompts:
            print(f"🔍 [LLM] network_prompts contient des valeurs: {any(network_prompts.values())}")
            print(f"🔍 [LLM] Détail des prompts: {network_prompts}")
        
        # Si des prompts spécifiques par réseau sont fournis, les utiliser
        # Vérifier que network_prompts existe et contient au moins une valeur non vide
        has_specific_prompts = network_prompts and any(
            prompt and prompt.strip() for prompt in network_prompts.values()
        )
        
        if has_specific_prompts:
            print(f"✅ [LLM] Utilisation des prompts spécifiques par réseau")
            print(f"🔍 [LLM] Prompts disponibles: {list(network_prompts.keys())}")
            return self._generate_posts_with_specific_prompts(article_content, network_prompts, target_networks, source_url, title, source_image)
        else:
            print(f"⚠️ [LLM] Pas de prompts spécifiques valides, utilisation du prompt général")
            if network_prompts:
                print(f"🔍 [LLM] network_prompts existe mais est vide ou contient seulement des chaînes vides")
        
        # Sinon, utiliser le prompt général
        networks_description = ", ".join(target_networks).title()
        base_prompt = custom_prompt or f"""
        Crée des posts pour les réseaux sociaux suivants à partir de cet article: {networks_description}.
        
        Pour chaque réseau social, adapte le contenu selon ses spécificités :
        - Facebook : Ton convivial, engagement communautaire, hashtags modérés
        - LinkedIn : Ton professionnel, focus business/carrière, contenu informatif
        - X (Twitter) : Messages concis, hashtags pertinents, engagement immédiat
        
        IMPORTANT : TOUJOURS inclure le lien de l'article à la fin de chaque post.
        
        Retourne les posts dans le format JSON suivant :
        {{
            "facebook": "contenu pour Facebook",
            "linkedin": "contenu pour LinkedIn", 
            "x": "contenu pour X/Twitter"
        }}
        
        Garde un ton professionnel et engageant. Chaque post doit être optimisé pour son réseau.
        Le lien DOIT apparaître à la fin de chaque post.
        """

        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": base_prompt},
                    {"role": "user", "content": f"Article à traiter:\n{article_content}"}
                ],
                max_tokens=1500,
                temperature=0.7
            )

            generated_text = response.choices[0].message.content
            
            # Parser la réponse pour extraire les différents posts
            return self._parse_llm_response(generated_text, target_networks)
            
        except Exception as e:
            print(f"Erreur lors de la génération LLM: {e}")
            # Retourner des messages d'erreur pour tous les réseaux cibles
            error_posts = {}
            for network in target_networks:
                error_posts[network] = "Erreur lors de la génération"
            return error_posts

    def _replace_variables(self, prompt: str, article_data: Dict[str, Any]) -> str:
        """
        Remplace les variables dans le prompt par leurs valeurs réelles
        Variables disponibles: {titre}, {contenu}, {url}
        Si une variable n'est pas disponible (None ou vide), elle est retirée du prompt
        """
        if not prompt:
            return prompt
        
        result = prompt
        for var_name, var_key in self.VARIABLES_MAPPING.items():
            value = article_data.get(var_key, '')
            
            # Si la variable existe dans le prompt
            if var_name in result:
                # Si la valeur est disponible (non None et non vide)
                if value and str(value).strip():
                    # Remplacer la variable par sa valeur
                    value_str = str(value).strip()
                    result = result.replace(var_name, value_str)
                else:
                    # Retirer la variable du prompt si elle n'est pas disponible
                    # Retirer la variable et nettoyer les espaces autour
                    result = result.replace(var_name, '')
                    # Nettoyer les espaces multiples et les retours à la ligne multiples
                    import re
                    result = re.sub(r'\s+', ' ', result)  # Remplacer espaces multiples par un seul
                    result = re.sub(r'\n\s*\n+', '\n\n', result)  # Remplacer retours à la ligne multiples par deux max
                    print(f"🔍 [LLM] Variable {var_name} non disponible, retirée du prompt")
        
        return result.strip()
    
    def _generate_posts_with_specific_prompts(self, article_content: str, network_prompts: Dict[str, str], target_networks: List[str], source_url: str = None, title: str = None, source_image: str = None) -> Dict[str, Any]:
        """
        Génère des posts en utilisant des prompts spécifiques pour chaque réseau
        Les variables {titre}, {contenu}, {url} sont remplacées dynamiquement
        """
        generated_posts = {}
        
        # Préparer les données de l'article pour le remplacement des variables
        article_data = {
            'title': title or '',
            'content': article_content.replace('Titre: ', '').split('\nContenu: ')[-1] if 'Contenu: ' in article_content else article_content,
            'source_url': source_url or ''
        }
        
        for network in target_networks:
            try:
                # Récupérer le prompt spécifique pour ce réseau
                network_prompt = network_prompts.get(network)
                
                # DEBUG: Afficher le prompt AVANT remplacement
                print(f"🔍 [LLM] Prompt pour {network} (avant remplacement): {network_prompt[:200] if network_prompt else 'AUCUN'}...")
                
                if not network_prompt:
                    # Si pas de prompt spécifique, utiliser un prompt par défaut
                    network_prompt = f"Crée un post pour {network} basé sur cet article."
                
                # Remplacer les variables dans le prompt
                network_prompt = self._replace_variables(network_prompt, article_data)
                
                # DEBUG: Afficher le prompt APRÈS remplacement
                print(f"🔍 [LLM] Prompt pour {network} (après remplacement): {network_prompt[:200]}...")
                
                # Ajouter instruction pour inclure le lien UNIQUEMENT si {url} n'a pas été utilisé dans le prompt
                # Vérifier si le prompt contient déjà {url} ou si source_url n'est pas dans le prompt final
              #  if source_url and network_prompt and '{url}' not in network_prompt and source_url not in network_prompt:
               #     network_prompt += f"\n\nIMPORTANT : Inclure le lien {source_url} à la fin du post."
                
                # Générer le post pour ce réseau spécifique
                response = self._call_openai_with_retry(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": network_prompt},
                        {"role": "user", "content": f"Article à traiter:\n{article_content}"}
                    ],
                    max_tokens=500,
                    temperature=0.7,
                    network=network
                )
                
                if response:
                    generated_posts[network] = response.strip()
                    print(f"✅ Post généré avec succès pour {network}")
                else:
                    generated_posts[network] = f"Erreur lors de la génération pour {network}"
                
            except Exception as e:
                print(f"❌ Erreur lors de la génération pour {network}: {e}")
                generated_posts[network] = f"Erreur lors de la génération pour {network}"
        
        return generated_posts

    def _parse_llm_response(self, response_text: str, target_networks: List[str] = None) -> Dict[str, Any]:
        """
        Parse la réponse du LLM pour extraire les posts par réseau social
        """
        if target_networks is None:
            target_networks = ["facebook", "linkedin", "x"]
        
        posts = {network: "" for network in target_networks}
        
        # Essayer d'abord de parser comme JSON
        try:
            import json
            # Nettoyer le texte pour extraire le JSON
            cleaned_text = response_text.strip()
            if cleaned_text.startswith('```'):
                # Enlever les backticks
                lines = cleaned_text.split('\n')
                json_lines = []
                in_json = False
                for line in lines:
                    if line.strip().startswith('{') and not in_json:
                        in_json = True
                    if in_json:
                        json_lines.append(line)
                    if line.strip().endswith('}') and in_json:
                        break
                cleaned_text = '\n'.join(json_lines)
            
            # Parser le JSON
            parsed_json = json.loads(cleaned_text)
            
            # Récupérer les posts pour chaque réseau cible
            for network in target_networks:
                if network in parsed_json:
                    posts[network] = parsed_json[network]
                else:
                    # Essayer des variantes de noms
                    variants = {
                        'x': ['twitter', 'x', 'x.com'],
                        'facebook': ['facebook', 'fb'],
                        'linkedin': ['linkedin', 'linkedin.com']
                    }
                    for variant in variants.get(network, [network]):
                        if variant in parsed_json:
                            posts[network] = parsed_json[variant]
                            break
            
            # Vérifier si on a récupéré au moins un post
            if any(posts.values()):
                return posts
                
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Si le parsing JSON échoue, utiliser l'ancienne méthode
        lines = response_text.split('\n')
        current_platform = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Détecter le réseau social
            if 'facebook' in line.lower() or 'fb' in line.lower():
                current_platform = 'facebook'
            elif 'linkedin' in line.lower():
                current_platform = 'linkedin'
            elif 'twitter' in line.lower() or 'x' in line.lower():
                current_platform = 'x'
            elif current_platform and current_platform in posts and line:
                # Ajouter le contenu au post
                if posts[current_platform]:
                    posts[current_platform] += " " + line
                else:
                    posts[current_platform] = line
        
        # Si aucun format spécifique n'est détecté, utiliser le texte complet
        if not any(posts.values()):
            # Diviser le texte en parties pour chaque réseau
            words = response_text.split()
            chunk_size = len(words) // len(target_networks) if target_networks else 3
            
            for i, network in enumerate(target_networks):
                start_idx = i * chunk_size
                end_idx = start_idx + chunk_size if i < len(target_networks) - 1 else len(words)
                posts[network] = " ".join(words[start_idx:end_idx])
        
        return posts
    
    def _generate_test_posts(self, article_content: str, target_networks: List[str], source_url: str = None) -> Dict[str, Any]:
        """
        Génère des posts de test sans OpenAI pour le développement
        """
        # Extraire le titre de l'article
        lines = article_content.split('\n')
        title = lines[0].replace('Titre: ', '') if lines else "Article sans titre"
        
        # Générer du contenu simple pour chaque réseau
        posts = {}
        
        # Préparer le lien à ajouter
        link_text = f"\n\n🔗 {source_url}" if source_url else ""
        
        for network in target_networks:
            if network == "facebook":
                posts[network] = f"📰 {title}\n\nDécouvrez cet article intéressant sur notre page ! #Actualités #EcoFin{link_text}"
            elif network == "linkedin":
                posts[network] = f"Article professionnel : {title}\n\nUn regard approfondi sur les développements récents dans notre secteur. #Business #Innovation{link_text}"
            elif network == "x":
                posts[network] = f"🚀 {title}\n\n#Actualités #EcoFin{link_text}"
            else:
                posts[network] = f"📰 {title}\n\nContenu adapté pour {network}{link_text}"
        
        return posts

    def _call_openai_with_retry(self, model: str, messages: List[Dict], max_tokens: int = 500, temperature: float = 0.7, network: str = "unknown", max_retries: int = 3) -> str:
        """
        Appelle OpenAI avec retry en cas d'erreur
        """
        import time
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 Tentative {attempt + 1}/{max_retries} pour {network}")
                
                response = openai.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                if response and response.choices:
                    content = response.choices[0].message.content
                    print(f"✅ Réponse reçue pour {network} (tentative {attempt + 1})")
                    return content
                else:
                    print(f"⚠️ Réponse vide pour {network} (tentative {attempt + 1})")
                    
            except openai.RateLimitError as e:
                print(f"⏳ Rate limit atteint pour {network} (tentative {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2  # Backoff exponentiel
                    print(f"⏰ Attente de {wait_time} secondes...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Nombre maximum de tentatives atteint pour {network}")
                    return None
                    
            except openai.APIError as e:
                print(f"❌ Erreur API OpenAI pour {network} (tentative {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return None
                    
            except Exception as e:
                print(f"❌ Erreur inattendue pour {network} (tentative {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return None
        
        return None
