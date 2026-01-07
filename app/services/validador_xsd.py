#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Validador de XML contra schemas XSD da SEFAZ

Valida:
- NF-e (modelo 55)
- Eventos (cancelamento, CC-e)
- Inutilização
"""

import os
from typing import Tuple, List
from lxml import etree


class ValidadorXSD:
    """Validador de XML contra schemas XSD oficiais da SEFAZ"""
    
    # Caminhos dos schemas (relativos à pasta do projeto)
    SCHEMAS = {
        'nfe': 'schemas/nfe/PL_010b_NT2025_002_v1.30/nfe_v4.00.xsd',
        'evento': 'schemas/nfe/PL_010b_NT2025_002_v1.30/envEvento_v1.00.xsd',
        'inutilizacao': 'schemas/nfe/PL_010b_NT2025_002_v1.30/inutNFe_v4.00.xsd',
        'lote': 'schemas/nfe/PL_010b_NT2025_002_v1.30/enviNFe_v4.00.xsd',
    }
    
    def __init__(self, base_path: str = None):
        """
        Args:
            base_path: Caminho base do projeto (onde estão os schemas)
        """
        if base_path is None:
            # Detectar caminho base automaticamente
            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_path = os.path.abspath(os.path.join(current_dir, '..', '..'))
        
        self.base_path = base_path
        self._schemas_cache = {}
    
    def _get_schema_path(self, tipo: str) -> str:
        """Retorna o caminho completo do schema"""
        if tipo not in self.SCHEMAS:
            raise ValueError(f"Tipo de schema desconhecido: {tipo}")
        
        return os.path.join(self.base_path, self.SCHEMAS[tipo])
    
    def _load_schema(self, tipo: str) -> etree.XMLSchema:
        """Carrega e cacheia o schema XSD"""
        if tipo not in self._schemas_cache:
            schema_path = self._get_schema_path(tipo)
            
            if not os.path.exists(schema_path):
                raise FileNotFoundError(f"Schema XSD não encontrado: {schema_path}")
            
            with open(schema_path, 'rb') as f:
                schema_doc = etree.parse(f)
                self._schemas_cache[tipo] = etree.XMLSchema(schema_doc)
        
        return self._schemas_cache[tipo]
    
    def validar_nfe(self, xml_string: str) -> Tuple[bool, List[str]]:
        """
        Valida XML de NF-e contra o schema oficial.
        
        Args:
            xml_string: XML da NF-e como string
        
        Returns:
            Tuple (valido: bool, erros: list)
        """
        return self._validar(xml_string, 'nfe')
    
    def validar_evento(self, xml_string: str) -> Tuple[bool, List[str]]:
        """
        Valida XML de evento (cancelamento, CC-e) contra o schema oficial.
        
        Args:
            xml_string: XML do evento como string
        
        Returns:
            Tuple (valido: bool, erros: list)
        """
        return self._validar(xml_string, 'evento')
    
    def validar_inutilizacao(self, xml_string: str) -> Tuple[bool, List[str]]:
        """
        Valida XML de inutilização contra o schema oficial.
        
        Args:
            xml_string: XML de inutilização como string
        
        Returns:
            Tuple (valido: bool, erros: list)
        """
        return self._validar(xml_string, 'inutilizacao')
    
    def validar_lote(self, xml_string: str) -> Tuple[bool, List[str]]:
        """
        Valida XML de lote (enviNFe) contra o schema oficial.
        
        Args:
            xml_string: XML do lote como string
        
        Returns:
            Tuple (valido: bool, erros: list)
        """
        return self._validar(xml_string, 'lote')
    
    def _validar(self, xml_string: str, tipo: str) -> Tuple[bool, List[str]]:
        """
        Valida XML contra o schema especificado.
        
        Args:
            xml_string: XML como string
            tipo: Tipo do schema ('nfe', 'evento', 'inutilizacao', 'lote')
        
        Returns:
            Tuple (valido: bool, erros: list)
        """
        try:
            schema = self._load_schema(tipo)
            xml_doc = etree.fromstring(xml_string.encode('utf-8'))
            
            is_valid = schema.validate(xml_doc)
            
            if is_valid:
                return True, []
            else:
                erros = [str(e) for e in schema.error_log]
                return False, erros
                
        except FileNotFoundError as e:
            return False, [str(e)]
        except etree.XMLSyntaxError as e:
            return False, [f"XML inválido: {str(e)}"]
        except Exception as e:
            return False, [f"Erro na validação: {str(e)}"]
    
    def schema_existe(self, tipo: str) -> bool:
        """Verifica se o schema existe no sistema de arquivos"""
        try:
            schema_path = self._get_schema_path(tipo)
            return os.path.exists(schema_path)
        except ValueError:
            return False
    
    def listar_schemas_disponiveis(self) -> dict:
        """Lista os schemas disponíveis e seu status"""
        status = {}
        for tipo in self.SCHEMAS:
            status[tipo] = {
                'path': self.SCHEMAS[tipo],
                'existe': self.schema_existe(tipo)
            }
        return status


# Instância global para uso conveniente
_validador = None

def get_validador() -> ValidadorXSD:
    """Retorna instância singleton do validador"""
    global _validador
    if _validador is None:
        _validador = ValidadorXSD()
    return _validador


def validar_nfe(xml_string: str) -> Tuple[bool, List[str]]:
    """Função de conveniência para validar NF-e"""
    return get_validador().validar_nfe(xml_string)


def validar_evento(xml_string: str) -> Tuple[bool, List[str]]:
    """Função de conveniência para validar evento"""
    return get_validador().validar_evento(xml_string)


def validar_inutilizacao(xml_string: str) -> Tuple[bool, List[str]]:
    """Função de conveniência para validar inutilização"""
    return get_validador().validar_inutilizacao(xml_string)


# Teste quando executado diretamente
if __name__ == '__main__':
    validador = ValidadorXSD()
    print("Schemas disponíveis:")
    for tipo, info in validador.listar_schemas_disponiveis().items():
        status = "✅" if info['existe'] else "❌"
        print(f"  {status} {tipo}: {info['path']}")
