"""
Serviço de emissão de NFC-e
Reutiliza NFeService existente com adaptações para modelo 65
"""

from app.database import Database
from app.services.nfe_service import NFeService
# Usar versão minimalista para debug
from app.services.nfce_xml_builder_minimal import NFCeXMLBuilderMinimal as NFCeXMLBuilder
from app.services.certificado_digital import CertificadoDigital
from lxml import etree
import requests
from datetime import datetime
import re


# URLs dos Webservices NFC-e - MS
# Nota: Evento usa nfe.sefaz (não nfce.sefaz)
URLS_NFCE = {
    'homologacao': {
        'autorizacao': 'https://hom.nfce.sefaz.ms.gov.br/ws/NFeAutorizacao4',
        'retorno': 'https://hom.nfce.sefaz.ms.gov.br/ws/NFeRetAutorizacao4',
        'consulta': 'https://hom.nfce.sefaz.ms.gov.br/ws/NFeConsultaProtocolo4',
        'inutilizacao': 'https://hom.nfce.sefaz.ms.gov.br/ws/NFeInutilizacao4',
        'evento': 'https://hom.nfce.sefaz.ms.gov.br/ws/NFeRecepcaoEvento4',  # Testar nfce
        'status': 'https://hom.nfce.sefaz.ms.gov.br/ws/NFeStatusServico4',
    },
    'producao': {
        'autorizacao': 'https://nfce.sefaz.ms.gov.br/ws/NFeAutorizacao4',
        'retorno': 'https://nfce.sefaz.ms.gov.br/ws/NFeRetAutorizacao4',
        'consulta': 'https://nfce.sefaz.ms.gov.br/ws/NFeConsultaProtocolo4',
        'inutilizacao': 'https://nfce.sefaz.ms.gov.br/ws/NFeInutilizacao4',
        'evento': 'https://nfce.sefaz.ms.gov.br/ws/NFeRecepcaoEvento4',
        'status': 'https://nfce.sefaz.ms.gov.br/ws/NFeStatusServico4',
    }
}


class NFCeService:
    """
    Serviço para emissão de NFC-e
    Reutiliza métodos do NFeEmissaoService
    """
    
    def __init__(self, empresa_id: int):
        self.empresa_id = empresa_id
        self.db = Database()
        
        # Carregar empresa diretamente (evita criar múltiplas conexões)
        self.empresa = self.db.fetch_one("""
            SELECT id, nome_fantasia, razao_social, cnpj,
                   COALESCE(inscricao_estadual, 'ISENTO') as inscricao_estadual,
                   COALESCE(crt, '3') as crt, logradouro, numero, complemento,
                   bairro, cidade, estado, cep, codigo_municipio_ibge,
                   COALESCE(ambiente_nfe, '2') as ambiente_nfe
            FROM empresas WHERE id = %s
        """, (empresa_id,))
        
        if not self.empresa:
            raise Exception(f"Empresa {empresa_id} não encontrada")
        
        # Buscar campos específicos de NFC-e (CSC por ambiente)
        nfce_config = self.db.fetch_one("""
            SELECT 
                csc_nfce, id_csc_nfce,
                csc_nfce_homologacao, id_csc_nfce_homologacao,
                csc_nfce_producao, id_csc_nfce_producao,
                ambiente_nfce, regime_tributario
            FROM empresas WHERE id = %s
        """, (empresa_id,))
        
        if nfce_config:
            ambiente_nfce = nfce_config.get('ambiente_nfce', 2)
            self.empresa['ambiente_nfce'] = ambiente_nfce
            self.empresa['regime_tributario'] = nfce_config.get('regime_tributario', '1')
            
            # Selecionar CSC baseado no ambiente
            if ambiente_nfce == 1:  # Produção
                self.empresa['csc_nfce'] = nfce_config.get('csc_nfce_producao') or nfce_config.get('csc_nfce')
                self.empresa['id_csc_nfce'] = nfce_config.get('id_csc_nfce_producao') or nfce_config.get('id_csc_nfce')
            else:  # Homologação
                self.empresa['csc_nfce'] = nfce_config.get('csc_nfce_homologacao') or nfce_config.get('csc_nfce')
                self.empresa['id_csc_nfce'] = nfce_config.get('id_csc_nfce_homologacao') or nfce_config.get('id_csc_nfce')
        
        # Detectar ambiente NFC-e (separado do NF-e)
        ambiente_nfce = self.empresa.get('ambiente_nfce', 2)
        self.ambiente = 'producao' if str(ambiente_nfce) == '1' else 'homologacao'
        self.urls = URLS_NFCE[self.ambiente]
        
        # Adicionar codigo_uf baseado no estado
        estado = self.empresa.get('estado', 'MS')
        uf_codigos = {'MS': '50', 'SP': '35', 'RJ': '33', 'MG': '31', 'PR': '41', 'SC': '42', 'RS': '43'}
        self.empresa['codigo_uf'] = uf_codigos.get(estado, '50')
        self.empresa['codigo_municipio'] = self.empresa.get('codigo_municipio_ibge', '5002704')
        
        # Garantir que municipio está preenchido
        if not self.empresa.get('municipio'):
            self.empresa['municipio'] = self.empresa.get('cidade', 'CAMPO GRANDE')
        
        self.cert_service = None
        self.cert_path = None
        self.key_path = None
        self._nfe_service = None  # Lazy load
        
        print(f"[NFC-e] Empresa: {self.empresa.get('nome_fantasia')}")
        print(f"[NFC-e] Ambiente: {self.ambiente}")
        csc = self.empresa.get('csc_nfce', '')
        print(f"[NFC-e] CSC: {csc[:10] if csc else 'NAO CONFIGURADO'}...")
    
    @property
    def nfe_service(self):
        """Lazy load do NFeService para evitar conexões desnecessárias"""
        if self._nfe_service is None:
            self._nfe_service = NFeService()
        return self._nfe_service
    
    def _preparar_certificado(self):
        """Prepara certificado para mTLS"""
        self.cert_service = CertificadoDigital(self.empresa_id)
        self.cert_service.carregar_do_banco()
        
        # Salvar PEM temporários usando método da classe
        self.cert_path, self.key_path = self.cert_service.salvar_pem_temporario(f'nfce_{self.empresa_id}')
        
        return (self.cert_path, self.key_path)
    
    def _limpar_certificado(self):
        """Remove arquivos temporários do certificado"""
        import os
        if self.cert_path and os.path.exists(self.cert_path):
            os.remove(self.cert_path)
        if self.key_path and os.path.exists(self.key_path):
            os.remove(self.key_path)
    
    def consultar_status(self) -> dict:
        """Consulta status do serviço NFC-e na SEFAZ"""
        try:
            print(f"[NFC-e] Consultando status do serviço...")
            print(f"[NFC-e] URL: {self.urls['status']}")
            
            tpAmb = '1' if self.ambiente == 'producao' else '2'
            cUF = self.empresa.get('codigo_uf', '50')
            
            xml_status = f"""<consStatServ xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
<tpAmb>{tpAmb}</tpAmb>
<cUF>{cUF}</cUF>
<xServ>STATUS</xServ>
</consStatServ>"""
            
            # Headers iguais ao SefazService (que funciona)
            headers = {
                'Content-Type': 'application/soap+xml; charset=utf-8',
                'SOAPAction': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeStatusServico4'
            }
            
            soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:nfe="http://www.portalfiscal.inf.br/nfe/wsdl/NFeStatusServico4">
  <soap:Body>
    <nfe:nfeDadosMsg>
      {xml_status}
    </nfe:nfeDadosMsg>
  </soap:Body>
</soap:Envelope>"""
            
            cert = self._preparar_certificado()
            
            try:
                print(f"[NFC-e] Enviando requisição...")
                response = requests.post(
                    self.urls['status'],
                    data=soap.encode('utf-8'),
                    headers=headers,
                    timeout=30,
                    cert=cert,
                    verify=False
                )
                
                print(f"[NFC-e] Status HTTP: {response.status_code}")
                print(f"[NFC-e] Resposta: {response.text[:300]}")
                
                if response.status_code == 200:
                    # Parsear resposta
                    root = etree.fromstring(response.content)
                    cStat = root.find('.//{http://www.portalfiscal.inf.br/nfe}cStat')
                    xMotivo = root.find('.//{http://www.portalfiscal.inf.br/nfe}xMotivo')
                    
                    if cStat is None:
                        cStat = root.find('.//cStat')
                    if xMotivo is None:
                        xMotivo = root.find('.//xMotivo')
                    
                    cStat_val = cStat.text if cStat is not None else '999'
                    xMotivo_val = xMotivo.text if xMotivo is not None else 'Erro'
                    
                    print(f"[NFC-e] Status: {cStat_val} - {xMotivo_val}")
                    
                    return {
                        'sucesso': cStat_val == '107',  # 107 = Serviço em operação
                        'cStat': cStat_val,
                        'mensagem': xMotivo_val
                    }
                else:
                    print(f"[NFC-e] Erro HTTP: {response.text}")
                    return {'sucesso': False, 'erro': f'HTTP {response.status_code}: {response.text[:200]}'}
                    
            finally:
                self._limpar_certificado()
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'erro': str(e)}
    
    def emitir(self, venda_id: int) -> dict:
        """
        Emite NFC-e para uma venda
        Reutiliza métodos do NFeEmissaoService
        """
        try:
            print(f"\n[NFC-e] Iniciando emissão para venda {venda_id}")
            
            # Carregar dados da venda usando NFeEmissaoService
            venda = self.db.fetch_one("""
                SELECT s.*, c.id as cliente_id
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.id = %s
            """, (venda_id,))
            
            if not venda:
                return {'sucesso': False, 'erro': 'Venda não encontrada'}
            
            # Carregar cliente usando método do NFeEmissaoService
            cliente = None
            if venda.get('cliente_id'):
                cliente = self.nfe_service.carregar_cliente(venda['cliente_id'])
            
            # Carregar itens usando método do NFeEmissaoService  
            itens = self.nfe_service.carregar_itens_venda(venda_id)
            
            if not itens:
                return {'sucesso': False, 'erro': 'Venda sem itens'}
            
            # Buscar próximo número NFC-e
            serie = 1
            ambiente_str = 'producao' if self.ambiente == 'producao' else 'homologacao'
            
            # Primeiro: verificar tabela de controle de numeração (inclui inutilizados)
            resultado_ctrl = self.db.fetch_one("""
                SELECT ultimo_numero FROM nfe_numeracao
                WHERE empresa_id = %s AND serie = %s AND ambiente = %s
            """, (self.empresa_id, serie, ambiente_str))
            
            # Segundo: buscar MAX da tabela sales
            resultado_sales = self.db.fetch_one("""
                SELECT MAX(CAST(numero_nfce AS UNSIGNED)) as ultimo
                FROM sales
                WHERE empresa_id = %s AND serie_nfce = %s AND numero_nfce IS NOT NULL
            """, (self.empresa_id, serie))
            
            # Usar o MAIOR entre os dois
            ultimo_ctrl = resultado_ctrl['ultimo_numero'] if resultado_ctrl and resultado_ctrl['ultimo_numero'] else 0
            ultimo_sales = resultado_sales['ultimo'] if resultado_sales and resultado_sales['ultimo'] else 0
            ultimo = max(ultimo_ctrl, ultimo_sales)
            proximo = ultimo + 1
            
            print(f"[NFC-e] Próximo número: {proximo} (ctrl={ultimo_ctrl}, sales={ultimo_sales})")
            
            # Preparar dados da venda
            venda_data = {
                'numero_nfce': proximo,
                'serie_nfce': serie,
                'natureza_operacao': 'VENDA',
                'forma_pagamento': venda.get('payment_method', '01')
            }
            
            # Preparar itens (converter formato do NFeEmissaoService para NFCeXMLBuilder)
            itens_preparados = []
            for item in itens:
                itens_preparados.append({
                    'codigo': item.get('produto_id') or item.get('codigo'),
                    'nome': item.get('descricao'),
                    'ean': item.get('ean') or 'SEM GTIN',
                    'ncm': item.get('ncm') or '00000000',
                    'cest': item.get('cest'),
                    'cfop': item.get('cfop') or '5102',
                    'unidade': item.get('unidade') or 'UN',
                    'quantidade': item.get('quantidade'),
                    'valor_unitario': item.get('valor_unitario'),
                    'desconto': 0,
                    'origem_mercadoria': '0',
                    'aliquota_icms': item.get('aliquota_icms') or 0,
                    'aliquota_aprox_tributos': 18
                })
            
            # Gerar XML base (sem assinatura, sem infNFeSupl)
            print(f"[NFC-e] Gerando XML...")
            # Versão minimalista: sem cliente (opcional para NFC-e)
            builder = NFCeXMLBuilder(self.empresa, itens_preparados, venda_data)
            xml_nfce = builder.build(self.ambiente)
            chave_acesso = builder.get_chave_acesso()
            
            print(f"[NFC-e] Chave de acesso: {chave_acesso}")
            
            # Adicionar infNFeSupl (QR Code) ANTES da assinatura
            # Ordem final exigida pelo XSD: infNFe → infNFeSupl → Signature
            print(f"[NFC-e] Adicionando QR Code...")
            xml_com_qrcode = builder.adicionar_qrcode(xml_nfce, self.ambiente)
            
            # Assinar XML já com infNFeSupl
            print(f"[NFC-e] Assinando XML...")
            self.cert_service = CertificadoDigital(self.empresa_id)
            self.cert_service.carregar_do_banco()
            xml_assinado = self.cert_service.assinar_xml(xml_com_qrcode)
            
            # Montar envelope SOAP com XML assinado completo
            envelope = self._montar_envelope(xml_assinado)
            
            # Debug: salvar XML e envelope para análise
            import tempfile
            debug_file = tempfile.gettempdir() + '/nfce_enviado.xml'
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(xml_assinado)
            print(f"[NFC-e] XML salvo em: {debug_file}")
            
            debug_envelope = tempfile.gettempdir() + '/nfce_envelope.xml'
            with open(debug_envelope, 'w', encoding='utf-8') as f:
                f.write(envelope)
            print(f"[NFC-e] Envelope salvo em: {debug_envelope}")
            
            # Enviar para SEFAZ
            print(f"[NFC-e] Enviando para SEFAZ ({self.ambiente})...")
            resultado = self._enviar_sefaz(envelope)
            
            if resultado['sucesso']:
                # Criar nfeProc (XML completo com protocolo) usando XML assinado
                xml_nfeproc = self._criar_nfeproc(xml_assinado, resultado)
                
                # Atualizar venda com dados da NFC-e
                self.db.execute("""
                    UPDATE sales SET
                        numero_nfce = %s,
                        serie_nfce = %s,
                        chave_acesso_nfce = %s,
                        protocolo_nfce = %s,
                        status_nfce = 'autorizada',
                        xml_nfce = %s,
                        data_autorizacao_nfce = NOW()
                    WHERE id = %s
                """, (proximo, serie, chave_acesso, resultado['protocolo'], 
                      xml_nfeproc, venda_id))
                
                resultado['numero_nfce'] = proximo
                resultado['serie_nfce'] = serie
                resultado['chave_acesso'] = chave_acesso
                resultado['xml_nfeproc'] = xml_nfeproc
                
                print(f"[NFC-e] ✅ Autorizada! Número: {proximo}, Protocolo: {resultado['protocolo']}")
            else:
                print(f"[NFC-e] ❌ Rejeitada: {resultado.get('erro')}")
            
            return resultado
            
        except Exception as e:
            import traceback
            print(f"[NFC-e] Erro: {str(e)}")
            traceback.print_exc()
            return {'sucesso': False, 'erro': str(e)}
        finally:
            self._limpar_certificado()
    
    def _criar_nfeproc(self, xml_nfe: str, resultado: dict) -> str:
        """Cria o nfeProc (XML autorizado com protocolo)"""
        try:
            dhRecbto = datetime.now().strftime('%Y-%m-%dT%H:%M:%S-04:00')
            tpAmb = '1' if self.ambiente == 'producao' else '2'
            
            # Remover declaração XML do xml_nfe para evitar duplicação
            xml_nfe_limpo = re.sub(r'<\?xml[^?]*\?>\s*', '', xml_nfe)
            
            # Extrair chave do XML
            nfe_root = etree.fromstring(xml_nfe.encode('utf-8'))
            infNFe = nfe_root.find('.//{http://www.portalfiscal.inf.br/nfe}infNFe')
            chave = infNFe.get('Id', '').replace('NFe', '') if infNFe is not None else ''
            
            # Protocolo de autorização
            protNFe = f"""<protNFe versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
<infProt>
<tpAmb>{tpAmb}</tpAmb>
<verAplic>MS_NFE_PL_009b</verAplic>
<chNFe>{chave}</chNFe>
<dhRecbto>{dhRecbto}</dhRecbto>
<nProt>{resultado.get('protocolo', '')}</nProt>
<digVal>{resultado.get('digVal', '')}</digVal>
<cStat>100</cStat>
<xMotivo>Autorizado o uso da NF-e</xMotivo>
</infProt>
</protNFe>"""
            
            # Montar nfeProc (apenas uma declaração XML no início)
            nfeproc = f"""<?xml version="1.0" encoding="UTF-8"?>
<nfeProc versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
{xml_nfe_limpo}
{protNFe}
</nfeProc>"""
            
            return nfeproc
            
        except Exception as e:
            print(f"[NFC-e] Erro ao criar nfeProc: {e}")
            return xml_nfe
    
    def _montar_envelope(self, xml_assinado: str) -> str:
        """Monta envelope SOAP para envio"""
        id_lote = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Remover declaração XML
        xml_limpo = xml_assinado.strip()
        if xml_limpo.startswith('<?xml'):
            xml_limpo = xml_limpo.split('?>', 1)[1].strip()
        
        # NÃO remover namespace da NFe! A SEFAZ exige que a NFe tenha xmlns
        
        envelope = f"""<enviNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><idLote>{id_lote}</idLote><indSinc>1</indSinc>{xml_limpo}</enviNFe>"""
        
        return envelope
    
    def _enviar_sefaz(self, envelope: str) -> dict:
        """Envia NFC-e para SEFAZ - IGUAL ao SefazService que funciona"""
        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'SOAPAction': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4'
        }
        
        # SOAP IGUAL ao SefazService que funciona - COM soap:Header!
        soap = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
  <soap:Header>
    <nfeCabecMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4">
      <cUF>50</cUF>
      <versaoDados>4.00</versaoDados>
    </nfeCabecMsg>
  </soap:Header>
  <soap:Body>
    <nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeAutorizacao4">
      {envelope}
    </nfeDadosMsg>
  </soap:Body>
</soap:Envelope>"""
        
        # DEBUG: Salvar SOAP completo para análise
        import tempfile
        import os as os_module
        soap_debug = os_module.path.join(tempfile.gettempdir(), 'soap_debug.xml')
        with open(soap_debug, 'w', encoding='utf-8') as f:
            f.write(soap)
        print(f"[NFC-e] SOAP salvo em: {soap_debug}")
        
        # Debug
        print(f"[NFC-e] URL: {self.urls['autorizacao']}")
        print(f"[NFC-e] Tamanho SOAP: {len(soap)} bytes")
        
        cert = self._preparar_certificado()
        
        try:
            response = requests.post(
                self.urls['autorizacao'],
                data=soap.encode('utf-8'),
                headers=headers,
                timeout=30,
                cert=cert,
                verify=False
            )
            
            print(f"[NFC-e] Status HTTP: {response.status_code}")
            if response.status_code != 200:
                print(f"[NFC-e] Resposta erro: {response.text[:500]}")
                
        finally:
            self._limpar_certificado()
        
        # Log da resposta para debug
        print(f"[NFC-e] Resposta SEFAZ: {response.text[:800]}")
        
        if response.status_code != 200:
            # Tentar parsear mesmo com erro para pegar mensagem
            try:
                return self._parsear_resposta(response.text)
            except:
                return {'sucesso': False, 'erro': f'HTTP {response.status_code}'}
        
        # Parsear resposta
        return self._parsear_resposta(response.text)
    
    def _parsear_resposta(self, xml_resposta: str) -> dict:
        """Parseia resposta da SEFAZ"""
        try:
            # Parser com namespaces
            root = etree.fromstring(xml_resposta.encode('utf-8'))
            
            # Definir namespaces
            ns = {
                'soap': 'http://www.w3.org/2003/05/soap-envelope',
                'nfe': 'http://www.portalfiscal.inf.br/nfe'
            }
            
            # Buscar código de status (com namespace)
            cStat = root.find('.//{http://www.portalfiscal.inf.br/nfe}cStat')
            xMotivo = root.find('.//{http://www.portalfiscal.inf.br/nfe}xMotivo')
            nProt = root.find('.//{http://www.portalfiscal.inf.br/nfe}nProt')
            digVal = root.find('.//{http://www.portalfiscal.inf.br/nfe}digVal')
            
            # Fallback sem namespace
            if cStat is None:
                cStat = root.find('.//cStat')
            if xMotivo is None:
                xMotivo = root.find('.//xMotivo')
            if nProt is None:
                nProt = root.find('.//nProt')
            if digVal is None:
                digVal = root.find('.//digVal')
            
            cStat_val = cStat.text if cStat is not None else '999'
            xMotivo_val = xMotivo.text if xMotivo is not None else 'Erro desconhecido'
            nProt_val = nProt.text if nProt is not None else None
            digVal_val = digVal.text if digVal is not None else ''
            
            print(f"[NFC-e] Resposta SEFAZ - cStat: {cStat_val}, Motivo: {xMotivo_val}")
            
            # 100 = Autorizado
            if cStat_val == '100':
                return {
                    'sucesso': True,
                    'protocolo': nProt_val,
                    'digVal': digVal_val,
                    'mensagem': xMotivo_val
                }
            # 104 = Lote processado (verificar protNFe)
            elif cStat_val == '104':
                # Buscar no protNFe (com e sem namespace)
                prot_cStat = root.find('.//{http://www.portalfiscal.inf.br/nfe}protNFe//{http://www.portalfiscal.inf.br/nfe}cStat')
                if prot_cStat is None:
                    prot_cStat = root.find('.//protNFe//cStat')
                
                prot_xMotivo = root.find('.//{http://www.portalfiscal.inf.br/nfe}protNFe//{http://www.portalfiscal.inf.br/nfe}xMotivo')
                if prot_xMotivo is None:
                    prot_xMotivo = root.find('.//protNFe//xMotivo')
                
                prot_nProt = root.find('.//{http://www.portalfiscal.inf.br/nfe}protNFe//{http://www.portalfiscal.inf.br/nfe}nProt')
                if prot_nProt is None:
                    prot_nProt = root.find('.//protNFe//nProt')
                
                prot_digVal = root.find('.//{http://www.portalfiscal.inf.br/nfe}protNFe//{http://www.portalfiscal.inf.br/nfe}digVal')
                if prot_digVal is None:
                    prot_digVal = root.find('.//protNFe//digVal')
                
                prot_cStat_val = prot_cStat.text if prot_cStat is not None else None
                print(f"[NFC-e] protNFe cStat: {prot_cStat_val}")
                
                if prot_cStat_val == '100':
                    return {
                        'sucesso': True,
                        'protocolo': prot_nProt.text if prot_nProt is not None else None,
                        'digVal': prot_digVal.text if prot_digVal is not None else '',
                        'mensagem': prot_xMotivo.text if prot_xMotivo is not None else xMotivo_val
                    }
                else:
                    return {
                        'sucesso': False,
                        'erro': f"Rejeição: {prot_cStat_val or cStat_val} - {prot_xMotivo.text if prot_xMotivo is not None else xMotivo_val}"
                    }
            else:
                return {
                    'sucesso': False,
                    'erro': f"Rejeição: {cStat_val} - {xMotivo_val}"
                }
                
        except Exception as e:
            return {'sucesso': False, 'erro': f'Erro ao parsear resposta: {str(e)}'}
    
    def _parsear_resposta_evento(self, xml_resposta: str) -> dict:
        """Parseia resposta de evento (cancelamento, etc)"""
        try:
            root = etree.fromstring(xml_resposta.encode('utf-8'))
            
            ns = 'http://www.portalfiscal.inf.br/nfe'
            
            # Primeiro: cStat do lote (retEnvEvento)
            cStat_lote = root.find(f'.//{{{ns}}}retEnvEvento/{{{ns}}}cStat')
            if cStat_lote is None:
                cStat_lote = root.find(f'.//{{{ns}}}cStat')
            cStat_lote_val = cStat_lote.text if cStat_lote is not None else '999'
            
            print(f"[NFC-e] Lote cStat: {cStat_lote_val}")
            
            # Se lote não foi processado, erro
            if cStat_lote_val != '128':
                xMotivo = root.find(f'.//{{{ns}}}xMotivo')
                return {'sucesso': False, 'erro': f"Lote rejeitado: {cStat_lote_val} - {xMotivo.text if xMotivo is not None else 'Erro'}"}
            
            # Segundo: cStat do evento individual (retEvento/infEvento)
            infEvento = root.find(f'.//{{{ns}}}retEvento/{{{ns}}}infEvento')
            if infEvento is not None:
                cStat_evento = infEvento.find(f'{{{ns}}}cStat')
                xMotivo_evento = infEvento.find(f'{{{ns}}}xMotivo')
                nProt_evento = infEvento.find(f'{{{ns}}}nProt')
                
                cStat_val = cStat_evento.text if cStat_evento is not None else '999'
                xMotivo_val = xMotivo_evento.text if xMotivo_evento is not None else 'Erro'
                nProt_val = nProt_evento.text if nProt_evento is not None else None
                
                print(f"[NFC-e] Evento cStat: {cStat_val}, Motivo: {xMotivo_val}")
                
                # 135 = Evento registrado e vinculado a NF-e
                # 155 = Cancelamento homologado fora de prazo
                if cStat_val in ('135', '155'):
                    return {
                        'sucesso': True,
                        'protocolo': nProt_val,
                        'mensagem': xMotivo_val,
                        'cStat': cStat_val
                    }
                else:
                    return {
                        'sucesso': False,
                        'erro': f"Evento rejeitado: {cStat_val} - {xMotivo_val}"
                    }
            else:
                return {'sucesso': False, 'erro': 'retEvento não encontrado na resposta'}
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'erro': f'Erro ao parsear resposta evento: {str(e)}'}
    
    def cancelar(self, venda_id: int, justificativa: str) -> dict:
        """Cancela uma NFC-e pelo ID da venda"""
        try:
            # Buscar dados da NFC-e
            venda = self.db.fetch_one("""
                SELECT chave_acesso_nfce, protocolo_nfce, numero_nfce
                FROM sales WHERE id = %s
            """, (venda_id,))
            
            if not venda or not venda.get('chave_acesso_nfce'):
                return {'sucesso': False, 'erro': 'NFC-e não encontrada para esta venda'}
            
            return self.cancelar_por_chave(venda['chave_acesso_nfce'], justificativa)
            
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}
    
    def cancelar_por_chave(self, chave_acesso: str, justificativa: str) -> dict:
        """Cancela uma NFC-e pela chave de acesso"""
        try:
            print(f"[NFC-e] Cancelando NFC-e: {chave_acesso[:20]}...")
            
            # Buscar protocolo
            venda = self.db.fetch_one("""
                SELECT id, protocolo_nfce FROM sales 
                WHERE chave_acesso_nfce = %s
            """, (chave_acesso,))
            
            if not venda or not venda.get('protocolo_nfce'):
                return {'sucesso': False, 'erro': 'Protocolo não encontrado'}
            
            protocolo = venda['protocolo_nfce']
            
            # Montar XML de cancelamento
            from datetime import datetime
            import hashlib
            
            dhEvento = datetime.now().strftime('%Y-%m-%dT%H:%M:%S-04:00')
            nSeqEvento = '1'
            tpEvento = '110111'  # Cancelamento
            
            cnpj = str(self.empresa.get('cnpj', '')).replace('.', '').replace('/', '').replace('-', '')
            
            xml_evento = f'<evento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><infEvento Id="ID{tpEvento}{chave_acesso}{nSeqEvento.zfill(2)}"><cOrgao>{self.empresa.get("codigo_uf", "50")}</cOrgao><tpAmb>{"1" if self.ambiente == "producao" else "2"}</tpAmb><CNPJ>{cnpj}</CNPJ><chNFe>{chave_acesso}</chNFe><dhEvento>{dhEvento}</dhEvento><tpEvento>{tpEvento}</tpEvento><nSeqEvento>{nSeqEvento}</nSeqEvento><verEvento>1.00</verEvento><detEvento versao="1.00"><descEvento>Cancelamento</descEvento><nProt>{protocolo}</nProt><xJust>{justificativa}</xJust></detEvento></infEvento></evento>'
            
            print(f"[NFC-e] XML Evento: {xml_evento[:200]}...")
            
            # Assinar
            self.cert_service = CertificadoDigital(self.empresa_id)
            self.cert_service.carregar_do_banco()
            xml_assinado = self.cert_service.assinar_xml(xml_evento)
            
            # Remover declaração XML do xml_assinado (evita duplicação no envelope)
            xml_assinado = re.sub(r'<\?xml[^?]*\?>', '', xml_assinado).strip()
            
            # Montar envelope (sem espaços extras)
            idLote = datetime.now().strftime('%Y%m%d%H%M%S')
            envelope = f'<envEvento xmlns="http://www.portalfiscal.inf.br/nfe" versao="1.00"><idLote>{idLote}</idLote>{xml_assinado}</envEvento>'
            
            # Enviar
            resultado = self._enviar_evento(envelope)
            
            if resultado.get('sucesso'):
                # Atualizar banco
                self.db.execute("""
                    UPDATE sales SET
                        status_nfce = 'cancelada',
                        protocolo_cancelamento_nfce = %s,
                        data_cancelamento_nfce = NOW(),
                        justificativa_cancelamento_nfce = %s
                    WHERE chave_acesso_nfce = %s
                """, (resultado.get('protocolo'), justificativa, chave_acesso))
                
                print(f"[NFC-e] ✅ Cancelada com sucesso!")
            
            return resultado
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'erro': str(e)}
    
    def _enviar_evento(self, envelope: str) -> dict:
        """Envia evento para SEFAZ"""
        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'SOAPAction': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4/nfeRecepcaoEvento'
        }
        
        # SOAP sem espaços extras
        soap = f'<?xml version="1.0" encoding="UTF-8"?><soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"><soap12:Body><nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4">{envelope}</nfeDadosMsg></soap12:Body></soap12:Envelope>'
        
        print(f"[NFC-e] URL Evento: {self.urls['evento']}")
        print(f"[NFC-e] Tamanho SOAP Evento: {len(soap)} bytes")
        
        cert = self._preparar_certificado()
        
        try:
            response = requests.post(
                self.urls['evento'],
                data=soap.encode('utf-8'),
                headers=headers,
                timeout=30,
                cert=cert,
                verify=False
            )
            print(f"[NFC-e] Status HTTP Evento: {response.status_code}")
            print(f"[NFC-e] Resposta Evento: {response.text[:500]}...")
        finally:
            self._limpar_certificado()
        
        if response.status_code != 200:
            return {'sucesso': False, 'erro': f'HTTP {response.status_code}'}
        
        return self._parsear_resposta_evento(response.text)
    
    def inutilizar(self, serie: int, numero_ini: int, numero_fim: int, justificativa: str) -> dict:
        """Inutiliza numeração de NFC-e"""
        try:
            print(f"[NFC-e] Inutilizando numeração {numero_ini}-{numero_fim}...")
            
            from datetime import datetime
            
            ano = datetime.now().strftime('%y')
            cnpj = str(self.empresa.get('cnpj', '')).replace('.', '').replace('/', '').replace('-', '')
            cUF = self.empresa.get('codigo_uf', '50')
            
            # ID: cUF + Ano + CNPJ + mod + serie + nNFIni + nNFFin
            id_inut = f"ID{cUF}{ano}{cnpj}65{str(serie).zfill(3)}{str(numero_ini).zfill(9)}{str(numero_fim).zfill(9)}"
            
            # XML sem espaços extras
            xml_inut = f'<inutNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00"><infInut Id="{id_inut}"><tpAmb>{"1" if self.ambiente == "producao" else "2"}</tpAmb><xServ>INUTILIZAR</xServ><cUF>{cUF}</cUF><ano>{ano}</ano><CNPJ>{cnpj}</CNPJ><mod>65</mod><serie>{serie}</serie><nNFIni>{numero_ini}</nNFIni><nNFFin>{numero_fim}</nNFFin><xJust>{justificativa}</xJust></infInut></inutNFe>'
            
            # Assinar
            self.cert_service = CertificadoDigital(self.empresa_id)
            self.cert_service.carregar_do_banco()
            xml_assinado = self.cert_service.assinar_xml(xml_inut)
            
            # Remover declaração XML do xml_assinado (evita duplicação no envelope)
            xml_assinado = re.sub(r'<\?xml[^?]*\?>', '', xml_assinado).strip()
            
            # Enviar
            resultado = self._enviar_inutilizacao(xml_assinado)
            
            if resultado.get('sucesso'):
                print(f"[NFC-e] ✅ Numeração inutilizada!")
            
            return resultado
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'erro': str(e)}
    
    def _enviar_inutilizacao(self, xml: str) -> dict:
        """Envia inutilização para SEFAZ"""
        headers = {
            'Content-Type': 'application/soap+xml; charset=utf-8',
            'SOAPAction': 'http://www.portalfiscal.inf.br/nfe/wsdl/NFeInutilizacao4/nfeInutilizacaoNF'
        }
        
        # SOAP sem espaços extras
        soap = f'<?xml version="1.0" encoding="UTF-8"?><soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope"><soap12:Body><nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeInutilizacao4">{xml}</nfeDadosMsg></soap12:Body></soap12:Envelope>'
        
        print(f"[NFC-e] URL Inutilização: {self.urls['inutilizacao']}")
        print(f"[NFC-e] Tamanho SOAP Inut: {len(soap)} bytes")
        
        cert = self._preparar_certificado()
        
        try:
            response = requests.post(
                self.urls['inutilizacao'],
                data=soap.encode('utf-8'),
                headers=headers,
                timeout=30,
                cert=cert,
                verify=False
            )
            print(f"[NFC-e] Status HTTP Inut: {response.status_code}")
            print(f"[NFC-e] Resposta Inut: {response.text[:500]}...")
        finally:
            self._limpar_certificado()
        
        if response.status_code != 200:
            return {'sucesso': False, 'erro': f'HTTP {response.status_code}'}
        
        return self._parsear_resposta_inut(response.text)
    
    def _parsear_resposta_inut(self, xml_resposta: str) -> dict:
        """Parseia resposta de inutilização"""
        try:
            root = etree.fromstring(xml_resposta.encode('utf-8'))
            
            # Buscar cStat e xMotivo
            cStat = root.find('.//{http://www.portalfiscal.inf.br/nfe}cStat')
            xMotivo = root.find('.//{http://www.portalfiscal.inf.br/nfe}xMotivo')
            nProt = root.find('.//{http://www.portalfiscal.inf.br/nfe}nProt')
            
            cStat_val = cStat.text if cStat is not None else '999'
            xMotivo_val = xMotivo.text if xMotivo is not None else 'Erro desconhecido'
            nProt_val = nProt.text if nProt is not None else None
            
            print(f"[NFC-e] Inut cStat: {cStat_val}, Motivo: {xMotivo_val}")
            
            # 102 = Inutilização de número homologado
            if cStat_val == '102':
                return {
                    'sucesso': True,
                    'protocolo': nProt_val,
                    'mensagem': xMotivo_val
                }
            else:
                return {
                    'sucesso': False,
                    'erro': f"Rejeição: {cStat_val} - {xMotivo_val}"
                }
                
        except Exception as e:
            return {'sucesso': False, 'erro': f'Erro ao parsear resposta inut: {str(e)}'}
    
    # ========== MÉTODOS DE CONTINGÊNCIA ==========
    
    def entrar_contingencia(self, justificativa: str = None) -> dict:
        """Ativa modo de contingência offline para NFC-e"""
        try:
            from datetime import datetime
            
            dhCont = datetime.now()
            xJust = justificativa or 'Problemas tecnicos - sem conexao com SEFAZ'
            
            # Salvar no banco
            self.db.execute("""
                UPDATE empresas SET 
                    nfce_contingencia = 1,
                    nfce_contingencia_dhcont = %s,
                    nfce_contingencia_xjust = %s
                WHERE id = %s
            """, (dhCont, xJust, self.empresa_id))
            
            print(f"[NFC-e] ⚠️ MODO CONTINGÊNCIA ATIVADO!")
            print(f"[NFC-e] Data/Hora: {dhCont}")
            print(f"[NFC-e] Justificativa: {xJust}")
            
            return {
                'sucesso': True,
                'mensagem': 'Modo contingência ativado',
                'dhCont': dhCont.isoformat(),
                'xJust': xJust
            }
            
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}
    
    def sair_contingencia(self) -> dict:
        """Desativa modo de contingência"""
        try:
            self.db.execute("""
                UPDATE empresas SET 
                    nfce_contingencia = 0,
                    nfce_contingencia_dhcont = NULL,
                    nfce_contingencia_xjust = NULL
                WHERE id = %s
            """, (self.empresa_id,))
            
            print(f"[NFC-e] ✅ Modo contingência DESATIVADO!")
            
            return {'sucesso': True, 'mensagem': 'Modo contingência desativado'}
            
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}
    
    def verificar_contingencia(self) -> dict:
        """Verifica se está em modo contingência"""
        try:
            config = self.db.fetch_one("""
                SELECT nfce_contingencia, nfce_contingencia_dhcont, nfce_contingencia_xjust
                FROM empresas WHERE id = %s
            """, (self.empresa_id,))
            
            if config and config.get('nfce_contingencia'):
                return {
                    'contingencia': True,
                    'dhCont': config.get('nfce_contingencia_dhcont'),
                    'xJust': config.get('nfce_contingencia_xjust')
                }
            
            return {'contingencia': False}
            
        except Exception as e:
            return {'contingencia': False, 'erro': str(e)}
    
    def emitir_contingencia(self, venda_id: int) -> dict:
        """Emite NFC-e em modo contingência offline - MESMO FLUXO DO EMITIR NORMAL"""
        try:
            # Verificar se está em contingência
            cont_status = self.verificar_contingencia()
            if not cont_status.get('contingencia'):
                return {'sucesso': False, 'erro': 'Empresa não está em modo contingência'}
            
            contingencia = {
                'dhCont': cont_status.get('dhCont') or datetime.now(),
                'xJust': cont_status.get('xJust') or 'Problemas tecnicos'
            }
            
            # ========== MESMO CÓDIGO DO MÉTODO emitir() ==========
            
            # Buscar venda
            venda = self.db.fetch_one("SELECT * FROM sales WHERE id = %s", (venda_id,))
            if not venda:
                return {'sucesso': False, 'erro': 'Venda não encontrada'}
            
            # Carregar itens usando método do NFeEmissaoService (IGUAL EMISSÃO NORMAL)
            itens = self.nfe_service.carregar_itens_venda(venda_id)
            
            if not itens:
                return {'sucesso': False, 'erro': 'Venda sem itens'}
            
            # Buscar próximo número NFC-e (IGUAL EMISSÃO NORMAL)
            serie = 1
            ambiente_str = 'producao' if self.ambiente == 'producao' else 'homologacao'
            
            resultado_ctrl = self.db.fetch_one("""
                SELECT ultimo_numero FROM nfe_numeracao
                WHERE empresa_id = %s AND serie = %s AND ambiente = %s
            """, (self.empresa_id, serie, ambiente_str))
            
            resultado_sales = self.db.fetch_one("""
                SELECT MAX(CAST(numero_nfce AS UNSIGNED)) as ultimo
                FROM sales
                WHERE empresa_id = %s AND serie_nfce = %s AND numero_nfce IS NOT NULL
            """, (self.empresa_id, serie))
            
            ultimo_ctrl = resultado_ctrl['ultimo_numero'] if resultado_ctrl and resultado_ctrl['ultimo_numero'] else 0
            ultimo_sales = resultado_sales['ultimo'] if resultado_sales and resultado_sales['ultimo'] else 0
            ultimo = max(ultimo_ctrl, ultimo_sales)
            proximo = ultimo + 1
            
            print(f"[NFC-e] Próximo número: {proximo} (ctrl={ultimo_ctrl}, sales={ultimo_sales})")
            
            # Preparar dados da venda (IGUAL EMISSÃO NORMAL)
            venda_data = {
                'numero_nfce': proximo,
                'serie_nfce': serie,
                'natureza_operacao': 'VENDA',
                'forma_pagamento': venda.get('payment_method', '01')
            }
            
            # Preparar itens (IGUAL EMISSÃO NORMAL)
            itens_preparados = []
            for item in itens:
                itens_preparados.append({
                    'codigo': item.get('produto_id') or item.get('codigo'),
                    'nome': item.get('descricao'),
                    'ean': item.get('ean') or 'SEM GTIN',
                    'ncm': item.get('ncm') or '00000000',
                    'cest': item.get('cest'),
                    'cfop': item.get('cfop') or '5102',
                    'unidade': item.get('unidade') or 'UN',
                    'quantidade': item.get('quantidade'),
                    'valor_unitario': item.get('valor_unitario'),
                    'desconto': 0,
                    'origem_mercadoria': '0',
                    'aliquota_icms': item.get('aliquota_icms') or 0,
                    'aliquota_aprox_tributos': 18
                })
            
            # Gerar XML (IGUAL EMISSÃO NORMAL, mas com parâmetro contingencia)
            print(f"[NFC-e] Gerando XML em CONTINGÊNCIA...")
            builder = NFCeXMLBuilder(self.empresa, itens_preparados, venda_data)
            xml_nfce = builder.build(self.ambiente, contingencia=contingencia)  # ÚNICA DIFERENÇA!
            chave_acesso = builder.get_chave_acesso()
            
            print(f"[NFC-e] Chave de acesso: {chave_acesso}")
            
            # Adicionar QR Code (IGUAL EMISSÃO NORMAL)
            print(f"[NFC-e] Adicionando QR Code...")
            xml_com_qrcode = builder.adicionar_qrcode(xml_nfce, self.ambiente)
            
            # ASSINAR XML (IGUAL EMISSÃO NORMAL QUE FUNCIONA!)
            print(f"[NFC-e] Assinando XML...")
            self.cert_service = CertificadoDigital(self.empresa_id)
            self.cert_service.carregar_do_banco()
            xml_assinado = self.cert_service.assinar_xml(xml_com_qrcode)
            
            # Montar envelope e enviar
            envelope = self._montar_envelope(xml_assinado)
            
            # Debug
            import tempfile
            debug_file = tempfile.gettempdir() + '/nfce_contingencia_enviado.xml'
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(xml_assinado)
            print(f"[NFC-e] XML salvo em: {debug_file}")
            
            # Enviar para SEFAZ
            resultado = self._enviar_sefaz(envelope)
            
            if resultado.get('sucesso'):
                # Autorizada!
                xml_nfeproc = self._criar_nfeproc(xml_assinado, resultado)
                self.db.execute("""
                    UPDATE sales SET 
                        numero_nfce = %s,
                        serie_nfce = %s,
                        chave_acesso_nfce = %s,
                        status_nfce = 'autorizada',
                        protocolo_nfce = %s,
                        xml_nfce = %s,
                        data_autorizacao_nfce = NOW()
                    WHERE id = %s
                """, (proximo, serie, chave_acesso, resultado.get('protocolo'), xml_nfeproc, venda_id))
                
                print(f"[NFC-e] ✅ NFC-e {proximo} AUTORIZADA!")
                
                return {
                    'sucesso': True,
                    'numero_nfce': proximo,
                    'chave_acesso': chave_acesso,
                    'protocolo': resultado.get('protocolo'),
                    'contingencia': True
                }
            else:
                # Falhou - salvar como pendente
                self.db.execute("""
                    UPDATE sales SET 
                        numero_nfce = %s,
                        serie_nfce = %s,
                        chave_acesso_nfce = %s,
                        status_nfce = 'contingencia',
                        xml_nfce = %s
                    WHERE id = %s
                """, (proximo, serie, chave_acesso, xml_assinado, venda_id))
                
                print(f"[NFC-e] ⚠️ NFC-e {proximo} gerada em CONTINGÊNCIA!")
                print(f"[NFC-e] Erro SEFAZ: {resultado.get('erro')}")
                
                return {
                    'sucesso': True,
                    'numero_nfce': proximo,
                    'chave_acesso': chave_acesso,
                    'contingencia': True,
                    'erro_sefaz': resultado.get('erro'),
                    'mensagem': 'NFC-e gerada em contingência - pendente de transmissão'
                }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'sucesso': False, 'erro': str(e)}
    
    def transmitir_pendentes(self) -> dict:
        """Transmite NFC-es pendentes de contingência"""
        try:
            # Buscar NFC-es em contingência
            pendentes = self.db.fetch_all("""
                SELECT id, numero_nfce, chave_acesso_nfce, xml_nfce
                FROM sales 
                WHERE empresa_id = %s AND status_nfce = 'contingencia'
                ORDER BY numero_nfce
            """, (self.empresa_id,))
            
            if not pendentes:
                return {'sucesso': True, 'mensagem': 'Nenhuma NFC-e pendente', 'transmitidas': 0}
            
            print(f"[NFC-e] Transmitindo {len(pendentes)} NFC-e(s) pendente(s)...")
            
            # Preparar certificado
            self._preparar_certificado()
            
            transmitidas = 0
            erros = []
            
            for nfce in pendentes:
                try:
                    xml = nfce.get('xml_nfce')
                    if not xml:
                        erros.append(f"NFC-e {nfce['numero_nfce']}: XML não encontrado")
                        continue
                    
                    # O XML já está assinado (salvo com assinatura)
                    print(f"[NFC-e] Transmitindo NFC-e {nfce['numero_nfce']}...")
                    
                    # Salvar XML para debug
                    import tempfile
                    debug_file = f"{tempfile.gettempdir()}/nfce_contingencia_{nfce['numero_nfce']}.xml"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(xml)
                    print(f"[NFC-e] XML salvo para debug: {debug_file}")
                    
                    # Montar envelope e enviar
                    envelope = self._montar_envelope(xml)
                    resultado = self._enviar_sefaz(envelope)
                    
                    if resultado.get('sucesso'):
                        # Atualizar para autorizada
                        self.db.execute("""
                            UPDATE sales SET 
                                status_nfce = 'autorizada',
                                protocolo_nfce = %s,
                                data_autorizacao_nfce = NOW()
                            WHERE id = %s
                        """, (resultado.get('protocolo'), nfce['id']))
                        
                        transmitidas += 1
                        print(f"[NFC-e] ✅ NFC-e {nfce['numero_nfce']} transmitida!")
                    else:
                        erros.append(f"NFC-e {nfce['numero_nfce']}: {resultado.get('erro')}")
                        
                except Exception as e:
                    erros.append(f"NFC-e {nfce['numero_nfce']}: {str(e)}")
            
            return {
                'sucesso': True,
                'transmitidas': transmitidas,
                'total': len(pendentes),
                'erros': erros if erros else None
            }
            
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}
