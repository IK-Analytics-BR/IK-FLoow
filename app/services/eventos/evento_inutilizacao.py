#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Builder para Inutilização de Numeração de NF-e
"""

from datetime import datetime
from lxml import etree
from copy import deepcopy
import hashlib
import base64

# Namespaces
NS_NFE = "http://www.portalfiscal.inf.br/nfe"
NS_DS = "http://www.w3.org/2000/09/xmldsig#"


class EventoInutilizacao:
    """
    Inutilização de Numeração de NF-e.
    
    Permite inutilizar números de NF-e que foram pulados na sequência
    e não serão mais utilizados.
    
    Exemplo: Se emitiu NF-e 100 e depois 105, deve inutilizar 101-104.
    """
    
    def __init__(self, cnpj: str, serie: int, numero_inicial: int, numero_final: int,
                 justificativa: str, codigo_uf: int, ano: int = None, ambiente: str = '2'):
        """
        Args:
            cnpj: CNPJ do emitente (14 dígitos)
            serie: Série da NF-e
            numero_inicial: Número inicial da faixa
            numero_final: Número final da faixa
            justificativa: Motivo da inutilização (15-255 caracteres)
            codigo_uf: Código IBGE da UF
            ano: Ano da inutilização (2 dígitos, ex: 25 para 2025)
            ambiente: '1' = Produção, '2' = Homologação
        """
        self.cnpj = ''.join(c for c in cnpj if c.isdigit()).zfill(14)
        self.serie = serie
        self.numero_inicial = numero_inicial
        self.numero_final = numero_final
        self.justificativa = justificativa.strip()
        self.codigo_uf = codigo_uf
        self.ano = ano or int(datetime.now().strftime('%y'))
        self.ambiente = ambiente
        
        # ID: ID + cUF + ano + CNPJ + mod + serie + nNFIni + nNFFin
        self.id = (f"ID{codigo_uf}{self.ano:02d}{self.cnpj}55"
                   f"{serie:03d}{numero_inicial:09d}{numero_final:09d}")
    
    def validar(self) -> tuple:
        """Valida os dados da inutilização"""
        erros = []
        
        if len(self.cnpj) != 14:
            erros.append("CNPJ deve ter 14 dígitos")
        
        if self.numero_inicial <= 0:
            erros.append("Número inicial deve ser maior que zero")
        
        if self.numero_final < self.numero_inicial:
            erros.append("Número final deve ser maior ou igual ao inicial")
        
        if len(self.justificativa) < 15:
            erros.append("Justificativa deve ter no mínimo 15 caracteres")
        
        if len(self.justificativa) > 255:
            erros.append("Justificativa deve ter no máximo 255 caracteres")
        
        return len(erros) == 0, erros
    
    def build_xml(self) -> str:
        """
        Constrói o XML de inutilização (sem assinatura).
        
        Returns:
            XML como string
        """
        # Root do inutNFe
        inut_nfe = etree.Element('inutNFe', xmlns=NS_NFE, versao="4.00")
        
        # infInut
        inf_inut = etree.SubElement(inut_nfe, 'infInut', Id=self.id)
        etree.SubElement(inf_inut, 'tpAmb').text = self.ambiente
        etree.SubElement(inf_inut, 'xServ').text = 'INUTILIZAR'
        etree.SubElement(inf_inut, 'cUF').text = str(self.codigo_uf)
        etree.SubElement(inf_inut, 'ano').text = f"{self.ano:02d}"
        etree.SubElement(inf_inut, 'CNPJ').text = self.cnpj
        etree.SubElement(inf_inut, 'mod').text = '55'  # NF-e modelo 55
        etree.SubElement(inf_inut, 'serie').text = str(self.serie)
        etree.SubElement(inf_inut, 'nNFIni').text = str(self.numero_inicial)
        etree.SubElement(inf_inut, 'nNFFin').text = str(self.numero_final)
        etree.SubElement(inf_inut, 'xJust').text = self.justificativa[:255]
        
        return etree.tostring(inut_nfe, encoding='unicode')
    
    def assinar(self, xml_inut: str, cert_digital) -> str:
        """
        Assina o XML de inutilização.
        
        Args:
            xml_inut: XML de inutilização como string
            cert_digital: Instância de CertificadoDigital
        
        Returns:
            XML assinado como string
        """
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        
        # Parse do XML
        root = etree.fromstring(xml_inut.encode('utf-8'))
        
        # Encontrar infInut
        inf_inut = root.find("{%s}infInut" % NS_NFE)
        if inf_inut is None:
            inf_inut = root.find("infInut")
        
        # Obter o ID para referência
        id_inut = inf_inut.get("Id")
        
        # 1) Calcular DigestValue do infInut
        inf_inut_copy = deepcopy(inf_inut)
        inf_inut_c14n = etree.tostring(inf_inut_copy, method='c14n', exclusive=False, with_comments=False)
        digest = hashlib.sha1(inf_inut_c14n).digest()
        digest_b64 = base64.b64encode(digest).decode('ascii')
        
        # 2) Criar Signature com namespace padrão
        signature = etree.SubElement(root, '{%s}Signature' % NS_DS, nsmap={None: NS_DS})
        
        # 3) Criar SignedInfo
        signed_info = etree.SubElement(signature, 'SignedInfo')
        c14n_method = etree.SubElement(signed_info, 'CanonicalizationMethod')
        c14n_method.set('Algorithm', 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
        sig_method = etree.SubElement(signed_info, 'SignatureMethod')
        sig_method.set('Algorithm', 'http://www.w3.org/2000/09/xmldsig#rsa-sha1')
        
        reference = etree.SubElement(signed_info, 'Reference')
        reference.set('URI', f'#{id_inut}')
        
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
