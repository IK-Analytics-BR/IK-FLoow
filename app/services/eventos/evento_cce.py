#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Builder para Evento de Carta de Correção Eletrônica - CC-e (110110)
"""

from lxml import etree
from .evento_base import EventoBase


class EventoCartaCorrecao(EventoBase):
    """
    Evento de Carta de Correção Eletrônica (CC-e).
    
    Código do evento: 110110
    
    Permite corrigir informações da NF-e sem cancelá-la.
    
    ⚠️ NÃO pode corrigir:
    - Valores (base de cálculo, alíquotas, preços)
    - Quantidades
    - Dados cadastrais do emitente/destinatário
    - Data de emissão ou saída
    """
    
    # Condição de uso obrigatória (texto legal)
    CONDICAO_USO = (
        "A Carta de Correcao e disciplinada pelo paragrafo 1o-A do art. 7o do "
        "Convenio S/N, de 15 de dezembro de 1970 e pode ser utilizada para "
        "regularizacao de erro ocorrido na emissao de documento fiscal, desde que "
        "o erro nao esteja relacionado com: I - as variaveis que determinam o valor "
        "do imposto tais como: base de calculo, aliquota, diferenca de preco, "
        "quantidade, valor da operacao ou da prestacao; II - a correcao de dados "
        "cadastrais que implique mudanca do remetente ou do destinatario; "
        "III - a data de emissao ou de saida."
    )
    
    def __init__(self, chave_acesso: str, correcao: str,
                 codigo_uf: int, ambiente: str = '2'):
        """
        Args:
            chave_acesso: Chave de acesso da NF-e (44 dígitos)
            correcao: Texto da correção (15-1000 caracteres)
            codigo_uf: Código IBGE da UF
            ambiente: '1' = Produção, '2' = Homologação
        """
        super().__init__(chave_acesso, codigo_uf, ambiente)
        self.correcao = correcao.strip()
    
    @property
    def tipo_evento(self) -> str:
        return '110110'
    
    @property
    def descricao_evento(self) -> str:
        return 'Carta de Correcao'
    
    def validar(self) -> tuple:
        """Valida os dados da carta de correção"""
        valido, erros = super().validar()
        
        if len(self.correcao) < 15:
            erros.append("Texto da correção deve ter no mínimo 15 caracteres")
        
        if len(self.correcao) > 1000:
            erros.append("Texto da correção deve ter no máximo 1000 caracteres")
        
        return len(erros) == 0, erros
    
    def _build_det_evento(self, det_evento: etree.Element) -> None:
        """Constrói o conteúdo específico da carta de correção"""
        # Escapar caracteres especiais
        correcao_escaped = (self.correcao
                           .replace('&', '&amp;')
                           .replace('<', '&lt;')
                           .replace('>', '&gt;'))
        
        etree.SubElement(det_evento, 'xCorrecao').text = correcao_escaped[:1000]
        etree.SubElement(det_evento, 'xCondUso').text = self.CONDICAO_USO
