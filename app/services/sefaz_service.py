#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Serviço de Integração com SEFAZ
Compatível com:
- NF-e Modelo 55 (Versão 4.00)
- Webservices 2025/2026
- Autorização, Retorno, Consulta, Status
"""

import os
import sys
from typing import Dict, Optional
from datetime import datetime
import requests
import urllib3
from lxml import etree

# Desabilitar warnings de SSL (SEFAZ usa certificados específicos)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Ajuste de path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.certificado_digital import CertificadoDigital
from app.services.sefaz_webservices import (
    obter_webservice,
    obter_codigo_uf
)

try:
    from app.auto_config import DB_CONFIG
except ImportError:
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': 'aritana',
        'database': 'supply_chain_system'
    }


class SefazService:
    """
    Serviço principal de integração com SEFAZ
    - Envia NF-e (Modelo 55)
    - Consulta recibo
    - Consulta status
    """

    SOAP_NS = "http://www.w3.org/2003/05/soap-envelope"
    NFE_NS = "http://www.portalfiscal.inf.br/nfe"

    def __init__(self, ambiente='homologacao', empresa_id=None, uf=None, verificar_ssl=None):
        self.ambiente = ambiente
        self.empresa_id = empresa_id
        self.uf = uf
        self.cnpj = None
        self.codigo_uf = None
        self.urls = None
        self.timeout = 30
        self.cert_path = None
        self.key_path = None

        # SSL - Desabilitado temporariamente pois Python não tem certificados ICP-Brasil
        # Para produção real, instalar certificados raiz ICP-Brasil ou usar certifi atualizado
        self.verificar_ssl = False  # Temporário - produção real deve ser True com certs instalados
        if verificar_ssl is not None:
            self.verificar_ssl = verificar_ssl

        # Se UF informada manualmente
        if uf:
            self.codigo_uf = obter_codigo_uf(uf)
            self.urls = obter_webservice(uf, ambiente)

        # Se empresa definida → detectar UF automaticamente
        if empresa_id and not uf:
            self._detectar_uf_por_empresa()

    # ------------------------------------------------------------------------------
    # DETECTAR UF AUTOMATICAMENTE
    # ------------------------------------------------------------------------------

    def _detectar_uf_por_empresa(self):
        try:
            import mysql.connector
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT cnpj, estado, ambiente_nfe FROM empresas WHERE id = %s", (self.empresa_id,))
            empresa = cursor.fetchone()

            cursor.close()
            conn.close()

            if empresa:
                self.cnpj = empresa.get('cnpj')
                self.uf = empresa.get('estado')
                
                # Detectar ambiente da empresa (1=produção, 2=homologação)
                ambiente_nfe = empresa.get('ambiente_nfe')
                if ambiente_nfe:
                    self.ambiente = 'producao' if str(ambiente_nfe) == '1' else 'homologacao'
                    print(f"[SEFAZ] Ambiente detectado da empresa: {self.ambiente}")

                if self.uf:
                    self.codigo_uf = obter_codigo_uf(self.uf)
                    self.urls = obter_webservice(self.uf, self.ambiente)
        except Exception as e:
            print(f"[ERRO] Falha ao detectar UF: {e}")

    # ------------------------------------------------------------------------------
    # CERTIFICADO mTLS
    # ------------------------------------------------------------------------------

    def _preparar_certificado_mtls(self) -> Optional[tuple]:
        if not self.empresa_id:
            return None

        try:
            cert = CertificadoDigital(self.empresa_id)
            if not cert.carregar_do_banco():
                return None

            self.cert_path, self.key_path = cert.salvar_pem_temporario(
                prefixo=f"sefaz_{self.empresa_id}"
            )

            return (self.cert_path, self.key_path)

        except Exception as e:
            print(f"[ERRO mTLS] {e}")
            return None

    def _limpar_certificado_mtls(self):
        if self.cert_path and self.key_path:
            try:
                cert = CertificadoDigital(self.empresa_id)
                cert.limpar_pem_temporario(self.cert_path, self.key_path)
            except Exception:
                pass

    # ------------------------------------------------------------------------------
    # CONSULTAR STATUS DO SERVIÇO
    # ------------------------------------------------------------------------------

    def consultar_status_servico(self) -> Dict:
        try:
            if not self.urls:
                return {'sucesso': False, 'erro': 'UF não configurada'}

            tp_amb = "2" if self.ambiente == "homologacao" else "1"

            soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{self.SOAP_NS}">
  <soap:Header>
    <nfeCabecMsg xmlns="{self.NFE_NS}/wsdl/NFeStatusServico4">
      <cUF>{self.codigo_uf}</cUF>
      <versaoDados>4.00</versaoDados>
    </nfeCabecMsg>
  </soap:Header>
  <soap:Body>
    <nfeDadosMsg xmlns="{self.NFE_NS}/wsdl/NFeStatusServico4">
      <consStatServ xmlns="{self.NFE_NS}" versao="4.00">
        <tpAmb>{tp_amb}</tpAmb>
        <cUF>{self.codigo_uf}</cUF>
        <xServ>STATUS</xServ>
      </consStatServ>
    </nfeDadosMsg>
  </soap:Body>
</soap:Envelope>"""

            headers = {
                "Content-Type": "application/soap+xml; charset=utf-8",
                "SOAPAction": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeStatusServico4"
            }

            cert = self._preparar_certificado_mtls()

            try:
                response = requests.post(
                    self.urls['status'],
                    data=soap.encode('utf-8'),
                    headers=headers,
                    timeout=self.timeout,
                    cert=cert,
                    verify=self.verificar_ssl
                )
            finally:
                self._limpar_certificado_mtls()

            if response.status_code != 200:
                return {'sucesso': False, 'erro': response.text}

            root = etree.fromstring(response.content)
            ns = {"soap": self.SOAP_NS, "nfe": self.NFE_NS}

            retorno = root.find(".//nfe:retConsStatServ", ns)
            if retorno is None:
                return {'sucesso': False, 'erro': 'Resposta inválida'}

            cstat = retorno.findtext("nfe:cStat", namespaces=ns)
            motivo = retorno.findtext("nfe:xMotivo", namespaces=ns)

            return {
                'sucesso': cstat == "107",
                'codigo': cstat,
                'motivo': motivo
            }

        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}

    # ------------------------------------------------------------------------------
    # ENVIO DE NF-e
    # ------------------------------------------------------------------------------

    def enviar_nfe(self, xml_assinado: str, lote=None) -> Dict:
        try:
            if not lote:
                lote = datetime.now().strftime('%Y%m%d%H%M%S')

            tp_amb = "2" if self.ambiente == "homologacao" else "1"

            # Remover apenas a declaração XML do XML assinado (conteúdo deve permanecer
            # exatamente como foi assinado, para não quebrar a verificação da SEFAZ)
            xml_limpo = xml_assinado.strip()
            if xml_limpo.startswith('<?xml'):
                xml_limpo = xml_limpo.split('?>', 1)[1].strip()

            # NÃO alterar mais a tag <NFe> nem o namespace após a assinatura
            envelope = f"""<enviNFe xmlns="{self.NFE_NS}" versao="4.00"><idLote>{lote}</idLote><indSinc>1</indSinc>{xml_limpo}</enviNFe>"""
            
            # DEBUG: Salvar envelope para inspeção
            print(f"\n[DEBUG-ENVELOPE] Primeiros 1000 chars do envelope:")
            print(envelope[:1000])
            print(f"\n[DEBUG-ENVELOPE] Últimos 500 chars do envelope:")
            print(envelope[-500:])

            soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{self.SOAP_NS}">
  <soap:Header>
    <nfeCabecMsg xmlns="{self.NFE_NS}/wsdl/NFeAutorizacao4">
      <cUF>{self.codigo_uf}</cUF>
      <versaoDados>4.00</versaoDados>
    </nfeCabecMsg>
  </soap:Header>
  <soap:Body>
    <nfeDadosMsg xmlns="{self.NFE_NS}/wsdl/NFeAutorizacao4">
      {envelope}
    </nfeDadosMsg>
  </soap:Body>
</soap:Envelope>"""

            headers = {
                "Content-Type": "application/soap+xml; charset=utf-8",
                "SOAPAction": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4"
            }

            cert = self._preparar_certificado_mtls()

            try:
                response = requests.post(
                    self.urls['autorizacao'],
                    data=soap.encode('utf-8'),
                    headers=headers,
                    timeout=self.timeout,
                    cert=cert,
                    verify=self.verificar_ssl
                )
            finally:
                self._limpar_certificado_mtls()

            if response.status_code != 200:
                return {'sucesso': False, 'erro': f'HTTP {response.status_code}: {response.text}'}

            # Debug: mostrar resposta completa
            print(f"\n[SEFAZ-DEBUG] Response Status: {response.status_code}")
            print(f"[SEFAZ-DEBUG] Response Content (primeiros 500 chars):\n{response.text[:500]}")

            ns = {"soap": self.SOAP_NS, "nfe": self.NFE_NS}
            root = etree.fromstring(response.content)
            ret = root.find(".//nfe:retEnviNFe", ns)

            if ret is None:
                # Tentar sem namespace
                ret = root.find(".//retEnviNFe")
                if ret is None:
                    return {'sucesso': False, 'erro': f'Retorno inválido da SEFAZ. XML: {response.text[:500]}'}

            cstat = ret.findtext("nfe:cStat", namespaces=ns) or ret.findtext("cStat")
            motivo = ret.findtext("nfe:xMotivo", namespaces=ns) or ret.findtext("xMotivo")
            recibo = ret.findtext("nfe:infRec/nfe:nRec", namespaces=ns) or ret.findtext("infRec/nRec")

            # Estrutura base do resultado
            resultado = {
                # Sucesso de comunicação com SEFAZ (não necessariamente autorização da NFe)
                'sucesso': cstat in ["100", "103", "104"],
                'codigo': cstat,
                'motivo': motivo,
                'recibo': recibo,
                'lote': lote,
                # Campos adicionais esperados pelos scripts de teste
                'status': cstat,
                'codigo_status': cstat,
                'mensagem': motivo,
                'autorizado': False,
                'protocolo': None,
                'data_autorizacao': None,
                'xml_completo': None,
            }

            # cStat 103: lote recebido para processamento assíncrono
            if cstat == "103" and recibo:
                return self.consultar_recibo(recibo)

            # cStat 104: lote processado (modo síncrono) → ler protNFe/infProt
            if cstat == "104":
                prot = ret.find(".//nfe:protNFe", ns)
                if prot is None:
                    prot = ret.find(".//protNFe")
                if prot is not None:
                    inf_prot = prot.find("nfe:infProt", ns)
                    if inf_prot is None:
                        inf_prot = prot.find("infProt")
                    if inf_prot is not None:
                        cstat_nfe = inf_prot.findtext("nfe:cStat", namespaces=ns) or inf_prot.findtext("cStat")
                        xmotivo_nfe = inf_prot.findtext("nfe:xMotivo", namespaces=ns) or inf_prot.findtext("xMotivo")
                        nprot = inf_prot.findtext("nfe:nProt", namespaces=ns) or inf_prot.findtext("nProt")
                        dhrecbto_nfe = inf_prot.findtext("nfe:dhRecbto", namespaces=ns) or inf_prot.findtext("dhRecbto")

                        # Autorizado quando cStat da NFe = 100
                        autorizado = cstat_nfe == "100"

                        resultado.update({
                            'status': cstat_nfe,
                            'codigo_status': cstat_nfe,
                            'mensagem': xmotivo_nfe,
                            'autorizado': autorizado,
                            'protocolo': nprot,
                            'data_autorizacao': dhrecbto_nfe,
                        })

                        if not autorizado and cstat_nfe:
                            resultado.setdefault('erros', []).append(f"{cstat_nfe} - {xmotivo_nfe}")

            return resultado

        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}

    # ------------------------------------------------------------------------------
    # CONSULTAR RECIBO
    # ------------------------------------------------------------------------------

    def consultar_recibo(self, recibo: str) -> Dict:
        try:
            tp_amb = "2" if self.ambiente == "homologacao" else "1"

            soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{self.SOAP_NS}">
  <soap:Header>
    <nfeCabecMsg xmlns="{self.NFE_NS}/wsdl/NFeRetAutorizacao4">
      <cUF>{self.codigo_uf}</cUF>
      <versaoDados>4.00</versaoDados>
    </nfeCabecMsg>
  </soap:Header>
  <soap:Body>
    <nfeDadosMsg xmlns="{self.NFE_NS}/wsdl/NFeRetAutorizacao4">
      <consReciNFe xmlns="{self.NFE_NS}" versao="4.00">
        <tpAmb>{tp_amb}</tpAmb>
        <nRec>{recibo}</nRec>
      </consReciNFe>
    </nfeDadosMsg>
  </soap:Body>
</soap:Envelope>"""

            headers = {
                "Content-Type": "application/soap+xml; charset=utf-8",
                "SOAPAction": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRetAutorizacao4"
            }

            cert = self._preparar_certificado_mtls()

            try:
                response = requests.post(
                    self.urls['retorno'],
                    data=soap.encode('utf-8'),
                    headers=headers,
                    cert=cert,
                    timeout=self.timeout,
                    verify=self.verificar_ssl
                )
            finally:
                self._limpar_certificado_mtls()

            if response.status_code != 200:
                return {'sucesso': False, 'erro': response.text}

            ns = {"soap": self.SOAP_NS, "nfe": self.NFE_NS}
            root = etree.fromstring(response.content)

            ret = root.find(".//nfe:retConsReciNFe", ns)
            if ret is None:
                return {'sucesso': False, 'erro': 'Retorno inválido'}

            prot = ret.find(".//nfe:protNFe/nfe:infProt", ns)

            if prot is None:
                return {
                    'sucesso': False,
                    'codigo': ret.findtext("nfe:cStat", namespaces=ns),
                    'motivo': ret.findtext("nfe:xMotivo", namespaces=ns)
                }

            cstat = prot.findtext("nfe:cStat", namespaces=ns)
            motivo = prot.findtext("nfe:xMotivo", namespaces=ns)
            protocolo = prot.findtext("nfe:nProt", namespaces=ns)
            chave = prot.findtext("nfe:chNFe", namespaces=ns)

            return {
                'sucesso': cstat == "100",
                'codigo': cstat,
                'motivo': motivo,
                'protocolo': protocolo,
                'chave': chave
            }

        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}

    # ------------------------------------------------------------------------------
    # CONSULTAR NF-e POR CHAVE
    # ------------------------------------------------------------------------------

    def consultar_nfe(self, chave_acesso: str) -> Dict:
        """
        Consulta NFe na SEFAZ pela chave de acesso (44 dígitos).
        Retorna informações sobre a situação da NFe.
        """
        try:
            if not self.urls:
                return {'sucesso': False, 'erro': 'UF não configurada'}

            # Validar chave de acesso
            chave_limpa = ''.join(c for c in chave_acesso if c.isdigit())
            if len(chave_limpa) != 44:
                return {'sucesso': False, 'erro': f'Chave de acesso inválida (deve ter 44 dígitos, tem {len(chave_limpa)})'}

            tp_amb = "2" if self.ambiente == "homologacao" else "1"

            soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{self.SOAP_NS}">
  <soap:Header>
    <nfeCabecMsg xmlns="{self.NFE_NS}/wsdl/NFeConsultaProtocolo4">
      <cUF>{self.codigo_uf}</cUF>
      <versaoDados>4.00</versaoDados>
    </nfeCabecMsg>
  </soap:Header>
  <soap:Body>
    <nfeDadosMsg xmlns="{self.NFE_NS}/wsdl/NFeConsultaProtocolo4">
      <consSitNFe xmlns="{self.NFE_NS}" versao="4.00">
        <tpAmb>{tp_amb}</tpAmb>
        <xServ>CONSULTAR</xServ>
        <chNFe>{chave_limpa}</chNFe>
      </consSitNFe>
    </nfeDadosMsg>
  </soap:Body>
</soap:Envelope>"""

            headers = {
                "Content-Type": "application/soap+xml; charset=utf-8",
                "SOAPAction": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4"
            }

            cert = self._preparar_certificado_mtls()

            try:
                response = requests.post(
                    self.urls['consulta'],
                    data=soap.encode('utf-8'),
                    headers=headers,
                    timeout=self.timeout,
                    cert=cert,
                    verify=self.verificar_ssl
                )
            finally:
                self._limpar_certificado_mtls()

            if response.status_code != 200:
                return {'sucesso': False, 'erro': f'HTTP {response.status_code}: {response.text[:200]}'}

            ns = {"soap": self.SOAP_NS, "nfe": self.NFE_NS}
            root = etree.fromstring(response.content)

            ret = root.find(".//nfe:retConsSitNFe", ns)
            if ret is None:
                return {'sucesso': False, 'erro': 'Resposta inválida da SEFAZ'}

            cstat = ret.findtext("nfe:cStat", namespaces=ns)
            motivo = ret.findtext("nfe:xMotivo", namespaces=ns)

            # Informações do protocolo (se autorizada)
            prot = ret.find(".//nfe:protNFe/nfe:infProt", ns)
            protocolo = None
            data_autorizacao = None

            if prot is not None:
                protocolo = prot.findtext("nfe:nProt", namespaces=ns)
                dh_recbto = prot.findtext("nfe:dhRecbto", namespaces=ns)
                if dh_recbto:
                    data_autorizacao = dh_recbto

            # Informações de cancelamento (se cancelada)
            evento_canc = ret.find(".//nfe:procEventoNFe", ns)
            cancelada = False
            data_cancelamento = None
            motivo_cancelamento = None

            if evento_canc is not None:
                ret_evento = evento_canc.find(".//nfe:retEvento", ns)
                if ret_evento is not None:
                    cstat_evento = ret_evento.findtext("nfe:cStat", namespaces=ns)
                    if cstat_evento == "135":  # Evento registrado e vinculado
                        cancelada = True
                        data_cancelamento = ret_evento.findtext("nfe:dhRegEvento", namespaces=ns)
                        motivo_cancelamento = ret_evento.findtext("nfe:xMotivo", namespaces=ns)

            resultado = {
                'sucesso': cstat in ["100", "101"],  # 100=Autorizada, 101=Cancelada
                'codigo': cstat,
                'motivo': motivo,
                'chave': chave_limpa,
                'protocolo': protocolo,
                'data_autorizacao': data_autorizacao,
                'cancelada': cancelada,
                'data_cancelamento': data_cancelamento,
                'motivo_cancelamento': motivo_cancelamento,
                'ambiente': self.ambiente
            }

            return resultado

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'erro': str(e)}

    # ------------------------------------------------------------------------------
    # CANCELAMENTO DE NF-e (Evento 110111)
    # ------------------------------------------------------------------------------

    def cancelar_nfe(self, chave_acesso: str, protocolo: str, justificativa: str) -> Dict:
        """
        Cancela uma NF-e já autorizada.
        
        Args:
            chave_acesso: Chave de acesso da NF-e (44 dígitos)
            protocolo: Número do protocolo de autorização
            justificativa: Motivo do cancelamento (mínimo 15 caracteres)
        
        Returns:
            Dict com resultado do cancelamento
        """
        try:
            if not self.urls:
                return {'sucesso': False, 'erro': 'UF não configurada'}

            # Validações
            chave_limpa = ''.join(c for c in chave_acesso if c.isdigit())
            if len(chave_limpa) != 44:
                return {'sucesso': False, 'erro': f'Chave de acesso inválida (deve ter 44 dígitos)'}

            if len(justificativa) < 15:
                return {'sucesso': False, 'erro': 'Justificativa deve ter no mínimo 15 caracteres'}

            if len(justificativa) > 255:
                justificativa = justificativa[:255]

            # Validar protocolo (pode ser None se NF-e não foi autorizada)
            if not protocolo:
                return {'sucesso': False, 'erro': 'Protocolo de autorização não informado. A NF-e pode não ter sido autorizada.'}
            
            protocolo_limpo = ''.join(c for c in str(protocolo) if c.isdigit())
            if not protocolo_limpo:
                return {'sucesso': False, 'erro': 'Protocolo de autorização inválido'}
            
            print(f"[CANCELAMENTO] Iniciando cancelamento - Chave: {chave_limpa}, Protocolo: {protocolo_limpo}, Ambiente: {self.ambiente}")

            tp_amb = "2" if self.ambiente == "homologacao" else "1"
            
            # Extrair CNPJ da chave de acesso (posições 6-19)
            cnpj_emitente = chave_limpa[6:20]
            
            # Data/hora do evento
            from datetime import datetime
            dh_evento = datetime.now().strftime('%Y-%m-%dT%H:%M:%S-04:00')
            
            # ID do evento: ID + tpEvento + chNFe + nSeqEvento (2 dígitos)
            id_evento = f"ID110111{chave_limpa}01"
            
            # ID do lote
            id_lote = datetime.now().strftime('%Y%m%d%H%M%S')

            # Construir XML do evento
            xml_evento = self._construir_xml_evento_cancelamento(
                id_evento=id_evento,
                id_lote=id_lote,
                tp_amb=tp_amb,
                cnpj=cnpj_emitente,
                chave=chave_limpa,
                dh_evento=dh_evento,
                protocolo=protocolo_limpo,
                justificativa=justificativa
            )

            # Assinar o evento
            print("[CANCELAMENTO] Assinando evento de cancelamento...")
            xml_assinado = self._assinar_evento(xml_evento)
            if not xml_assinado:
                print("[CANCELAMENTO] ERRO: Falha na assinatura do evento")
                return {'sucesso': False, 'erro': 'Falha ao assinar evento de cancelamento'}
            
            print(f"[CANCELAMENTO] Evento assinado OK. Enviando para SEFAZ (URL: {self.urls.get('evento', 'N/A')})...")

            # Montar envelope SOAP
            soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{self.SOAP_NS}">
  <soap:Header>
    <nfeCabecMsg xmlns="{self.NFE_NS}/wsdl/NFeRecepcaoEvento4">
      <cUF>{self.codigo_uf}</cUF>
      <versaoDados>1.00</versaoDados>
    </nfeCabecMsg>
  </soap:Header>
  <soap:Body>
    <nfeDadosMsg xmlns="{self.NFE_NS}/wsdl/NFeRecepcaoEvento4">
      {xml_assinado}
    </nfeDadosMsg>
  </soap:Body>
</soap:Envelope>"""

            headers = {
                "Content-Type": "application/soap+xml; charset=utf-8",
                "SOAPAction": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"
            }

            cert = self._preparar_certificado_mtls()

            try:
                print(f"[CANCELAMENTO] Enviando requisição HTTP POST para evento...")
                response = requests.post(
                    self.urls['evento'],
                    data=soap.encode('utf-8'),
                    headers=headers,
                    timeout=self.timeout,
                    cert=cert,
                    verify=self.verificar_ssl
                )
                print(f"[CANCELAMENTO] Resposta HTTP recebida: status={response.status_code}")
            finally:
                self._limpar_certificado_mtls()

            if response.status_code != 200:
                print(f"[CANCELAMENTO] ERRO HTTP: {response.status_code}")
                return {'sucesso': False, 'erro': f'HTTP {response.status_code}: {response.text[:200]}'}

            # Processar resposta - mostrar XML completo para debug
            print(f"[CANCELAMENTO] Resposta XML SEFAZ (1000 chars): {response.text[:1000]}")
            
            ns = {"soap": self.SOAP_NS, "nfe": self.NFE_NS}
            root = etree.fromstring(response.content)

            ret_evento = root.find(".//nfe:retEvento", ns)
            if ret_evento is None:
                ret_evento = root.find(".//retEvento")

            if ret_evento is None:
                print(f"[CANCELAMENTO] ERRO: retEvento não encontrado na resposta!")
                return {'sucesso': False, 'erro': 'Resposta inválida da SEFAZ'}

            inf_evento = ret_evento.find("nfe:infEvento", ns)
            if inf_evento is None:
                inf_evento = ret_evento.find("infEvento")

            if inf_evento is None:
                return {'sucesso': False, 'erro': 'infEvento não encontrado na resposta'}

            cstat = inf_evento.findtext("nfe:cStat", namespaces=ns) or inf_evento.findtext("cStat")
            motivo = inf_evento.findtext("nfe:xMotivo", namespaces=ns) or inf_evento.findtext("xMotivo")
            nprot = inf_evento.findtext("nfe:nProt", namespaces=ns) or inf_evento.findtext("nProt")
            dh_reg = inf_evento.findtext("nfe:dhRegEvento", namespaces=ns) or inf_evento.findtext("dhRegEvento")

            # cStat 135 = Evento registrado e vinculado a NF-e
            # cStat 155 = Cancelamento homologado fora de prazo
            sucesso = cstat in ["135", "155"]
            
            print(f"[CANCELAMENTO] Resposta SEFAZ - cStat: {cstat}, Motivo: {motivo}, Protocolo: {nprot}")

            resultado = {
                'sucesso': sucesso,
                'codigo': cstat,
                'motivo': motivo,
                'protocolo_cancelamento': nprot,
                'data_cancelamento': dh_reg,
                'chave': chave_limpa,
                'ambiente': self.ambiente
            }

            if not sucesso:
                resultado['erro'] = f'{cstat} - {motivo}'
                print(f"[CANCELAMENTO] ERRO: {resultado['erro']}")

            return resultado

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'erro': str(e)}

    def _construir_xml_evento_cancelamento(self, id_evento: str, id_lote: str, tp_amb: str,
                                            cnpj: str, chave: str, dh_evento: str,
                                            protocolo: str, justificativa: str) -> str:
        """Constrói o XML do evento de cancelamento (sem assinatura e sem formatação)"""
        
        # XML sem espaços/quebras de linha entre tags (SEFAZ rejeita com erro 588)
        xml = (
            f'<envEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00">'
            f'<idLote>{id_lote}</idLote>'
            f'<evento versao="1.00">'
            f'<infEvento Id="{id_evento}">'
            f'<cOrgao>{self.codigo_uf}</cOrgao>'
            f'<tpAmb>{tp_amb}</tpAmb>'
            f'<CNPJ>{cnpj}</CNPJ>'
            f'<chNFe>{chave}</chNFe>'
            f'<dhEvento>{dh_evento}</dhEvento>'
            f'<tpEvento>110111</tpEvento>'
            f'<nSeqEvento>1</nSeqEvento>'
            f'<verEvento>1.00</verEvento>'
            f'<detEvento versao="1.00">'
            f'<descEvento>Cancelamento</descEvento>'
            f'<nProt>{protocolo}</nProt>'
            f'<xJust>{justificativa}</xJust>'
            f'</detEvento>'
            f'</infEvento>'
            f'</evento>'
            f'</envEvento>'
        )
        
        return xml

    def _assinar_evento(self, xml_evento: str) -> Optional[str]:
        """Assina o XML do evento usando o certificado digital"""
        try:
            print("[ASSINAR-EVENTO] Iniciando assinatura do evento...")
            from copy import deepcopy
            import hashlib
            import base64
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding

            # Carregar certificado
            cert_digital = CertificadoDigital(self.empresa_id)
            if not cert_digital.carregar_do_banco():
                print("[ASSINAR-EVENTO] ERRO: Não foi possível carregar certificado")
                return None
            
            print("[ASSINAR-EVENTO] Certificado carregado OK")

            # Parse do XML
            root = etree.fromstring(xml_evento.encode('utf-8'))
            ns_nfe = "http://www.portalfiscal.inf.br/nfe"
            ns_ds = "http://www.w3.org/2000/09/xmldsig#"

            # Encontrar o elemento evento e infEvento
            evento = root.find(".//{%s}evento" % ns_nfe)
            if evento is None:
                evento = root.find(".//evento")
            
            inf_evento = evento.find("{%s}infEvento" % ns_nfe)
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
            signature = etree.SubElement(evento, '{%s}Signature' % ns_ds, nsmap={None: ns_ds})

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

            # Usar a private_key carregada pelo CertificadoDigital (novo modelo)
            assinatura = cert_digital.private_key.sign(
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

            # Obter certificado em PEM e converter para o formato esperado (base64 sem cabeçalhos)
            cert_pem, _ = cert_digital.extrair_pem()
            cert_pem_str = cert_pem.decode('ascii')
            cert_b64 = cert_pem_str.replace('-----BEGIN CERTIFICATE-----', '').replace('-----END CERTIFICATE-----', '').replace('\n', '')
            x509_cert.text = cert_b64

            # Retornar apenas o conteúdo do envEvento (sem declaração XML)
            xml_assinado = etree.tostring(root, encoding='unicode')
            
            # Remover declaração XML se houver
            if xml_assinado.startswith('<?xml'):
                xml_assinado = xml_assinado.split('?>', 1)[1].strip()

            print(f"[ASSINAR-EVENTO] Assinatura concluída com sucesso! (tamanho: {len(xml_assinado)} chars)")
            return xml_assinado

        except Exception as e:
            import traceback
            print(f"[ASSINAR-EVENTO] ERRO ao assinar evento: {e}")
            traceback.print_exc()
            return None

    # ------------------------------------------------------------------------------
    # CARTA DE CORREÇÃO ELETRÔNICA (CC-e) - Evento 110110
    # ------------------------------------------------------------------------------

    def carta_correcao(self, chave_acesso: str, correcao: str, sequencia: int = 1) -> Dict:
        """
        Envia Carta de Correção Eletrônica (CC-e) para uma NF-e.
        
        A CC-e permite corrigir informações da NF-e sem cancelá-la.
        NÃO pode corrigir: valores, quantidades, dados fiscais, dados do emitente/destinatário.
        
        Args:
            chave_acesso: Chave de acesso da NF-e (44 dígitos)
            correcao: Texto da correção (15-1000 caracteres)
            sequencia: Número sequencial do evento (1-20, padrão=1)
        
        Returns:
            Dict com resultado da CC-e
        """
        try:
            if not self.urls:
                return {'sucesso': False, 'erro': 'UF não configurada'}

            # Validações
            chave_limpa = ''.join(c for c in chave_acesso if c.isdigit())
            if len(chave_limpa) != 44:
                return {'sucesso': False, 'erro': 'Chave de acesso inválida (deve ter 44 dígitos)'}

            if len(correcao) < 15:
                return {'sucesso': False, 'erro': 'Texto da correção deve ter no mínimo 15 caracteres'}

            if len(correcao) > 1000:
                correcao = correcao[:1000]

            if sequencia < 1 or sequencia > 20:
                return {'sucesso': False, 'erro': 'Sequência deve ser entre 1 e 20'}

            tp_amb = "2" if self.ambiente == "homologacao" else "1"
            
            # Extrair CNPJ da chave de acesso (posições 6-19)
            cnpj_emitente = chave_limpa[6:20]
            
            # Data/hora do evento
            from datetime import datetime
            dh_evento = datetime.now().strftime('%Y-%m-%dT%H:%M:%S-04:00')
            
            # ID do evento: ID + tpEvento + chNFe + nSeqEvento (2 dígitos)
            id_evento = f"ID110110{chave_limpa}{sequencia:02d}"
            
            # ID do lote
            id_lote = datetime.now().strftime('%Y%m%d%H%M%S')

            # Construir XML do evento
            xml_evento = self._construir_xml_carta_correcao(
                id_evento=id_evento,
                id_lote=id_lote,
                tp_amb=tp_amb,
                cnpj=cnpj_emitente,
                chave=chave_limpa,
                dh_evento=dh_evento,
                correcao=correcao,
                sequencia=sequencia
            )

            # Assinar o evento
            xml_assinado = self._assinar_evento(xml_evento)
            if not xml_assinado:
                return {'sucesso': False, 'erro': 'Falha ao assinar evento de carta de correção'}

            # Montar envelope SOAP
            soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{self.SOAP_NS}">
  <soap:Header>
    <nfeCabecMsg xmlns="{self.NFE_NS}/wsdl/NFeRecepcaoEvento4">
      <cUF>{self.codigo_uf}</cUF>
      <versaoDados>1.00</versaoDados>
    </nfeCabecMsg>
  </soap:Header>
  <soap:Body>
    <nfeDadosMsg xmlns="{self.NFE_NS}/wsdl/NFeRecepcaoEvento4">
      {xml_assinado}
    </nfeDadosMsg>
  </soap:Body>
</soap:Envelope>"""

            headers = {
                "Content-Type": "application/soap+xml; charset=utf-8",
                "SOAPAction": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4"
            }

            cert = self._preparar_certificado_mtls()

            try:
                response = requests.post(
                    self.urls['evento'],
                    data=soap.encode('utf-8'),
                    headers=headers,
                    timeout=self.timeout,
                    cert=cert,
                    verify=self.verificar_ssl
                )
            finally:
                self._limpar_certificado_mtls()

            if response.status_code != 200:
                return {'sucesso': False, 'erro': f'HTTP {response.status_code}: {response.text[:200]}'}

            # Processar resposta
            ns = {"soap": self.SOAP_NS, "nfe": self.NFE_NS}
            root = etree.fromstring(response.content)

            ret_evento = root.find(".//nfe:retEvento", ns)
            if ret_evento is None:
                ret_evento = root.find(".//retEvento")

            if ret_evento is None:
                return {'sucesso': False, 'erro': 'Resposta inválida da SEFAZ'}

            inf_evento = ret_evento.find("nfe:infEvento", ns)
            if inf_evento is None:
                inf_evento = ret_evento.find("infEvento")

            if inf_evento is None:
                return {'sucesso': False, 'erro': 'infEvento não encontrado na resposta'}

            cstat = inf_evento.findtext("nfe:cStat", namespaces=ns) or inf_evento.findtext("cStat")
            motivo = inf_evento.findtext("nfe:xMotivo", namespaces=ns) or inf_evento.findtext("xMotivo")
            nprot = inf_evento.findtext("nfe:nProt", namespaces=ns) or inf_evento.findtext("nProt")
            dh_reg = inf_evento.findtext("nfe:dhRegEvento", namespaces=ns) or inf_evento.findtext("dhRegEvento")

            # cStat 135 = Evento registrado e vinculado a NF-e
            sucesso = cstat == "135"

            resultado = {
                'sucesso': sucesso,
                'codigo': cstat,
                'motivo': motivo,
                'protocolo': nprot,
                'data_registro': dh_reg,
                'sequencia': sequencia,
                'chave': chave_limpa,
                'ambiente': self.ambiente
            }

            if not sucesso:
                resultado['erro'] = f'{cstat} - {motivo}'

            return resultado

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'erro': str(e)}

    def _construir_xml_carta_correcao(self, id_evento: str, id_lote: str, tp_amb: str,
                                       cnpj: str, chave: str, dh_evento: str,
                                       correcao: str, sequencia: int) -> str:
        """Constrói o XML do evento de Carta de Correção (sem assinatura e sem formatação)"""
        
        # Escapar caracteres especiais no texto da correção
        correcao_escaped = correcao.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Condição de uso obrigatória para CC-e
        condicao_uso = ("A Carta de Correcao e disciplinada pelo paragrafo 1o-A do art. 7o do "
                        "Convenio S/N, de 15 de dezembro de 1970 e pode ser utilizada para "
                        "regularizacao de erro ocorrido na emissao de documento fiscal, desde que "
                        "o erro nao esteja relacionado com: I - as variaveis que determinam o valor "
                        "do imposto tais como: base de calculo, aliquota, diferenca de preco, "
                        "quantidade, valor da operacao ou da prestacao; II - a correcao de dados "
                        "cadastrais que implique mudanca do remetente ou do destinatario; "
                        "III - a data de emissao ou de saida.")
        
        # XML sem espaços/quebras de linha entre tags (SEFAZ rejeita com erro 588)
        xml = (
            f'<envEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00">'
            f'<idLote>{id_lote}</idLote>'
            f'<evento versao="1.00">'
            f'<infEvento Id="{id_evento}">'
            f'<cOrgao>{self.codigo_uf}</cOrgao>'
            f'<tpAmb>{tp_amb}</tpAmb>'
            f'<CNPJ>{cnpj}</CNPJ>'
            f'<chNFe>{chave}</chNFe>'
            f'<dhEvento>{dh_evento}</dhEvento>'
            f'<tpEvento>110110</tpEvento>'
            f'<nSeqEvento>{sequencia}</nSeqEvento>'
            f'<verEvento>1.00</verEvento>'
            f'<detEvento versao="1.00">'
            f'<descEvento>Carta de Correcao</descEvento>'
            f'<xCorrecao>{correcao_escaped}</xCorrecao>'
            f'<xCondUso>{condicao_uso}</xCondUso>'
            f'</detEvento>'
            f'</infEvento>'
            f'</evento>'
            f'</envEvento>'
        )
        
        return xml

    # ------------------------------------------------------------------------------
    # INUTILIZAÇÃO DE NUMERAÇÃO
    # ------------------------------------------------------------------------------

    def inutilizar_numeracao(self, cnpj: str, serie: int, numero_inicial: int,
                              numero_final: int, justificativa: str, ano: int = None) -> Dict:
        """
        Inutiliza uma faixa de números de NF-e.
        
        Usado quando números foram pulados na sequência e não serão mais utilizados.
        Exemplo: Se emitiu NF-e 100 e depois 105, deve inutilizar 101-104.
        
        Args:
            cnpj: CNPJ do emitente (14 dígitos)
            serie: Série da NF-e
            numero_inicial: Número inicial da faixa
            numero_final: Número final da faixa
            justificativa: Motivo da inutilização (15-255 caracteres)
            ano: Ano da inutilização (2 dígitos, ex: 25 para 2025)
        
        Returns:
            Dict com resultado da inutilização
        """
        try:
            if not self.urls:
                return {'sucesso': False, 'erro': 'UF não configurada'}

            # Validações
            cnpj_limpo = ''.join(c for c in cnpj if c.isdigit()).zfill(14)
            if len(cnpj_limpo) != 14:
                return {'sucesso': False, 'erro': 'CNPJ deve ter 14 dígitos'}

            if numero_inicial <= 0:
                return {'sucesso': False, 'erro': 'Número inicial deve ser maior que zero'}

            if numero_final < numero_inicial:
                return {'sucesso': False, 'erro': 'Número final deve ser maior ou igual ao inicial'}

            if len(justificativa) < 15:
                return {'sucesso': False, 'erro': 'Justificativa deve ter no mínimo 15 caracteres'}

            if len(justificativa) > 255:
                justificativa = justificativa[:255]

            tp_amb = "2" if self.ambiente == "homologacao" else "1"
            
            # Ano (sempre 2 dígitos - últimos 2 dígitos do ano)
            from datetime import datetime
            if ano:
                ano_2d = ano % 100  # Garante apenas 2 dígitos (ex: 2025 -> 25)
            else:
                ano_2d = int(datetime.now().strftime('%y'))  # Ex: 25

            # Construir XML de inutilização
            xml_inut = self._construir_xml_inutilizacao(
                cnpj=cnpj_limpo, serie=serie, numero_inicial=numero_inicial,
                numero_final=numero_final, justificativa=justificativa,
                ano=ano_2d, tp_amb=tp_amb
            )

            # Assinar
            xml_assinado = self._assinar_inutilizacao(xml_inut)
            if not xml_assinado:
                return {'sucesso': False, 'erro': 'Falha ao assinar XML de inutilização'}

            # Montar envelope SOAP
            soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="{self.SOAP_NS}">
  <soap:Header>
    <nfeCabecMsg xmlns="{self.NFE_NS}/wsdl/NFeInutilizacao4">
      <cUF>{self.codigo_uf}</cUF>
      <versaoDados>4.00</versaoDados>
    </nfeCabecMsg>
  </soap:Header>
  <soap:Body>
    <nfeDadosMsg xmlns="{self.NFE_NS}/wsdl/NFeInutilizacao4">
      {xml_assinado}
    </nfeDadosMsg>
  </soap:Body>
</soap:Envelope>"""

            headers = {
                "Content-Type": "application/soap+xml; charset=utf-8",
                "SOAPAction": "http://www.portalfiscal.inf.br/nfe/wsdl/NFeInutilizacao4"
            }

            cert = self._preparar_certificado_mtls()

            try:
                response = requests.post(
                    self.urls['inutilizacao'], data=soap.encode('utf-8'),
                    headers=headers, timeout=self.timeout,
                    cert=cert, verify=self.verificar_ssl
                )
            finally:
                self._limpar_certificado_mtls()

            if response.status_code != 200:
                print(f"[INUTILIZAÇÃO] ERRO HTTP: {response.status_code}")
                return {'sucesso': False, 'erro': f'HTTP {response.status_code}: {response.text[:200]}'}

            # Processar resposta - mostrar XML completo para debug
            print(f"[INUTILIZAÇÃO] Resposta XML SEFAZ (1000 chars): {response.text[:1000]}")
            
            ns = {"soap": self.SOAP_NS, "nfe": self.NFE_NS}
            root = etree.fromstring(response.content)

            ret_inut = root.find(".//nfe:retInutNFe", ns)
            if ret_inut is None:
                ret_inut = root.find(".//retInutNFe")

            if ret_inut is None:
                print(f"[INUTILIZAÇÃO] ERRO: retInutNFe não encontrado!")
                return {'sucesso': False, 'erro': 'Resposta inválida da SEFAZ'}

            inf_inut = ret_inut.find("nfe:infInut", ns)
            if inf_inut is None:
                inf_inut = ret_inut.find("infInut")

            cstat = inf_inut.findtext("nfe:cStat", namespaces=ns) or inf_inut.findtext("cStat") if inf_inut is not None else None
            motivo = inf_inut.findtext("nfe:xMotivo", namespaces=ns) or inf_inut.findtext("xMotivo") if inf_inut is not None else None
            nprot = inf_inut.findtext("nfe:nProt", namespaces=ns) or inf_inut.findtext("nProt") if inf_inut is not None else None
            dh_recbto = inf_inut.findtext("nfe:dhRecbto", namespaces=ns) or inf_inut.findtext("dhRecbto") if inf_inut is not None else None

            print(f"[INUTILIZAÇÃO] Resposta SEFAZ - cStat: {cstat}, Motivo: {motivo}")

            # cStat 102 = Inutilização homologada
            sucesso = cstat == "102"

            resultado = {
                'sucesso': sucesso, 'codigo': cstat, 'motivo': motivo,
                'protocolo': nprot, 'data_inutilizacao': dh_recbto,
                'serie': serie, 'numero_inicial': numero_inicial,
                'numero_final': numero_final, 'ambiente': self.ambiente
            }

            if not sucesso:
                resultado['erro'] = f'{cstat} - {motivo}'
                print(f"[INUTILIZAÇÃO] ERRO: {resultado['erro']}")

            return resultado

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'erro': str(e)}

    def _construir_xml_inutilizacao(self, cnpj: str, serie: int,
                                     numero_inicial: int, numero_final: int, justificativa: str,
                                     ano: int, tp_amb: str) -> str:
        """Constrói o XML de inutilização (sem assinatura e sem formatação)"""
        # ID: ID + cUF(2) + Ano(2) + CNPJ(14) + mod(2) + série(3) + nNFIni(9) + nNFFin(9)
        id_inut = f"ID{self.codigo_uf}{ano:02d}{cnpj}55{serie:03d}{numero_inicial:09d}{numero_final:09d}"
        
        print(f"[INUTILIZAÇÃO] ID gerado: {id_inut} (tamanho: {len(id_inut)})")
        print(f"[INUTILIZAÇÃO] CNPJ: {cnpj} (tamanho: {len(cnpj)})")
        
        # XML sem espaços/quebras de linha entre tags (SEFAZ rejeita com erro 588)
        # Ordem das tags conforme schema PL_009q (NT 2011/004)
        xml = (
            f'<inutNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">'
            f'<infInut Id="{id_inut}">'
            f'<tpAmb>{tp_amb}</tpAmb>'
            f'<xServ>INUTILIZAR</xServ>'
            f'<cUF>{self.codigo_uf}</cUF>'
            f'<ano>{ano:02d}</ano>'
            f'<CNPJ>{cnpj}</CNPJ>'
            f'<mod>55</mod>'
            f'<serie>{serie}</serie>'
            f'<nNFIni>{numero_inicial}</nNFIni>'
            f'<nNFFin>{numero_final}</nNFFin>'
            f'<xJust>{justificativa}</xJust>'
            f'</infInut>'
            f'</inutNFe>'
        )
        
        print(f"[INUTILIZAÇÃO] XML gerado: {xml}")
        return xml

    def _assinar_inutilizacao(self, xml_inut: str) -> Optional[str]:
        """Assina o XML de inutilização"""
        try:
            from copy import deepcopy
            import hashlib
            import base64
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding

            cert_digital = CertificadoDigital(self.empresa_id)
            if not cert_digital.carregar_do_banco():
                return None

            ns_nfe = "http://www.portalfiscal.inf.br/nfe"
            ns_ds = "http://www.w3.org/2000/09/xmldsig#"

            root = etree.fromstring(xml_inut.encode('utf-8'))
            inf_inut = root.find("{%s}infInut" % ns_nfe) or root.find("infInut")
            id_inut = inf_inut.get("Id")

            # DigestValue
            inf_inut_c14n = etree.tostring(deepcopy(inf_inut), method='c14n', exclusive=False, with_comments=False)
            digest_b64 = base64.b64encode(hashlib.sha1(inf_inut_c14n).digest()).decode('ascii')

            # Signature
            signature = etree.SubElement(root, '{%s}Signature' % ns_ds, nsmap={None: ns_ds})
            signed_info = etree.SubElement(signature, 'SignedInfo')
            etree.SubElement(signed_info, 'CanonicalizationMethod').set('Algorithm', 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
            etree.SubElement(signed_info, 'SignatureMethod').set('Algorithm', 'http://www.w3.org/2000/09/xmldsig#rsa-sha1')

            reference = etree.SubElement(signed_info, 'Reference', URI=f'#{id_inut}')
            transforms = etree.SubElement(reference, 'Transforms')
            etree.SubElement(transforms, 'Transform').set('Algorithm', 'http://www.w3.org/2000/09/xmldsig#enveloped-signature')
            etree.SubElement(transforms, 'Transform').set('Algorithm', 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
            etree.SubElement(reference, 'DigestMethod').set('Algorithm', 'http://www.w3.org/2000/09/xmldsig#sha1')
            etree.SubElement(reference, 'DigestValue').text = digest_b64

            # Assinar usando private_key (novo modelo)
            signed_info_c14n = etree.tostring(signed_info, method='c14n', exclusive=False, with_comments=False)
            assinatura = cert_digital.private_key.sign(signed_info_c14n, padding.PKCS1v15(), hashes.SHA1())
            etree.SubElement(signature, 'SignatureValue').text = base64.b64encode(assinatura).decode('ascii')

            key_info = etree.SubElement(signature, 'KeyInfo')
            x509_data = etree.SubElement(key_info, 'X509Data')
            
            # Obter certificado em PEM e converter para base64 (sem cabeçalhos)
            cert_pem, _ = cert_digital.extrair_pem()
            cert_pem_str = cert_pem.decode('ascii')
            cert_b64 = cert_pem_str.replace('-----BEGIN CERTIFICATE-----', '').replace('-----END CERTIFICATE-----', '').replace('\n', '')
            etree.SubElement(x509_data, 'X509Certificate').text = cert_b64

            xml_assinado = etree.tostring(root, encoding='unicode')
            xml_final = xml_assinado.split('?>', 1)[1].strip() if xml_assinado.startswith('<?xml') else xml_assinado
            
            print(f"[INUTILIZAÇÃO] XML assinado (500 chars): {xml_final[:500]}")
            return xml_final

        except Exception as e:
            import traceback
            print(f"[INUTILIZAÇÃO] ERRO ao assinar: {e}")
            traceback.print_exc()
            return None
