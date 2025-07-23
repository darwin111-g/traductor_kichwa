# db/consultas.py
from traductor_kichwa.config.conexion import conectar_bd
from typing import Optional, List, Dict
def buscar_pronombre_es(pronombre_es: str) -> Optional[Dict]:
    conn = conectar_bd()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, pronombre_ki, numero
        FROM persona
        WHERE pronombre_es = %s
        LIMIT 1
    """, (pronombre_es,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def buscar_conjugacion_auto(verbo_es: str, persona_id: int) -> Optional[str]:
    mapping = [
        ("verbo_conjugado_es",        "verbo_conjugado"       ),
        ("verbo_conjugado_pasado_es", "verbo_conjugado_pasado"),
        ("verbo_conjugado_futuro_es", "verbo_conjugado_futuro"),
        ("verbo_continuo_es",         "verbo_continuo"        ),
    ]
    conn = conectar_bd()
    cur = conn.cursor(dictionary=True)
    for col_es, col_ki in mapping:
        cur.execute(f"""
            SELECT {col_ki}
            FROM conjugacion_ki
            WHERE {col_es} = %s
            AND persona_id = %s
            LIMIT 1
        """, (verbo_es, persona_id))
        row = cur.fetchone()
        if row:
            cur.close()
            conn.close()
            return row[col_ki]
    cur.close()
    conn.close()
    return None

def buscar_traduccion_palabra(lema_es: str) -> Optional[str]:
    conn = conectar_bd()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT pk.raiz
        FROM palabra_es pe
        JOIN traduccion t  ON pe.id = t.palabra_es_id
        JOIN palabra_ki pk ON pk.id = t.palabra_ki_id
        WHERE pe.lema = %s
        LIMIT 1
    """, (lema_es,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row["raiz"] if row else None

def buscar_todas_traducciones(lema_es: str) -> List[str]:
    conn = conectar_bd()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT pk.raiz
        FROM palabra_es pe
        JOIN traduccion t ON pe.id = t.palabra_es_id
        JOIN palabra_ki pk ON pk.id = t.palabra_ki_id
        WHERE pe.lema = %s
    """, (lema_es,))
    traducciones = [row["raiz"] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return traducciones

def buscar_morfema_desde_frase(frase_es: str) -> Optional[Dict]:
    conn = conectar_bd()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT m.id, m.forma,m.tipo, m.modo_aplicacion, m.elemento_a_eliminar
        FROM traduccion_morfema tm
        JOIN morfema m ON tm.morfema_id = m.id
        WHERE tm.frase_es = %s
        LIMIT 1
    """, (frase_es,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def obtener_marcadores_modo(tipo_modo: str) -> List[Dict]:
    conn = conectar_bd()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT marcador, posicion
        FROM modo_oracional
        WHERE tipo = %s
    """, (tipo_modo,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

