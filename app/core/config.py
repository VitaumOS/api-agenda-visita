from datetime import time
from zoneinfo import ZoneInfo

# fuso de Brasília.
FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")

# Limites locais permitidos.
INICIO_EXPEDIENTE = time(8, 0) # 8:00
FIM_EXPEDIENTE = time(19, 0) # 19:00
