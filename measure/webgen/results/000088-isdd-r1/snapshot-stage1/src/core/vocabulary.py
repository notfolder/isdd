"""生物種の選択肢（分類群・生息環境・食性・保全状況）の定義。

画面の選択欄と入力チェックと、保存される値は、ここの文字列どおりに一致させる。
"""

TAXONOMIC_CLASSES = ("Mammals", "Birds", "Reptiles", "Amphibians", "Fish", "Insects")

HABITATS = (
    "Forest",
    "Grassland",
    "Wetland",
    "Freshwater",
    "Marine",
    "Desert",
    "Mountain",
    "Urban",
)

DIETS = ("Herbivore", "Carnivore", "Omnivore", "Insectivore")

CONSERVATION_STATUSES = (
    "Least Concern",
    "Near Threatened",
    "Vulnerable",
    "Endangered",
    "Critically Endangered",
    "Data Deficient",
)
