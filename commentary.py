"""
commentary.py
=============
Genera un comentari en llenguatge natural (catala) per a cada accio,
traduint les metriques ja calculades (biaix, estesa/stretch, potencial
restant, regim) en una frase entenedora per prendre decisions rapides,
sense haver d'interpretar numeros.

Cada situacio (categoria) te diverses variants de frase. Cada vegada
que es genera l'informe (cada ~15 minuts, quan s'actualitzen les dades
retardades), es tria una frase a l'atzar dins la categoria que toqui,
perque el text no surti sempre identic encara que la situacio de fons
sigui similar.

IMPORTANT: aixo NO es una predicio ni consell financer. Nomes tradueix
a paraules senyals TECNICS ja calculats sobre l'ESTAT ACTUAL del preu.
"""

import random

from models import StockReport


def _category(r: StockReport) -> str:
    """Classifica la situacio actual en una de les 5 categories base."""
    bias = r.bias.bias
    stretch = r.stretch.stretch_level
    potential = r.remaining_potential.category

    if bias in ("BAIXISTA_CLAR", "BAIXISTA_LLEU"):
        return "BAIXISTA"
    if bias == "MIXT":
        return "INDECIS"

    # A partir d'aqui, es alcista (CLAR o LLEU): afinem amb stretch/potencial.
    if stretch == "ALT" or potential == "ENTRADA_TARDANA":
        return "ALCISTA_ESTIRAT"
    if potential == "MOLT_RECORREGUT" and stretch in ("BAIX", "MITJA"):
        return "ALCISTA_AMB_MARGE"
    return "ALCISTA_NORMAL"


_PHRASES = {
    "ALCISTA_AMB_MARGE": [
        "Tendencia alcista neta i encara li queda recorregut real fins a l'objectiu: bon moment per valorar l'entrada.",
        "Puja amb forca i sense estar encara massa estesa: el marge fins a l'objectiu es ampli, situacio favorable.",
        "Alcista i amb marge de sobres: no sembla que hagi tocat sostre encara, es pot valorar entrar-hi.",
        "Bona pinta: tendencia clara amunt i encara hi ha recorregut abans de topar amb l'objectiu.",
        "Moment interessant: la pujada te suport i encara no s'ha exhaurit el marge fins a l'objectiu.",
    ],
    "ALCISTA_NORMAL": [
        "Tendencia alcista, sense senyals d'esgotament preocupants, pero tampoc amb marge extraordinari: situacio correcta, sense presses.",
        "Puja amb normalitat, ni molt estesa ni amb marge enorme: es pot valorar amb prudencia.",
        "Alcista moderat: res que faci saltar les alarmes, pero tampoc el millor moment possible per entrar-hi de cap.",
        "Tendencia a favor pero sense res destacable ara mateix: ni urgencia ni motiu de precaucio especial.",
    ],
    "ALCISTA_ESTIRAT": [
        "Ull: tot i ser alcista, el preu ja esta molt estes i li queda poc recorregut. Millor esperar un retroces abans d'entrar-hi.",
        "Alcista, pero ja ha corregut bona part del seu recorregut habitual: risc de rebot en contra si s'entra ara mateix. Paciencia.",
        "Puja, si, pero l'entrada ja es cara: poc marge fins a l'objectiu i lluny del seu preu mitja del dia. Val mes esperar que reculli.",
        "Senyal d'esgotament: tot i que la tendencia es alcista, el moviment ja sembla molt avançat per avui. No es el millor punt per afegir-hi posicio.",
        "Compte amb comprar aqui dalt: la pujada ja porta molt de recorregut fet, el risc de digestio/retroces ha pujat.",
    ],
    "BAIXISTA": [
        "Tendencia baixista clara ara mateix: no es moment d'entrar-hi llarg, millor esperar que es giri.",
        "Els senyals apunten cap avall: evitar entrar-hi mentre no es reverteixi la tendencia.",
        "Baixista: si ja hi tens posicio oberta, vigila el stop; si no hi ets, no es el moment d'entrar-hi.",
        "Pressio venedora dominant ara mateix: millor quedar-se al marge fins que hi hagi un canvi clar.",
    ],
    "INDECIS": [
        "Senyals contradictoris ara mateix: ni clarament alcista ni baixista. Millor esperar mes confirmacio abans de moure's.",
        "Sense direccio clara: mal moment per prendre decisions, toca esperar que es defineixi.",
        "El mercat dubta en aquest valor ara mateix: paciencia fins que hi hagi mes claredat.",
        "Moviment lateral sense un biaix net: no es el millor moment ni per entrar ni per sortir amb convicció.",
    ],
}

# Colors per categoria (per si es vol fer servir mes enlla del biaix cru).
_COLOR_BY_CATEGORY = {
    "ALCISTA_AMB_MARGE": "verd",
    "ALCISTA_NORMAL": "verd",
    "ALCISTA_ESTIRAT": "groc",   # alcista pero amb precaucio -> ambre, no verd ple
    "BAIXISTA": "vermell",
    "INDECIS": "groc",
}


def generate_commentary(r: StockReport) -> str:
    """Retorna una frase en catala que tradueix l'estat actual de l'accio.

    Es tria a l'atzar entre diverses variants de la mateixa categoria,
    perque el text no sigui sempre identic entre actualitzacions
    consecutives (cada ~15 minuts).

    Args:
        r: StockReport ja calculat.

    Returns:
        Frase (str) llesta per mostrar a l'usuari.
    """
    category = _category(r)
    options = _PHRASES.get(category, _PHRASES["INDECIS"])
    return random.choice(options)


def get_color(r: StockReport) -> str:
    """Retorna 'verd', 'groc' o 'vermell' segons la categoria calculada.

    Es mes matisat que nomes bias.color: distingeix un alcista "estirat"
    (precaucio, groc) d'un alcista amb marge real (verd).
    """
    category = _category(r)
    return _COLOR_BY_CATEGORY.get(category, "groc")
