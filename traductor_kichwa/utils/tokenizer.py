import unicodedata, re
try:
    from nltk.stem import SnowballStemmer
    stemmer = SnowballStemmer('spanish')
    _HAS_NLTK = True
except ImportError:
    _HAS_NLTK = False

from traductor_kichwa.db.consultas import buscar_morfema_desde_frase, buscar_conjugacion_auto

def normalizar_texto(texto: str) -> str:
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii','ignore').decode('utf-8')
    return texto.lower()

def tokenizar_oracion(texto: str) -> list[str]:
    texto = re.sub(r'[^\w\s]', '', texto)
    return texto.split()

def agrupar_ngramas(tokens: list[str], buscar_morfema_desde_frase) -> list[str]:
    """
    - Coge hasta 3-gramas para morfemas (p.ej. "en la" → pi).
    - Luego, SI NO FUE morfema, agrupa pares para buscar CONTINUOS
    (“esta cocinando”, “estamos jugando”…) usando buscar_conjugacion_auto.
    """
    out, i, n = [], 0, len(tokens)
    while i < n:
        # 1) morfemas compuestos (3 o 2 palabras)
        match = None
        for size in (3,2):
            if i+size <= n:
                frase = ' '.join(tokens[i:i+size])
                if buscar_morfema_desde_frase(frase):
                    match = frase
                    break
        if match:
            out.append(match)
            i += size
            continue

        # 2) verbos en continuo: "esta cocinando", "estamos jugando", etc.
        if i+1 < n:
            duo = f"{tokens[i]} {tokens[i+1]}"
            # probamos con persona_id dummy (1–7) para ver si existe en cualquier persona
            for pid in range(1,8):
                if buscar_conjugacion_auto(duo, pid):
                    out.append(duo)
                    i += 2
                    match = True
                    break
            if match:
                continue

        # 3) token suelto
        out.append(tokens[i])
        i += 1

    return out

def lematizar_palabra(token: str) -> str:
    if _HAS_NLTK:
        return stemmer.stem(token)
    # fallback muy simple
    for suf in ("as","es","an"):
        if token.endswith(suf): return token[:-2]
    for suf in ("a","o"):
        if token.endswith(suf): return token[:-1]
    return token