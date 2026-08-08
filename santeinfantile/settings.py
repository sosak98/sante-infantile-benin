# Assurez-vous d'avoir ceci (si BASE_DIR est un Path object)
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

# ... autres settings ...

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# En dev, DEBUG=True devrait permettre le service via urls.py (voir ci‑dessous)
