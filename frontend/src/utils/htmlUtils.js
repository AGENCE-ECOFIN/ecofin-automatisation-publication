/**
 * Utilitaires pour nettoyer le contenu HTML
 */

/**
 * Nettoie le contenu HTML en supprimant les balises et en gardant seulement le texte
 * @param {string} html - Contenu HTML à nettoyer
 * @param {number} maxLength - Longueur maximale du texte (défaut: 200)
 * @returns {string} Texte nettoyé
 */
export const cleanHtmlContent = (html, maxLength = 200) => {
  if (!html) return 'Aucun contenu';
  
  // Supprimer les balises HTML
  let cleanText = html.replace(/<[^>]*>/g, '');
  
  // Supprimer les entités HTML
  cleanText = cleanText.replace(/&amp;/g, '&')
                      .replace(/&lt;/g, '<')
                      .replace(/&gt;/g, '>')
                      .replace(/&quot;/g, '"')
                      .replace(/&#39;/g, "'");
  
  // Nettoyer les espaces multiples
  cleanText = cleanText.replace(/\s+/g, ' ').trim();
  
  // Tronquer si nécessaire
  if (cleanText.length > maxLength) {
    cleanText = cleanText.substring(0, maxLength) + '...';
  }
  
  return cleanText;
};

/**
 * Extrait le texte principal d'un contenu HTML
 * @param {string} html - Contenu HTML
 * @returns {string} Texte principal extrait
 */
export const extractMainText = (html) => {
  if (!html) return 'Aucun contenu';
  
  // Supprimer les liens et images
  let text = html.replace(/<a[^>]*>.*?<\/a>/gi, '');
  text = text.replace(/<img[^>]*>/gi, '');
  
  // Nettoyer le HTML
  text = cleanHtmlContent(text, 300);
  
  return text;
};

