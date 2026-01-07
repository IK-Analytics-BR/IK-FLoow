#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Builder para Evento de Cancelamento de NF-e (110111)
"""

from lxml import etree
from .evento_base import EventoBase


class EventoCancelamento(EventoBase):
    """
    Evento de Cancelamento de NF-e.
    
    Código do evento: 110111
    
    Permite cancelar uma NF-e já autorizada dentro do prazo legal.
    """
    
    def __init__(self, chave_acesso: str, protocolo: str, justificativa: str,
                 codigo_uf: int, ambiente: str = '2'):
        """
        Args:
            chave_acesso: Chave de acesso da NF-e (44 dígitos)
            protocolo: Número do protocolo de autorização da NF-e
            justificativa: Motivo do cancelamento (15-255 caracteres)
            codigo_uf: Código IBGE da UF
            ambiente: '1' = Produção, '2' = Homologação
        """
        super().__init__(chave_acesso, codigo_uf, ambiente)
        self.protocolo = ''.join(c for c in protocolo if c.isdigit())
        self.justificativa = justificativa.strip()
    
    @property
    def tipo_evento(self) -> str:
        return '110111'
    
    @property
    def descricao_evento(self) -> str:
        return 'Cancelamento'
    
    def validar(self) -> tuple:
        """Valida os dados do cancelamento"""
        valido, erros = super().validar()
        
        if not self.protocolo:
            erros.append("Protocolo de autorização é obrigatório")
        
        if len(self.justificativa) < 15:
            erros.append("Justificativa deve ter no mínimo 15 caracteres")
        
        if len(self.justificativa) > 255:
            erros.append("Justificativa deve ter no máximo 255 caracteres")
        
        return len(erros) == 0, erros
    
    def _build_det_evento(self, det_evento: etree.Element) -> None:
        """Constrói o conteúdo específico do cancelamento"""
        etree.SubElement(det_evento, 'nProt').text = self.protocolo
        etree.SubElement(det_evento, 'xJust').text = self.justificativa[:255]
