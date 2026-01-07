#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Classe base para construção de eventos SEFAZ
"""

from abc import ABC, abstractmethod
from datetime import datetime
from lxml import etree
from copy import deepcopy
import hashlib
import base64

# Namespaces
NS_NFE = "http://www.portalfiscal.inf.br/nfe"
NS_DS = "http://www.w3.org/2000/09/xmldsig#"


class EventoBase(ABC):
    """Classe base abstrata para eventos SEFAZ"""
    
    def __init__(self, chave_acesso: str, codigo_uf: int, ambiente: str = '2'):
        """
        Args:
            chave_acesso: Chave de acesso da NF-e (44 dígitos)
            codigo_uf: Código IBGE da UF
            ambiente: '1' = Produção, '2' = Homologação
        """
        self.chave_acesso = ''.join(c for c in chave_acesso if c.isdigit())
        self.codigo_uf = codigo_uf
        self.ambiente = ambiente
        self.cnpj = self.chave_acesso[6:20]  # CNPJ está nas posições 6-19
        self.dh_evento = datetime.now().strftime('%Y-%m-%dT%H:%M:%S-04:00')
        self.id_lote = datetime.now().strftime('%Y%m%d%H%M%S')
    
    @property
    @abstractmethod
    def tipo_evento(self) -> str:
        """Código do tipo de evento (ex: '110111' para cancelamento)"""
        pass
    
    @property
    @abstractmethod
    def descricao_evento(self) -> str:
        """Descrição do evento (ex: 'Cancelamento')"""
        pass
    
    @abstractmethod
    def _build_det_evento(self, det_evento: etree.Element) -> None:
        """Constrói o conteúdo específico do detEvento"""
        pass
    
    def validar(self) -> tuple:
        """
        Valida os dados do evento.
        Returns: (valido: bool, erros: list)
        """
        erros = []
        
        if len(self.chave_acesso) != 44:
            erros.append(f"Chave de acesso deve ter 44 dígitos (tem {len(self.chave_acesso)})")
        
        return len(erros) == 0, erros
    
    def build_xml(self, sequencia: int = 1) -> str:
        """
        Constrói o XML do evento (sem assinatura).
        
        Args:
            sequencia: Número sequencial do evento (1-20)
        
        Returns:
            XML do evento como string
        """
        # ID do evento: ID + tpEvento + chNFe + nSeqEvento (2 dígitos)
        id_evento = f"ID{self.tipo_evento}{self.chave_acesso}{sequencia:02d}"
        
        # Root do envEvento
        env_evento = etree.Element('envEvento', xmlns=NS_NFE, versao="1.00")
        
        # idLote
        etree.SubElement(env_evento, 'idLote').text = self.id_lote
        
        # evento
        evento = etree.SubElement(env_evento, 'evento', versao="1.00")
        
        # infEvento
        inf_evento = etree.SubElement(evento, 'infEvento', Id=id_evento)
        etree.SubElement(inf_evento, 'cOrgao').text = str(self.codigo_uf)
        etree.SubElement(inf_evento, 'tpAmb').text = self.ambiente
        etree.SubElement(inf_evento, 'CNPJ').text = self.cnpj
        etree.SubElement(inf_evento, 'chNFe').text = self.chave_acesso
        etree.SubElement(inf_evento, 'dhEvento').text = self.dh_evento
        etree.SubElement(inf_evento, 'tpEvento').text = self.tipo_evento
        etree.SubElement(inf_evento, 'nSeqEvento').text = str(sequencia)
        etree.SubElement(inf_evento, 'verEvento').text = "1.00"
        
        # detEvento
        det_evento = etree.SubElement(inf_evento, 'detEvento', versao="1.00")
        etree.SubElement(det_evento, 'descEvento').text = self.descricao_evento
        
        # Conteúdo específico do evento (implementado nas subclasses)
        self._build_det_evento(det_evento)
        
        return etree.tostring(env_evento, encoding='unicode')
    
    def assinar(self, xml_evento: str, cert_digital) -> str:
        """
        Assina o XML do evento.
        
        Args:
            xml_evento: XML do evento como string
            cert_digital: Instância de CertificadoDigital
        
        Returns:
            XML assinado como string
        """
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        
        # Parse do XML
        root = etree.fromstring(xml_evento.encode('utf-8'))
        
        # Encontrar o elemento evento e infEvento
        evento = root.find(".//{%s}evento" % NS_NFE)
        if evento is None:
            evento = root.find(".//evento")
        
        inf_evento = evento.find("{%s}infEvento" % NS_NFE)
        if inf_evento is None:
            inf_evento = evento.find("infEvento")
        
        # Obter o ID para referência
        id_evento = inf_evento.get("Id")
        
        # 1) Calcular DigestValue do infEvento
        inf_evento_copy = deepcopy(inf_evento)
        inf_evento_c14n = etree.tostring(inf_evento_copy, method='c14n', exclusive=False, with_comments=False)
        digest = hashlib.sha1(inf_evento_c14n).digest()
        digest_b64 = base64.b64encode(digest).decode('ascii')
        
        # 2) Criar Signature com namespace padrão
        signature = etree.SubElement(evento, '{%s}Signature' % NS_DS, nsmap={None: NS_DS})
        
        # 3) Criar SignedInfo
        signed_info = etree.SubElement(signature, 'SignedInfo')
        c14n_method = etree.SubElement(signed_info, 'CanonicalizationMethod')
        c14n_method.set('Algorithm', 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
        sig_method = etree.SubElement(signed_info, 'SignatureMethod')
        sig_method.set('Algorithm', 'http://www.w3.org/2000/09/xmldsig#rsa-sha1')
        
        reference = etree.SubElement(signed_info, 'Reference')
        reference.set('URI', f'#{id_evento}')
        
        transforms = etree.SubElement(reference, 'Transforms')
        t1 = etree.SubElement(transforms, 'Transform')
        t1.set('Algorithm', 'http://www.w3.org/2000/09/xmldsig#enveloped-signature')
        t2 = etree.SubElement(transforms, 'Transform')
        t2.set('Algorithm', 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
        
        digest_method = etree.SubElement(reference, 'DigestMethod')
        digest_method.set('Algorithm', 'http://www.w3.org/2000/09/xmldsig#sha1')
        digest_value = etree.SubElement(reference, 'DigestValue')
        digest_value.text = digest_b64
        
        # 4) Canonizar e assinar SignedInfo
        signed_info_c14n = etree.tostring(signed_info, method='c14n', exclusive=False, with_comments=False)
        
        assinatura = cert_digital.chave_privada.sign(
            signed_info_c14n,
            padding.PKCS1v15(),
            hashes.SHA1()
        )
        signature_b64 = base64.b64encode(assinatura).decode('ascii')
        
        # 5) Adicionar SignatureValue e KeyInfo
        sig_val_elem = etree.SubElement(signature, 'SignatureValue')
        sig_val_elem.text = signature_b64
        
        key_info = etree.SubElement(signature, 'KeyInfo')
        x509_data = etree.SubElement(key_info, 'X509Data')
        x509_cert = etree.SubElement(x509_data, 'X509Certificate')
        x509_cert.text = cert_digital.certificado_b64
        
        # Retornar XML assinado (sem declaração XML)
        xml_assinado = etree.tostring(root, encoding='unicode')
        if xml_assinado.startswith('<?xml'):
            xml_assinado = xml_assinado.split('?>', 1)[1].strip()
        
        return xml_assinado
