# utils/estructuras.py
from db.consultas import buscar_categoria_gramatical

def analizar_estructura(tokens: list[str]) -> dict:
    """
    Busca en los tokens el pronombre (sujeto) y el verbo (infinitivo),
    todo lo que venga después va a 'complemento'.
    """
    sujeto = None
    verbo  = None
    resto  = []

    for t in tokens:
        cat = buscar_categoria_gramatical(t)
        # si aún no tenemos sujeto y es pronombre, lo tomamos
        if sujeto is None and cat == "pronombre":
            sujeto = t
            continue
        # si aún no tenemos verbo y es verbo, lo tomamos
        if verbo is None and cat == "verbo":
            verbo = t
            continue
        # lo demás va al complemento
        resto.append(t)

    return {
        "sujeto":     sujeto  or "",
        "verbo":      verbo   or "",
        "complemento": resto
    }