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


CATEGORY_STYLES = {"Culture": ["🧩", "purple"],
             "Music": ["🎵", "blue"],
             "Government": ["📎", "brown"],
             "Leisure": ["🪇", "pink"],
             "Religion": ["✝️", "yellow"],
             "Nature": ["🌱", "green"],
             "Sport": ["⚽️", "red"]}

OTHER_STYLE = ["Others", "#️⃣", "grey"]

AVOID_CATEGORIES = {"Government", "Religion"}

CATEGORY_DOCS = [(name, nlp(name.lower())) for name in TEMATICAS]


def event_classification(title: str) -> List[str]:
    event_doc = nlp(title.lower())
    matches = matcher(event_doc)
    if matches:
        conteo = {}
        primera_posicion = {}
        for match_id, start, end in matches:
            categoria = nlp.vocab.strings[match_id]
            conteo[categoria] = conteo.get(categoria, 0) + 1
            primera_posicion.setdefault(categoria, start)
        categoria_ganadora = max(conteo, key=lambda c: (conteo[c], -primera_posicion[c]))
        return [categoria_ganadora] + TEMATICAS[categoria_ganadora]

    if len(event_doc) == 0 or not event_doc.has_vector:
        return OTHER_STYLE

    keywords = [
        token.text for token in event_doc
        if token.pos_ in ("NOUN", "PROPN", "VERB", "ADJ") and not token.is_stop
    ]

    if not keywords:
        return OTHER_STYLE

    filtered_doc = nlp(" ".join(keywords))

    winner = "Others"
    best_similarity = 0.1

    for category_name, category_doc in CATEGORY_DOCS:
        similarity = filtered_doc.similarity(category_doc)
        if similarity > best_similarity:
            best_similarity = similarity
            winner = category_name

    if winner == "Others":
        return OTHER_STYLE

    return [winner] + CATEGORY_STYLES[winner]