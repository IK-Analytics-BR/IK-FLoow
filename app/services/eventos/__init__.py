"""
Módulo de Eventos SEFAZ
- Cancelamento (110111)
- Carta de Correção (110110)
- Inutilização
"""

from .evento_base import EventoBase
from .evento_cancelamento import EventoCancelamento
from .evento_cce import EventoCartaCorrecao
from .evento_inutilizacao import EventoInutilizacao

__all__ = [
    'EventoBase',
    'EventoCancelamento',
    'EventoCartaCorrecao',
    'EventoInutilizacao'
]
