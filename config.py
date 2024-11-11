from os import getenv

from dotenv import load_dotenv

load_dotenv()

API_ID = "20262586"
# -------------------------------------------------------------
API_HASH = "7c331e3751b606fdffe1fad18f0065b6"
# --------------------------------------------------------------
BOT_TOKEN = getenv("BOT_TOKEN", None)
MONGO_URL = getenv("MONGO_URL", None)
OWNER_ID = int(getenv("OWNER_ID", "6323559178"))
SUPPORT_GRP = "Poshtibaninetroplusbot"
UPDATE_CHNL = "Fortis_dastorat_music"
OWNER_USERNAME = "amirali_motlbi"
