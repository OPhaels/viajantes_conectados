import re
import urllib.request
import urllib.error
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
 
# Domínios bloqueados (conteúdo adulto/sensível conhecido)
DOMINIOS_BLOQUEADOS = [
    'pornhub', 'xvideos', 'xnxx', 'redtube', 'youporn',
    'onlyfans', 'fansly', 'brazzers', 'naughtyamerica',
    'playboy', 'hustler', 'penthouse',
]
 
# Extensões de imagem aceitas
EXTENSOES_IMAGEM = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif']
 
# Domínios de hospedagem de imagem confiáveis (opcional — mais restritivo)
DOMINIOS_CONFIAVEIS = [
    'imgur.com', 'i.imgur.com',
    'unsplash.com', 'images.unsplash.com',
    'pexels.com', 'images.pexels.com',
    'flickr.com', 'live.staticflickr.com',
    'googleusercontent.com',
    'wikimedia.org', 'upload.wikimedia.org',
    'booking.com', 'cf.bstatic.com',
    'airbnb.com',
    'tripadvisor.com', 'media-cdn.tripadvisor.com',
    'amazonaws.com', 's3.amazonaws.com',
    'cloudinary.com', 'res.cloudinary.com',
    'staticflickr.com',
    'instagram.com', 'cdninstagram.com',
    'pinimg.com',
]
 
 
def validar_url_imagem(url: str, restrito_dominios: bool = False) -> tuple[bool, str]:
    """
    Valida se uma URL aponta para uma imagem pública segura.
 
    Retorna (True, '') se válida, ou (False, mensagem_erro) se inválida.
    """
    if not url or not url.strip():
        return False, 'URL vazia.'
 
    url = url.strip()
 
    # Deve começar com https
    if not url.startswith('https://'):
        return False, 'Use apenas URLs com HTTPS.'
 
    # Verifica domínios bloqueados
    url_lower = url.lower()
    for dominio in DOMINIOS_BLOQUEADOS:
        if dominio in url_lower:
            return False, f'URL de domínio não permitido.'
 
    # Verifica se tem extensão de imagem (mais permissivo — aceita qualquer HTTPS)
    parsed_path = url.split('?')[0].lower()  # ignora query string
    tem_extensao = any(parsed_path.endswith(ext) for ext in EXTENSOES_IMAGEM)
 
    # Modo restrito: só domínios confiáveis
    if restrito_dominios:
        dominio_url = re.sub(r'^https?://', '', url).split('/')[0].lower()
        dominio_url = dominio_url.replace('www.', '')
        confiavel = any(
            dominio_url == d or dominio_url.endswith('.' + d)
            for d in DOMINIOS_CONFIAVEIS
        )
        if not confiavel:
            return False, 'Use imagens de sites conhecidos (Unsplash, Imgur, Pexels, etc.)'
 
    # Tenta verificar se a URL retorna uma imagem (HEAD request)
    try:
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0 (compatible; ViajantesConectados/1.0)')
        with urllib.request.urlopen(req, timeout=5) as resp:
            content_type = resp.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                if not tem_extensao:
                    return False, 'A URL não aponta para uma imagem.'
    except urllib.error.URLError:
        # Se não conseguir verificar, aceita se tiver extensão de imagem
        if not tem_extensao:
            return False, 'Não foi possível verificar a URL. Use uma URL direta de imagem.'
    except Exception:
        if not tem_extensao:
            return False, 'URL inválida ou inacessível.'
 
    return True, ''
 
 
def validar_lista_urls_imagem(urls: list, max_urls: int = 6) -> list[str]:
    """
    Valida uma lista de URLs. Retorna lista de erros (vazia se tudo OK).
    """
    erros = []
 
    if len(urls) > max_urls:
        erros.append(f'Máximo de {max_urls} imagens permitidas.')
        return erros
 
    for i, url in enumerate(urls, 1):
        valido, msg = validar_url_imagem(url)
        if not valido:
            erros.append(f'Imagem {i}: {msg}')
 
    return erros