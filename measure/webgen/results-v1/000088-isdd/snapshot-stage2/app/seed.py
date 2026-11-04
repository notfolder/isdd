"""表が空のときのサンプルの生物種の投入。"""

from __future__ import annotations

from typing import Any

# (学名, 和名, 界, 綱, 生息環境, 食性, 保全状況, 平均体長 cm, 説明)
SAMPLE_SPECIES: tuple[tuple[Any, ...], ...] = (
    ("Panthera leo", "Lion", "Animalia", "Mammalia", "Terrestrial", "Carnivore", "VU", "190.0",
     "Large social cat that lives in groups called prides."),
    ("Panthera tigris", "Tiger", "Animalia", "Mammalia", "Terrestrial", "Carnivore", "EN", "300.0",
     "The largest wild cat, with distinctive dark stripes."),
    ("Gorilla gorilla gorilla", "Western lowland gorilla", "Animalia", "Mammalia", "Terrestrial", "Herbivore",
     "CR", "170.0", "Great ape of the forests of west-central Africa."),
    ("Ailuropoda melanoleuca", "Giant panda", "Animalia", "Mammalia", "Terrestrial", "Herbivore", "VU", "150.0",
     "Bear with black and white fur that feeds mainly on bamboo."),
    ("Equus ferus przewalskii", "Przewalski's horse", "Animalia", "Mammalia", "Terrestrial", "Herbivore", "EW",
     "230.0", "Wild horse once extinct in the wild and since reintroduced."),
    ("Raphus cucullatus", "Dodo", "Animalia", "Aves", "Terrestrial", "Omnivore", "EX", "70.0",
     "Flightless bird of Mauritius that became extinct in the 17th century."),
    ("Lutra lutra", "Eurasian otter", "Animalia", "Mammalia", "Freshwater", "Carnivore", "NT", "80.0",
     "Semi-aquatic mammal that hunts fish in rivers and lakes."),
    ("Salmo salar", "Atlantic salmon", "Animalia", "Actinopterygii", "Mixed", "Carnivore", "LC", "150.0",
     "Fish that spends its adult life at sea and returns to rivers to spawn."),
    ("Mesoplodon perrini", "Perrin's beaked whale", "Animalia", "Mammalia", "Marine", "Carnivore", "DD", "500.0",
     "Deep-diving whale that is rarely seen, so its status is hard to assess."),
    ("Quercus robur", "English oak", "Plantae", "Magnoliopsida", "Terrestrial", "Other", "LC", "2500.0",
     "Deciduous tree native to Europe and western Asia."),
    ("Escherichia coli", "Escherichia coli", "Bacteria", None, "Mixed", "Omnivore", "LC", None,
     "Common bacterium that lives in the intestines of warm-blooded animals."),
    ("Amanita muscaria", "Fly agaric", "Fungi", "Agaricomycetes", "Terrestrial", "Other", "LC", None,
     "Mushroom with a red cap and white spots, found under birch and pine trees."),
)

_FIELD_ORDER = (
    "scientific_name", "common_name", "kingdom", "taxonomic_class", "habitat", "diet",
    "conservation_status", "average_length_cm", "description",
)


def seed_sample_species_if_empty(repository: Any) -> int:
    """生物種の表が空なら、サンプルを入れて投入件数を返す。1 件でもあれば何もしない。"""
    if repository.search():
        return 0
    count = 0
    for sample in SAMPLE_SPECIES:
        values = {name: "" if value is None else str(value) for name, value in zip(_FIELD_ORDER, sample)}
        repository.insert(values)
        count += 1
    return count
