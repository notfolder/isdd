"""Sample species that are loaded the first time the database is created.

The values are for demonstration. Conservation status, lifespan and mass
must be checked against an authoritative source before real use.
"""


def sample_species_data():
    """Return the list of 12 sample species as dictionaries of column values."""
    return [
        _species("Panthera leo", "Lion", "Mammalia", "Felidae", "Grassland", "Carnivore", "VU", 14, 190.0,
                 "Large social cat of the African savanna."),
        _species("Macaca fuscata", "Japanese macaque", "Mammalia", "Cercopithecidae", "Forest", "Omnivore", "LC", 20, 12.0,
                 "Monkey native to Japan that lives in troops in forests and mountains."),
        _species("Ailuropoda melanoleuca", "Giant panda", "Mammalia", "Ursidae", "Forest", "Herbivore", "VU", 20, 100.0,
                 "Bear of south-central China that feeds mainly on bamboo."),
        _species("Elephas maximus", "Asian elephant", "Mammalia", "Elephantidae", "Forest", "Herbivore", "EN", 60, 4000.0,
                 "Largest living land animal in Asia, found in forests and grasslands."),
        _species("Balaenoptera musculus", "Blue whale", "Mammalia", "Balaenopteridae", "Marine", "Carnivore", "EN", 80, 150000.0,
                 "The largest animal known to have lived, feeding mainly on krill."),
        _species("Passer domesticus", "House sparrow", "Aves", "Passeridae", "Terrestrial", "Omnivore", "LC", 3, 0.03,
                 "Small sparrow that lives close to people in towns and villages."),
        _species("Horornis diphone", "Japanese bush warbler", "Aves", "Cettiidae", "Forest", "Insectivore", "LC", 4, 0.02,
                 "Small songbird of forests and bushes, known for its loud song."),
        _species("Aptenodytes forsteri", "Emperor penguin", "Aves", "Spheniscidae", "Marine", "Carnivore", "NT", 20, 30.0,
                 "Largest penguin, breeding on Antarctic sea ice."),
        _species("Cyprinus carpio", "Common carp", "Actinopterygii", "Cyprinidae", "Freshwater", "Omnivore", "LC", 20, 10.0,
                 "Freshwater fish widely kept in ponds and rivers."),
        _species("Andrias japonicus", "Japanese giant salamander", "Amphibia", "Hynobiidae", "Freshwater", "Carnivore", "CR", 50, 25.0,
                 "Large aquatic salamander that lives in cold mountain streams."),
        _species("Chelonia mydas", "Green sea turtle", "Reptilia", "Cheloniidae", "Marine", "Herbivore", "EN", 80, 160.0,
                 "Sea turtle whose adults feed mainly on sea grass and algae."),
        _species("Coccinella septempunctata", "Seven-spot ladybird", "Insecta", "Coccinellidae", "Grassland", "Insectivore", "LC", None, None,
                 "Small beetle that feeds on aphids in grasslands and gardens."),
    ]


def _species(scientific_name, common_name, class_name, family, habitat, diet, status, lifespan, mass, description):
    return {
        "scientific_name": scientific_name,
        "common_name": common_name,
        "class_name": class_name,
        "family": family,
        "habitat": habitat,
        "diet": diet,
        "conservation_status": status,
        "average_lifespan_years": lifespan,
        "average_adult_mass_kg": mass,
        "description": description,
    }
