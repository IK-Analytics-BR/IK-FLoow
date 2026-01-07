# -*- coding: utf-8 -*-
"""
Módulo de Gerenciamento de Certificado Digital A1
Responsável por:
- Carregar certificado do banco de dados
- Assinar XMLs de NF-e
- Validar certificado
- Extrair informações do certificado
"""

import base64
import tempfile
import os
import sys
import warnings
from copy import deepcopy
from datetime import datetime, timezone
from typing import Optional, Dict, Tuple

# criptografia
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs12

# para assinatura
import hashlib
from cryptography.hazmat.primitives.asymmetric import padding

# xml
from lxml import etree

# evitar warnings SHA1 (algumas SEFAZs ainda aceitam/registram)
warnings.filterwarnings('ignore', message='.*SHA1.*')

# Adicionar o diretório raiz ao path (mesma lógica do seu projeto)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from app.auto_config import DB_CONFIG
except ImportError:
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': 'aritana',
        'database': 'supply_chain_system'
    }

import mysql.connector
from app.database import get_db


class CertificadoDigital:
    """
    Gerenciador de Certificado Digital A1 (PKCS#12)
    Usa pkcs12.load_key_and_certificates para extrair private key e certificado.
    """

    def __init__(self, empresa_id: int):
        self.empresa_id = empresa_id
        self.certificado_pfx: Optional[bytes] = None
        self.senha: Optional[bytes] = None
        self.private_key = None
        self.certificate = None
        self.chain = []
        # caminhos temporários gerados por salvar_pem_temporario
        self._tmp_cert_path: Optional[str] = None
        self._tmp_key_path: Optional[str] = None

    def carregar_do_banco(self) -> bool:
        """
        Carrega certificado (PFX) do banco de dados.
        Espera colunas:
            certificado_base64, senha_criptografada, validade, cnpj_titular
        Retorna True se carregado com sucesso.
        """
        try:
            db = get_db()
            query = """
                SELECT 
                    certificado_base64,
                    senha_criptografada,
                    validade,
                    cnpj_titular
                FROM certificados_digitais
                WHERE empresa_id = %s
                AND ativo = TRUE
                AND validade > NOW()
                ORDER BY created_at DESC
                LIMIT 1
            """
            resultado = db.execute_query(query, (self.empresa_id,))
            if hasattr(resultado, 'fetchone'):
                resultado = resultado.fetchone()
            else:
                resultado = resultado[0] if resultado else None

            if not resultado:
                print(f"[ERRO] Nenhum certificado válido encontrado para empresa {self.empresa_id}")
                return False

            if not resultado.get('certificado_base64'):
                print(f"[ERRO] Registro encontrado sem certificado para empresa {self.empresa_id}")
                return False

            # Decodificar PFX (base64)
            try:
                self.certificado_pfx = base64.b64decode(resultado['certificado_base64'])
            except Exception as e:
                print(f"[ERRO] Falha ao decodificar certificado_base64: {e}")
                return False

            # Senha (a tabela chama de senha_criptografada; por enquanto assumimos texto)
            senha_raw = resultado.get('senha_criptografada') or ''
            if isinstance(senha_raw, bytes):
                self.senha = senha_raw
            else:
                # manter como bytes (se vazio -> None)
                self.senha = senha_raw.encode('utf-8') if senha_raw else None

            # Carregar chaves do PFX
            try:
                self._carregar_chaves()
            except Exception as e:
                print(f"[ERRO] Falha ao carregar chaves do PFX: {e}")
                return False

            # Salvar atributos para acesso externo
            self.cnpj_titular = resultado.get('cnpj_titular', 'N/A')
            self.validade = resultado.get('validade', 'N/A')
            
            # Logs informativos
            print(f"[OK] Certificado carregado para empresa {self.empresa_id} (CNPJ: {self.cnpj_titular}, Validade: {self.validade})")
            return True

        except Exception as e:
            print(f"[ERRO] Erro ao carregar certificado do banco: {e}")
            return False

    def _carregar_chaves(self):
        """
        Extrai private_key, certificate e chain do PFX carregado.
        Lança Exception em caso de erro.
        """
        if not self.certificado_pfx:
            raise Exception("PFX não carregado")

        # pkcs12.load_key_and_certificates espera senha como bytes ou None
        try:
            private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                self.certificado_pfx,
                self.senha,
                backend=default_backend()
            )
        except TypeError:
            # alguns backends aceitam apenas senha str; converter se necessário
            try:
                pwd = self.senha.decode('utf-8') if self.senha else None
                private_key, certificate, additional_certs = pkcs12.load_key_and_certificates(
                    self.certificado_pfx,
                    pwd,
                    backend=default_backend()
                )
            except Exception as ex:
                raise Exception(f"Erro ao abrir PFX (tentativa com str): {ex}")
        except Exception as e:
            raise Exception(f"Erro ao abrir PFX: {e}")

        if private_key is None or certificate is None:
            raise Exception("PFX não contém chave privada ou certificado")

        self.private_key = private_key
        self.certificate = certificate
        self.chain = list(additional_certs) if additional_certs else []

    def assinar_xml(self, xml_string: str) -> str:
        """
        Assina um XML de NF-e (infNFe) com a chave privada do certificado.
        Implementação compatível com NF-e 4.00:
          - Canonicalização Exclusive (C14N) com InclusiveNamespaces (prefixList 'nfe')
          - Digest SHA-256
          - SignatureMethod RSA-SHA256
          - Insere <ds:Signature> DENTRO do elemento infNFe
        Retorna XML assinado (string).
        Lança Exception em caso de erro.
        """
        if self.private_key is None or self.certificate is None:
            raise Exception("Chave privada ou certificado não carregados. Rode carregar_do_banco().")

        try:
            # Parse do XML - preservar CDATA (importante para qrCode)
            parser = etree.XMLParser(remove_blank_text=True, strip_cdata=False)
            root = etree.fromstring(xml_string.encode('utf-8'), parser=parser)

            # localizar infNFe ou infEvento (considerando namespace padrão nfe)
            nsmap = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            # Tentar infNFe primeiro (para NF-e/NFC-e)
            infnfe = root.find('.//nfe:infNFe', namespaces=nsmap)
            if infnfe is None:
                infnfe = root.find('.//{http://www.portalfiscal.inf.br/nfe}infNFe')
            
            # Se não encontrar, tentar infEvento (para eventos como cancelamento)
            if infnfe is None:
                print(f"[ASSINATURA] Buscando infEvento...")
                infnfe = root.find('.//nfe:infEvento', namespaces=nsmap)
            if infnfe is None:
                infnfe = root.find('.//{http://www.portalfiscal.inf.br/nfe}infEvento')
            if infnfe is None:
                infnfe = root.find('.//infEvento')
            
            # Se não encontrar, tentar infInut (para inutilização)
            if infnfe is None:
                print(f"[ASSINATURA] Buscando infInut...")
                infnfe = root.find('.//nfe:infInut', namespaces=nsmap)
            if infnfe is None:
                infnfe = root.find('.//{http://www.portalfiscal.inf.br/nfe}infInut')
            if infnfe is None:
                infnfe = root.find('.//infInut')
            
            if infnfe is None:
                print(f"[ASSINATURA] Root tag: {root.tag}")
                print(f"[ASSINATURA] Root children: {[c.tag for c in root]}")
                raise Exception("Elemento infNFe, infEvento ou infInut não encontrado no XML")

            nfe_id = infnfe.get('Id')
            if not nfe_id:
                raise Exception("Atributo Id não encontrado em infNFe/infEvento")

            # 1) Calcular DigestValue do infNFe
            # IMPORTANTE: Usar deepcopy para evitar xmlns="" nos elementos netos
            infnfe_copy = deepcopy(infnfe)
            infnfe_c14n = etree.tostring(infnfe_copy, method='c14n', exclusive=False, with_comments=False)
            # SHA-1 para NFC-e (igual emissão normal que funciona)
            digest_b64 = base64.b64encode(hashlib.sha1(infnfe_c14n).digest()).decode('ascii')

            # 2) Criar Signature e SignedInfo
            # IMPORTANTE: Usar namespace padrão (sem prefixo ds:) como no XML de referência da SEFAZ
            # Isso evita que o SignedInfo herde o namespace NFe do pai
            dsig_ns = "http://www.w3.org/2000/09/xmldsig#"
            nfe_root = infnfe.getparent()
            
            # Remover assinatura existente se houver
            existing_sig = nfe_root.find('{%s}Signature' % dsig_ns)
            if existing_sig is not None:
                nfe_root.remove(existing_sig)
            
            # Criar Signature com namespace padrão = xmldsig (SEM prefixo ds:)
            # nsmap={None: dsig_ns} define o namespace padrão como xmldsig
            signature = etree.SubElement(nfe_root, '{%s}Signature' % dsig_ns, nsmap={None: dsig_ns})
            
            # IMPORTANTE: Criar elementos filhos SEM namespace explícito no tag
            # Eles herdarão o namespace xmldsig do Signature
            # Se usarmos {ns}tag, o lxml adiciona xmlns="" durante C14N
            signed_info = etree.SubElement(signature, 'SignedInfo')
            c14n_method = etree.SubElement(signed_info, 'CanonicalizationMethod')
            c14n_method.set('Algorithm', 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
            sig_method = etree.SubElement(signed_info, 'SignatureMethod')
            # SHA-1 para NFC-e (igual emissão normal que funciona)
            sig_method.set('Algorithm', 'http://www.w3.org/2000/09/xmldsig#rsa-sha1')
            
            reference = etree.SubElement(signed_info, 'Reference')
            reference.set('URI', f'#{nfe_id}')
            transforms = etree.SubElement(reference, 'Transforms')
            t_env = etree.SubElement(transforms, 'Transform')
            t_env.set('Algorithm', 'http://www.w3.org/2000/09/xmldsig#enveloped-signature')
            t_c14n = etree.SubElement(transforms, 'Transform')
            t_c14n.set('Algorithm', 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
            digest_method = etree.SubElement(reference, 'DigestMethod')
            # SHA-1 para NFC-e (igual emissão normal que funciona)
            digest_method.set('Algorithm', 'http://www.w3.org/2000/09/xmldsig#sha1')
            digest_value_elem = etree.SubElement(reference, 'DigestValue')
            digest_value_elem.text = digest_b64

            # 3) Canonizar SignedInfo
            # Agora o SignedInfo terá namespace xmldsig (não NFe) porque Signature define o namespace padrão
            signed_info_c14n = etree.tostring(signed_info, method='c14n', exclusive=False, with_comments=False)

            # 4) Assinar o SignedInfo canonizado com SHA-1
            signature_bytes = self.private_key.sign(
                signed_info_c14n,
                padding.PKCS1v15(),
                hashes.SHA1()  # SHA-1 para NFC-e (igual emissão normal que funciona)
            )
            signature_b64 = base64.b64encode(signature_bytes).decode('ascii')

            # 5) Adicionar SignatureValue e KeyInfo (também sem namespace explícito)
            sig_val_elem = etree.SubElement(signature, 'SignatureValue')
            sig_val_elem.text = signature_b64
            
            key_info = etree.SubElement(signature, 'KeyInfo')
            x509_data = etree.SubElement(key_info, 'X509Data')
            x509_cert = etree.SubElement(x509_data, 'X509Certificate')
            cert_pem = self.certificate.public_bytes(encoding=serialization.Encoding.PEM).decode('ascii')
            x509_cert.text = cert_pem.replace('-----BEGIN CERTIFICATE-----', '').replace('-----END CERTIFICATE-----', '').replace('\n', '')

            # 7) Serializar
            xml_assinado_bytes = etree.tostring(root, encoding='UTF-8', xml_declaration=True, pretty_print=False)
            xml_result = xml_assinado_bytes.decode('utf-8')
            
            # CORREÇÃO CRÍTICA: Remover espaços dentro do CDATA que lxml adiciona
            # De: <![CDATA[ http://... ]]>  Para: <![CDATA[http://...]]>
            import re
            xml_result = re.sub(r'<!\[CDATA\[\s+', '<![CDATA[', xml_result)
            xml_result = re.sub(r'\s+\]\]>', ']]>', xml_result)
            
            return xml_result

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"Falha na assinatura do XML: {e}")

    def validar_certificado(self) -> Dict[str, any]:
        """
        Retorna informações do certificado (titular, emissor, validade, dias restantes).
        """
        if self.certificate is None:
            raise Exception("Certificado não carregado")

        try:
            subj = self.certificate.subject
            issuer = self.certificate.issuer

            # Extrair CNPJ do subject - normalmente está em serialNumber ou OID específico
            cnpj = None
            for attr in subj:
                try:
                    name = attr.oid._name
                except Exception:
                    name = None
                if name in ('serialNumber', 'SERIALNUMBER'):
                    cnpj = attr.value
                    break

            # Datas (usar timezone-aware se disponível)
            not_before = self.certificate.not_valid_before
            not_after = self.certificate.not_valid_after

            now = datetime.now(timezone.utc) if not_after.tzinfo is not None else datetime.utcnow()

            valido = (not_before <= now <= not_after)
            dias_restantes = (not_after - now).days if isinstance(not_after, datetime) else None

            info = {
                'cnpj': cnpj,
                'titular': subj.rfc4514_string(),
                'emissor': issuer.rfc4514_string(),
                'valido_de': not_before.strftime('%d/%m/%Y'),
                'valido_ate': not_after.strftime('%d/%m/%Y'),
                'valido': valido,
                'dias_restantes': dias_restantes
            }
            return info

        except Exception as e:
            raise Exception(f"Erro ao validar certificado: {e}")

    def extrair_cnpj(self) -> Optional[str]:
        """
        Extrai CNPJ (serialNumber) do certificado, se disponível.
        """
        try:
            if not self.certificate:
                return None
            for attr in self.certificate.subject:
                try:
                    if attr.oid._name in ('serialNumber', 'SERIALNUMBER'):
                        return attr.value
                except Exception:
                    continue
            return None
        except Exception:
            return None

    def extrair_pem(self) -> Tuple[bytes, bytes]:
        """
        Retorna (cert_pem_bytes, key_pem_bytes)
        """
        if not self.certificate or not self.private_key:
            raise Exception("Certificado ou chave não carregados")

        try:
            cert_pem = self.certificate.public_bytes(encoding=serialization.Encoding.PEM)
            key_pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            )
            return cert_pem, key_pem
        except Exception as e:
            raise Exception(f"Erro ao extrair PEM: {e}")

    def salvar_pem_temporario(self, prefixo: str = 'certtmp') -> Tuple[str, str]:
        """
        Salva arquivos PEM temporários e retorna (cert_path, key_path).
        Usa tempfile.NamedTemporaryFile para criar arquivos seguros.
        """
        cert_pem, key_pem = self.extrair_pem()

        # criar arquivos temporários permanentes (delete=False) para uso com requests
        tmp_cert = tempfile.NamedTemporaryFile(prefix=f"{prefixo}_cert_", suffix=".pem", delete=False)
        tmp_key = tempfile.NamedTemporaryFile(prefix=f"{prefixo}_key_", suffix=".pem", delete=False)
        try:
            tmp_cert.write(cert_pem)
            tmp_cert.flush()
            tmp_cert.close()

            tmp_key.write(key_pem)
            tmp_key.flush()
            tmp_key.close()

            # armazenar caminhos para limpeza posterior
            self._tmp_cert_path = tmp_cert.name
            self._tmp_key_path = tmp_key.name

            # Permissões restritas (600)
            try:
                os.chmod(self._tmp_cert_path, 0o600)
                os.chmod(self._tmp_key_path, 0o600)
            except Exception:
                # permissão pode falhar em Windows - não crítico
                pass

            print(f"[CERTIFICADO] PEM temporário salvo: {self._tmp_cert_path}")
            print(f"[CHAVE] PEM temporária salva: {self._tmp_key_path}")

            return self._tmp_cert_path, self._tmp_key_path

        except Exception as e:
            # tentar remover em caso de erro parcial
            try:
                if os.path.exists(tmp_cert.name):
                    os.remove(tmp_cert.name)
                if os.path.exists(tmp_key.name):
                    os.remove(tmp_key.name)
            except Exception:
                pass
            raise Exception(f"Erro ao salvar PEM temporário: {e}")

    def limpar_pem_temporario(self, cert_path: Optional[str] = None, key_path: Optional[str] = None):
        """
        Remove arquivos PEM temporários.
        Se caminhos não informados, tenta limpar os que foram criados por esta instância.
        """
        to_remove = []
        if cert_path:
            to_remove.append(cert_path)
        elif self._tmp_cert_path:
            to_remove.append(self._tmp_cert_path)

        if key_path:
            to_remove.append(key_path)
        elif self._tmp_key_path:
            to_remove.append(self._tmp_key_path)

        for p in to_remove:
            try:
                if p and os.path.exists(p):
                    os.remove(p)
                    print(f"[CERTIFICADO] Removido: {p}")
            except Exception as e:
                print(f"[AVISO] Falha ao remover {p}: {e}")

        # reset internal refs
        self._tmp_cert_path = None
        self._tmp_key_path = None

# função de teste (mantida com cuidado)
def testar_certificado(empresa_id: int):
    cert = CertificadoDigital(empresa_id)
    if not cert.carregar_do_banco():
        print("Falha ao carregar certificado")
        return

    info = cert.validar_certificado()
    print("Informações do certificado:")
    for k, v in info.items():
        print(f"  {k}: {v}")

    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<NFe xmlns="http://www.portalfiscal.inf.br/nfe">
  <infNFe Id="NFe12345678901234567890123456789012345678901234" versao="4.00">
    <ide>
      <cUF>50</cUF>
      <natOp>VENDA</natOp>
      <mod>55</mod>
    </ide>
  </infNFe>
</NFe>"""
    try:
        xml_ass = cert.assinar_xml(sample_xml)
        print("XML assinado com sucesso. tamanho:", len(xml_ass))
    except Exception as e:
        print("Erro ao assinar XML:", e)

if __name__ == '__main__':
    # alterar para o ID real da empresa quando for testar
    testar_certificado(9)
