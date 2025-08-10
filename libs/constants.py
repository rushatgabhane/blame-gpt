import os

REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")

if not REPO_NAME or not REPO_OWNER:
    raise RuntimeError("REPO_NAME and REPO_OWNER environment variables must be set")

CACHE_DB_PATH = "data/cache.db"
DOCS_DB_PATH = "data/docs.db"

LABELS = {
    "DeployBlockerCash": "DeployBlockerCash",
    "DeployBlocker": "DeployBlocker",
}

USER_TAG = "@blamegpt"

ENVIRONMENT_PRODUCTION = "production"
ENVIRONMENT_DEVELOPMENT = "development"

THINKING_VERBS = [
    "Manifesting",
    "Actualizing",
    "Hustling",
    "Perusing",
    "Percolating",
    "Contemplating",
    "Sparkling",
    "Imagining",
    "Musing",
    "Determining",
    "Noodling",
    "Incubating",
    "Harmonizing",
    "Synthesizing",
    "Crystalizing",
    "Crafting",
    "Wizarding",
    "Pondering",
    "Ruminating",
    "Mulling",
    "Brooding",
    "Deliberating",
    "Conjuring",
    "Weaving",
    "Sculpting",
    "Architecting",
    "Choreographing",
    "Orchestrating",
    "Jamming",
    "Vibing",
    "Grooving",
    "Flowing",
    "Surfing",
    "Dancing",
    "Brewing",
    "Germinating",
    "Blossoming",
    "Evolving",
    "Metamorphosing",
    "Ripening",
    "Untangling",
    "Deciphering",
    "Unraveling",
    "Piecing",
    "Connecting",
    "Bridging",
    "Enchanting",
    "Spellbinding",
    "Transmuting",
    "Alchemizing",
    "Summoning",
    "Prototyping",
    "Iterating",
    "Calibrating",
    "Divining",
    "Wandering",
    "Simmering",
    "Smooshing",
    "Forging",
    "Herding",
    "Meandering",
    "Wrangling",
    "Coalescing",
    "Sussing",
    "Tinkering",
    "Envisioning",
    "Creating",
    "Bubbling",
    "Cooking",
    "Marinating",
    "Accomplishing",
    "Unfurling",
    "Forming",
    "Computing",
    "Philosophing",
    "Considering",
    "Stewing",
    "Smithing",
    "Reticulating",
    "Frolicking",
    "Finessing",
    "Sizzling",
    "Flibbertigibbeting",
]
