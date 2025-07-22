from traductor_kichwa.utils.tokenizer import normalizar_texto, tokenizar_oracion, agrupar_ngramas
from traductor_kichwa.db.consultas import (
    buscar_pronombre_es,
    buscar_conjugacion_auto,
    buscar_traduccion_palabra,
    buscar_morfema_desde_frase,
    obtener_marcadores_modo,
)
from traductor_kichwa.db.ensamblador import construir_oracion_kichwa

# Tipos de morfema que van ANTES del verbo y deben extraerse a 'preverb'
PREVERB_TYPES = {"ubicacion", "direccion", "tiempo/espacio"}
# 2) Alias para pronombres no registrados (singular/plural)
PRONOUN_ALIASES = {
    "nosotras": "nosotros",
    "ellas": "ellos",
    "vosotras": "vosotros",
    # ...añade más si las necesitas
}
def construir_complemento(tokens_es: list[str]):
    comp_norm = []
    comp_pre   = []
    i = 0
    n = len(tokens_es)
    while i < n:
        tok = tokens_es[i].lower()
        m   = buscar_morfema_desde_frase(tok)
        if m:
            forma = m["forma"]
            if i+1 < n:
                nxt = tokens_es[i+1].lower()
                raiz = buscar_traduccion_palabra(nxt)
                if raiz:
                    fusion = raiz + forma
                else:
                    fusion = tokens_es[i+1] + forma  # Une el morfema a la palabra original si no hay traducción
                if m["tipo"] in PREVERB_TYPES:
                    comp_pre.append(fusion)
                else:
                    comp_norm.append(fusion)
                i += 2
                continue
            if m["tipo"] in PREVERB_TYPES:
                comp_pre.append(forma)
            else:
                comp_norm.append(forma)
            i += 1
            continue
        raiz = buscar_traduccion_palabra(tok)
        if raiz:
            comp_norm.append(raiz)
        else:
            comp_norm.append(tokens_es[i])  # Agrega la palabra original si no hay traducción
        i += 1

    return comp_norm, comp_pre

def detectar_modo(entrada: str) -> str:
    low = entrada.strip().lower()
    if low.startswith("¿") or low.endswith("?"):
        return "pregunta"
    if " no " in f" {low} ":
        return "negacion"
    return "afirmacion"

def traducir_oracion(entrada: str) -> str:
    norm = normalizar_texto(entrada)
    toks = agrupar_ngramas(tokenizar_oracion(norm), buscar_morfema_desde_frase)

    sujeto_es = PRONOUN_ALIASES.get(toks[0].lower(), toks[0].lower())
    persona   = buscar_pronombre_es(sujeto_es)
    if not persona:
        raise ValueError(f"Pronombre '{sujeto_es}' no registrado en tabla persona.")
    sujeto_ki = persona["pronombre_ki"]
    pid       = persona["id"]

    modo = detectar_modo(entrada)
    if modo == "negacion":
        sujeto_ki += " mana"
        toks = [t for t in toks if t.lower() != "no"]

    verb_idx = None
    verbo_ki = None
    for i, tok in enumerate(toks[1:], start=1):
        c = buscar_conjugacion_auto(tok, pid)
        if c:
            verb_idx = i
            verbo_ki = c
            break
    if verb_idx is None:
        verb_idx = 1
        t0 = toks[1]
        verbo_ki = buscar_conjugacion_auto(t0, pid) \
                or buscar_traduccion_palabra(t0) \
                or t0

    comp_es = toks[1:verb_idx] + toks[verb_idx+1:]
    comp_norm, comp_pre = construir_complemento(comp_es)

    if modo != "negacion":
        for m in obtener_marcadores_modo(modo):
            if m["posicion"] == "antes_verbo":
                verbo_ki = f"{m['marcador']} {verbo_ki}"
            else:
                verbo_ki = f"{verbo_ki} {m['marcador']}"

    partes = {
        "sujeto":     sujeto_ki,
        "complemento": comp_norm,
        "preverb":    comp_pre,
        "verbo":      verbo_ki
    }
    return construir_oracion_kichwa(partes)

def traducir_futuro_inmediato(entrada: str) -> str:
    norm = normalizar_texto(entrada)
    toks = agrupar_ngramas(tokenizar_oracion(norm), buscar_morfema_desde_frase)

    if len(toks) < 4 or toks[2].lower() != "a":
        raise ValueError("Estructura no compatible con futuro inmediato.")

    sujeto_es = PRONOUN_ALIASES.get(toks[0].lower(), toks[0].lower())
    verbo_ir  = toks[1].lower()
    infinitivo_es = toks[3].lower()
    resto = toks[4:]

    persona = buscar_pronombre_es(sujeto_es)
    if not persona:
        raise ValueError(f"Pronombre '{sujeto_es}' no registrado.")
    sujeto_ki = persona["pronombre_ki"]
    pid = persona["id"]

    conj_verbo = buscar_conjugacion_auto(verbo_ir, pid)
    if not conj_verbo:
        raise ValueError(f"No se encontró conjugación de '{verbo_ir}'.")

    # modificar conjugación al estilo futuro inmediato (kri + sufijo)
    if conj_verbo.endswith("nki"):
        raiz = conj_verbo[:-3]
        sufijo = "nki"
    elif conj_verbo.endswith("ni"):
        raiz = conj_verbo[:-2]
        sufijo = "ni"
    elif conj_verbo.endswith("nchik"):
        raiz = conj_verbo[:-6]
        sufijo = "nchik"
    elif conj_verbo.endswith("kichik"):
        raiz = conj_verbo[:-6]
        sufijo = "kichik"
    elif conj_verbo.endswith("kuna"):
        raiz = conj_verbo[:-4]
        sufijo = "kuna"
    elif conj_verbo.endswith("ri"):
        raiz = conj_verbo[:-2]
        sufijo = "ri"
    else:
        raiz = conj_verbo
        sufijo = ""
    verbo_ki = f"{raiz}kri{sufijo}"

    # El verbo en infinitivo se vuelve parte del complemento (sustantivado + morfema si aplica)
    comp_norm, comp_pre = [], []

    inf_comp = ["a", infinitivo_es]  # intenta aplicar 'a' como morfema con el verbo
    norm_inf, pre_inf = construir_complemento(inf_comp)
    comp_norm.extend(norm_inf)
    comp_pre.extend(pre_inf)

    if resto:
        norm_extra, pre_extra = construir_complemento(resto)
        comp_norm.extend(norm_extra)
        comp_pre.extend(pre_extra)

    partes = {
        "sujeto": sujeto_ki,
        "complemento": comp_norm,
        "preverb": comp_pre,
        "verbo": verbo_ki
    }
    return construir_oracion_kichwa(partes)



if __name__ == "__main__":
    print("=== Traductor Español → Kichwa ===")
    while True:
        entrada = input("Oración (o 'salir'): ")
        if entrada.lower() in ("salir", "exit"):
            print("¡Hasta luego!")
            break
        try:
            if " a " in entrada and any(entrada.lower().startswith(p) for p in ("yo", "tu",'tú', "el", "ella", "nosotros", "nosotras", "ustedes", "ellos", "ellas")):
                print("Kichwa:", traducir_futuro_inmediato(entrada))
            else:
                print("Kichwa:", traducir_oracion(entrada))
        except Exception as e:
            print("ERROR:", e)