"""生物種の選択肢と入力の上限。"""

KINGDOMS: tuple[str, ...] = ("Animalia", "Plantae", "Fungi", "Protista", "Bacteria", "Archaea")
HABITATS: tuple[str, ...] = ("Terrestrial", "Freshwater", "Marine", "Mixed")
DIETS: tuple[str, ...] = ("Herbivore", "Carnivore", "Omnivore", "Other")

# 保全状況は IUCN の略号を保存し、画面では表示名を出す。
CONSERVATION_STATUSES: dict[str, str] = {
    "LC": "Least Concern (LC)",
    "NT": "Near Threatened (NT)",
    "VU": "Vulnerable (VU)",
    "EN": "Endangered (EN)",
    "CR": "Critically Endangered (CR)",
    "EW": "Extinct in the Wild (EW)",
    "EX": "Extinct (EX)",
    "DD": "Data Deficient (DD)",
}

SCIENTIFIC_NAME_MAX_LENGTH = 100
COMMON_NAME_MAX_LENGTH = 100
CLASS_MAX_LENGTH = 60
DESCRIPTION_MAX_LENGTH = 2000
AVERAGE_LENGTH_MAX_CM = 100000
