# db/ensamblador.py

def construir_oracion_kichwa(partes: dict) -> str:
    """
    Monta la oración final en este orden:
    1) sujeto
    2) complementos “normales” (sustantivos, adjetivos, modo, compañía…)
    3) morfemas locativo/temporal/dativo (pi, man, kaman…)
    4) verbo (con sus marcadores de modo_oracional si los hay)
    """
    seq = []
    if partes.get("sujeto"):
        seq.append(partes["sujeto"])

    # 2) complementos “normales”
    seq.extend(partes.get("complemento", []))

    # 3) morfemas locativo/temporal/dativo
    seq.extend(partes.get("preverb", []))

    # 4) verbo
    if partes.get("verbo"):
        seq.append(partes["verbo"])

    # unir y limpiar espacios múltiples
    return " ".join(seq).strip()