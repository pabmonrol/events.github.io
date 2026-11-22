import spacy
from spacy.matcher import PhraseMatcher
from typing import List

nlp = spacy.load("en_core_web_md", disable=["parser", "ner"])

matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
matcher.add("Culture", [
    nlp("theater"), nlp("exhibition"), nlp("art"), nlp("lecture"), 
    nlp("narrative"), nlp("museum"), nlp("story"), nlp("reading"), 
    nlp("life stories"), nlp("palm reading"), nlp("brain")
])
matcher.add("Music", [
    nlp("concert"), nlp("music"), nlp("choir"), nlp("band"), 
    nlp("platzkonzert"), nlp("song"), nlp("orchestra"), nlp("folk")
])
matcher.add("Government", [
    nlp("council"), nlp("meeting"), nlp("municipal"), nlp("state"), 
    nlp("fire brigade"), nlp("politics"), nlp("official"), nlp("town hall")
])
matcher.add("Leisure", [
    nlp("lunch"), nlp("party"), nlp("grill"), nlp("chill"), 
    nlp("knitting"), nlp("senior"), nlp("seniors"), nlp("café"), 
    nlp("cozy"), nlp("summer party"), nlp("summer"), nlp("holiday")
])
matcher.add("Religion", [
    nlp("pilgrimage"), nlp("church"), nlp("confirmation"), 
    nlp("corpus christi"), nlp("parish"), nlp("mass"), nlp("religious"),
    nlp("St."), nlp("saint"), nlp("virgen"), nlp("blood")
])
matcher.add("Nature", [
    nlp("neophyte"), nlp("nature"), nlp("plants"), nlp("garden"), 
    nlp("eco"), nlp("environment"), nlp("forest"), nlp("neophyte control"),
    nlp("clearance")
])
matcher.add("Sport", [
    nlp("sport"), nlp("fitness"), nlp("training"), nlp("football"), 
    nlp("soccer"), nlp("match"), nlp("workout"), nlp("brain fitness"),
    nlp("yoga")
])


TEMATICAS = {"Culture": ["🧩", "purple"],
             "Music": ["🎵", "blue"],
             "Government": ["📎", "brown"],
             "Leisure": ["🪇", "pink"],
             "Religion": ["✝️", "yellow"],
             "Nature": ["🌱", "green"],
             "Sport": ["⚽️", "red"]}

OTHER = ["Others", "#️⃣", "grey"]

CATEGORY_DOCS = [(name, nlp(name.lower())) for name in TEMATICAS]


def event_classification(title: str) -> List[str]:
    doc_evento = nlp(title.lower())
    matches = matcher(doc_evento)
    if matches:
        conteo = {}
        primera_posicion = {}
        for match_id, start, end in matches:
            categoria = nlp.vocab.strings[match_id]
            conteo[categoria] = conteo.get(categoria, 0) + 1
            primera_posicion.setdefault(categoria, start)
        categoria_ganadora = max(conteo, key=lambda c: (conteo[c], -primera_posicion[c]))
        return [categoria_ganadora] + TEMATICAS[categoria_ganadora]

    if len(doc_evento) == 0 or not doc_evento.has_vector:
        return OTHER
    
    palabras_esenciales = [
        token.text for token in doc_evento 
        if token.pos_ in ('NOUN', 'PROPN', 'VERB', 'ADJ') and not token.is_stop
    ]
    
    if not palabras_esenciales:
        return OTHER
        
    doc_filtrado = nlp(" ".join(palabras_esenciales))
    
    categoria_ganadora = "Others"
    mayor_similitud = 0.1
    
    for cat_ingles, doc_categoria in CATEGORY_DOCS:
        similitud = doc_filtrado.similarity(doc_categoria)
        
        if similitud > mayor_similitud:
            mayor_similitud = similitud
            categoria_ganadora = cat_ingles

    if categoria_ganadora == "Others":
        return OTHER
    
    return [categoria_ganadora] + TEMATICAS[categoria_ganadora]