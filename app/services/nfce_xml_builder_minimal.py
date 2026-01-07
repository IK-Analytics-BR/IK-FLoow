"""
Gerador de XML para NFC-e (Modelo 65) - VERSÃO MINIMALISTA
Apenas campos OBRIGATÓRIOS conforme XSD oficial
"""

from lxml import etree
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import random
import hashlib
from typing import Dict, List, Optional


def quantize_decimal(value, places=2):
    """Arredonda decimal para N casas"""
    if value is None:
        return Decimal('0.00')
    return Decimal(str(value)).quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)


class NFCeXMLBuilderMinimal:
    """
    Construtor MINIMALISTA de XML para NFC-e (Modelo 65)
    Apenas campos obrigatórios para facilitar debug
    """
    
    NFE_NS = "http://www.portalfiscal.inf.br/nfe"
    NSMAP = {None: NFE_NS}
    
    def __init__(self, empresa: Dict, itens: List[Dict], venda: Dict):
        self.empresa = empresa
        self.itens = itens
        self.venda = venda
        self.chave_acesso = None
        self.cDV = None
        
    def _sub(self, parent, tag, text=None, **attribs):
        """Cria subelemento"""
        elem = etree.SubElement(parent, tag, **attribs)
        if text is not None:
            elem.text = str(text)
        return elem
    
    def _gerar_codigo_numerico(self):
        """Gera código numérico de 8 dígitos"""
        return str(random.randint(10000000, 99999999))
    
    def _calcular_dv(self, chave_sem_dv):
        """Calcula dígito verificador da chave de acesso"""
        peso = 2
        soma = 0
        for c in reversed(chave_sem_dv):
            soma += int(c) * peso
            peso = peso + 1 if peso < 9 else 2
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto
    
    def _gerar_chave_acesso(self, cNF, dhEmi, contingencia=None):
        """Gera chave de acesso de 44 dígitos"""
        cUF = str(self.empresa.get('codigo_uf', '50')).zfill(2)
        AAMM = dhEmi.strftime('%y%m')
        CNPJ = str(self.empresa.get('cnpj', '')).replace('.', '').replace('/', '').replace('-', '').zfill(14)
        mod = '65'
        serie = str(self.venda.get('serie_nfce', 1)).zfill(3)
        nNF = str(self.venda.get('numero_nfce', 1)).zfill(9)
        # tpEmis: 1 = Normal, 9 = Contingência Offline
        tpEmis = '9' if contingencia else '1'
        cNF_str = str(cNF).zfill(8)
        
        chave_sem_dv = f"{cUF}{AAMM}{CNPJ}{mod}{serie}{nNF}{tpEmis}{cNF_str}"
        dv = self._calcular_dv(chave_sem_dv)
        
        self.cDV = dv
        self.tpEmis = tpEmis  # Salvar para uso no _build_ide
        self.chave_acesso = chave_sem_dv + str(dv)
        return self.chave_acesso
    
    def _gerar_qrcode(self, ambiente: str, dhEmi: str = None, vNF: str = None, vICMS: str = None, digestValue: str = None):
        """Gera URL do QR Code - Versão 2
        
        IMPORTANTE: Cada estado tem seu próprio padrão de QR Code!
        
        MS (Mato Grosso do Sul) - FORMATO SIMPLIFICADO (sempre 5 campos):
            chave|versao|tpAmb|idCSC|hash
            Mesmo em contingência, usa apenas 5 campos!
            
        SP, PR, AM, CE, etc - FORMATO COMPLETO (9 campos em contingência):
            Normal: chave|versao|tpAmb|idCSC|hash (5 campos)
            Contingência: chave|versao|tpAmb|dhEmi|vNF|vICMS|digVal|idCSC|hash (9 campos)
        """
        import base64
        
        # CRÍTICO: Remover espaços de todos os campos!
        csc = str(self.empresa.get('csc_nfce', '')).strip().replace(' ', '')
        id_csc_raw = self.empresa.get('id_csc_nfce', '1')
        # idCSC - formato varia por estado
        id_csc = str(int(id_csc_raw)) if id_csc_raw else '1'
        
        # DEBUG: Mostrar valores do CSC
        print(f"[QR-DEBUG] CSC do banco: '{csc}' (len={len(csc)})")
        print(f"[QR-DEBUG] ID CSC do banco: '{id_csc_raw}' -> usado: '{id_csc}'")
        
        tpAmb = '1' if ambiente == 'producao' else '2'
        chave = str(self.chave_acesso).strip().replace(' ', '')
        nVersao = '2'
        
        # Detectar UF da empresa (primeiros 2 dígitos da chave)
        uf_codigo = chave[:2] if chave else '50'
        
        # Estados que usam formato SIMPLIFICADO (sempre 5 campos)
        # MS = 50
        ESTADOS_QR_SIMPLIFICADO = ['50']  # MS
        
        # Estados que usam formato COMPLETO (9 campos em contingência)
        # SP = 35, PR = 41, AM = 13, CE = 23, etc.
        # ESTADOS_QR_COMPLETO = ['35', '41', '13', '23']
        
        usa_formato_simplificado = uf_codigo in ESTADOS_QR_SIMPLIFICADO
        
        # URLs por estado
        urls_qrcode = {
            '50': 'http://www.dfe.ms.gov.br/nfce/qrcode',  # MS
            '35': 'https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx',  # SP
            '41': 'http://www.sefa.pr.gov.br/nfce/qrcode',  # PR
            # Adicionar outros estados conforme necessário
        }
        url_base = urls_qrcode.get(uf_codigo, 'http://www.dfe.ms.gov.br/nfce/qrcode')
        
        if usa_formato_simplificado:
            # FORMATO MS - QR Code 2.00
            # XSD exige: quando chave tem 9 na posição 35 (contingência), usar 8 campos!
            
            url_base_ms = 'http://www.dfe.ms.gov.br/nfce/qrcode'
            
            if hasattr(self, 'tpEmis') and self.tpEmis == '9':
                # CONTINGÊNCIA - QR Code V2 OFFLINE
                # Pattern XSD: chave|2|tpAmb|DIA|vNF|digVal(56)|idCSC|hash(40)
                
                # DIA da emissão (2 dígitos: 01-31)
                if dhEmi:
                    if isinstance(dhEmi, str):
                        dia = dhEmi[8:10]  # Extrai DD de YYYY-MM-DD
                    else:
                        dia = dhEmi.strftime('%d')
                else:
                    from datetime import datetime as dt
                    dia = dt.now().strftime('%d')
                
                # vNF (valor da nota)
                vNF_str = str(vNF) if vNF else '0.00'
                
                # digVal - Converter Base64 para HEX dos bytes ASCII
                # Base64 tem 28 chars, cada char → 2 hex = 56 hex!
                if digestValue:
                    # Converter cada caractere Base64 para código ASCII em HEX
                    digVal_hex = ''.join(format(ord(c), '02X') for c in digestValue)
                    print(f"[QR-DEBUG] Base64 '{digestValue}' → HEX '{digVal_hex}'")
                else:
                    digVal_hex = '0' * 56
                
                # Hash = SHA1(chave|2|tpAmb|DIA|vNF|digVal|idCSC + CSC) em HEX
                texto_hash = f"{chave}|{nVersao}|{tpAmb}|{dia}|{vNF_str}|{digVal_hex}|{id_csc}{csc}"
                hash_hex = hashlib.sha1(texto_hash.encode()).hexdigest().upper()
                
                print(f"[QR-DEBUG] MS CONTINGÊNCIA V2 OFFLINE (8 campos)")
                print(f"[QR-DEBUG] DIA={dia}, vNF={vNF_str}")
                print(f"[QR-DEBUG] digVal={digVal_hex}")
                print(f"[QR-DEBUG] Hash HEX: {hash_hex}")
                
                url_final = f"{url_base_ms}?p={chave}|{nVersao}|{tpAmb}|{dia}|{vNF_str}|{digVal_hex}|{id_csc}|{hash_hex}"
            else:
                # EMISSÃO NORMAL (5 campos conforme XSD V2 ONLINE)
                texto_hash = f"{chave}|{nVersao}|{tpAmb}|{id_csc}{csc}"
                hash_hex = hashlib.sha1(texto_hash.encode()).hexdigest().upper()
                
                print(f"[QR-DEBUG] MS NORMAL (5 campos)")
                print(f"[QR-DEBUG] Hash HEX: {hash_hex}")
                
                url_final = f"{url_base_ms}?p={chave}|{nVersao}|{tpAmb}|{id_csc}|{hash_hex}"
            
            print(f"[QR-MS] QR Code: {url_final[:100]}...")
        else:
            # FORMATO COMPLETO (SP, PR, AM, CE, etc)
            if hasattr(self, 'tpEmis') and self.tpEmis == '9':
                # Contingência: 9 campos
                # chave|versao|tpAmb|dhEmi|vNF|vICMS|digVal|idCSC|hash
                id_csc_6 = id_csc.zfill(6)  # 6 dígitos para formato completo
                
                if dhEmi:
                    dhEmi_limpo = dhEmi.replace('-', '').replace(':', '').replace('T', '')[:14]
                else:
                    from datetime import datetime
                    dhEmi_limpo = datetime.now().strftime('%Y%m%d%H%M%S')
                
                vNF_str = vNF if vNF else '0.00'
                vICMS_str = vICMS if vICMS else '0.00'
                digVal = digestValue if digestValue else ''
                
                texto_hash = f"{chave}|{nVersao}|{tpAmb}|{dhEmi_limpo}|{vNF_str}|{vICMS_str}|{digVal}|{id_csc_6}{csc}"
                hash_calc = hashlib.sha1(texto_hash.encode()).hexdigest().upper()
                
                url_final = f"{url_base}?p={chave}|{nVersao}|{tpAmb}|{dhEmi_limpo}|{vNF_str}|{vICMS_str}|{digVal}|{id_csc_6}|{hash_calc}"
                
                print(f"[QR-CONT-9] Formato COMPLETO (9 campos) para UF {uf_codigo}")
            else:
                # Normal: 5 campos
                texto_hash = f"{chave}|{nVersao}|{tpAmb}|{id_csc}{csc}"
                hash_calc = hashlib.sha1(texto_hash.encode()).hexdigest().upper()
                
                url_final = f"{url_base}?p={chave}|{nVersao}|{tpAmb}|{id_csc}|{hash_calc}"
        
        return url_final.replace(' ', '')
    
    def _get_url_chave(self, ambiente: str):
        # URL oficial MS (igual emissão normal que funciona!)
        return "http://www.dfe.ms.gov.br/nfce/consulta"
    
    def build(self, ambiente: str = 'homologacao', contingencia: dict = None) -> str:
        """Constrói o XML da NFC-e - VERSÃO MINIMALISTA
        
        Args:
            ambiente: 'homologacao' ou 'producao'
            contingencia: dict com {'dhCont': datetime, 'xJust': str} ou None para normal
        """
        self.ambiente = ambiente  # Salvar para uso no _build_det
        self.contingencia = contingencia
        
        dhEmi = datetime.now()
        cNF = self._gerar_codigo_numerico()
        chave = self._gerar_chave_acesso(cNF, dhEmi, contingencia)
        
        # Raiz
        nfe = etree.Element('NFe', nsmap=self.NSMAP)
        infNFe = self._sub(nfe, 'infNFe', versao='4.00', Id=f'NFe{chave}')
        
        # === IDE (obrigatório) ===
        self._build_ide(infNFe, cNF, dhEmi, ambiente, contingencia)
        
        # === EMIT (obrigatório) ===
        self._build_emit(infNFe)
        
        # === DET (obrigatório - pelo menos 1 item) ===
        total_produtos = Decimal('0')
        for i, item in enumerate(self.itens, 1):
            vProd = self._build_det(infNFe, item, i)
            total_produtos += vProd
        
        # === TOTAL (obrigatório) ===
        self._build_total(infNFe, total_produtos)
        
        # === TRANSP (obrigatório) ===
        self._build_transp(infNFe)
        
        # === PAG (obrigatório) ===
        self._build_pag(infNFe, total_produtos)
        
        # === infRespTec (obrigatório - erro 972) ===
        self._build_inf_resp_tec(infNFe)
        
        return etree.tostring(nfe, encoding='unicode', pretty_print=False)
    
    def adicionar_qrcode(self, xml_nfe: str, ambiente: str = 'homologacao') -> str:
        """Adiciona infNFeSupl (QR Code) - obrigatório para NFC-e
        
        Para contingência (tpEmis=9), o QR Code tem 9 campos incluindo DigestValue.
        O DigestValue é calculado aqui (SHA1 do infNFe canonizado).
        """
        import base64
        from copy import deepcopy
        
        parser = etree.XMLParser(strip_cdata=False, remove_blank_text=True)
        root = etree.fromstring(xml_nfe.encode('utf-8'), parser=parser)
        
        ns = 'http://www.portalfiscal.inf.br/nfe'
        
        # Extrair dados do XML para QR Code
        dhEmi = None
        vNF = None
        vICMS = None
        digestValue = None
        
        # Buscar dhEmi
        dhEmi_elem = root.find(f'.//{{{ns}}}dhEmi')
        if dhEmi_elem is not None and dhEmi_elem.text:
            dhEmi = dhEmi_elem.text
        
        # Buscar vNF (valor total da nota)
        vNF_elem = root.find(f'.//{{{ns}}}vNF')
        if vNF_elem is not None and vNF_elem.text:
            vNF = vNF_elem.text
        
        # Buscar vICMS (valor do ICMS)
        vICMS_elem = root.find(f'.//{{{ns}}}ICMSTot/{{{ns}}}vICMS')
        if vICMS_elem is None:
            vICMS_elem = root.find(f'.//{{{ns}}}vICMS')
        if vICMS_elem is not None and vICMS_elem.text:
            vICMS = vICMS_elem.text
        
        # Detectar UF (primeiros 2 dígitos da chave no XML)
        infNFe = root.find(f'.//{{{ns}}}infNFe')
        uf_codigo = '50'  # default MS
        if infNFe is not None:
            id_attr = infNFe.get('Id', '')
            if id_attr and len(id_attr) > 5:
                uf_codigo = id_attr[3:5]  # NFe + 2 dígitos UF
        
        # MS usa formato simplificado
        ESTADOS_QR_SIMPLIFICADO = ['50']  # MS
        usa_formato_simplificado = uf_codigo in ESTADOS_QR_SIMPLIFICADO
        
        # Para CONTINGÊNCIA (tpEmis=9), calcular DigestValue para QR Code V3
        # V3 OFFLINE usa digVal em Base64 (igual ao DigestValue da assinatura)
        if hasattr(self, 'tpEmis') and self.tpEmis == '9':
            if infNFe is not None:
                # Canonizar infNFe (C14N) - IGUAL à assinatura!
                infNFe_copy = deepcopy(infNFe)
                c14n = etree.tostring(infNFe_copy, method='c14n', exclusive=False, with_comments=False)
                # SHA-1 em Base64 - IGUAL ao DigestValue da assinatura
                digest_bytes = hashlib.sha1(c14n).digest()
                digestValue = base64.b64encode(digest_bytes).decode('ascii')
                print(f"[NFC-e] DigestValue calculado (SHA-1 Base64): {digestValue}")
                print(f"[NFC-e] Dados para QR: dhEmi={dhEmi}, vNF={vNF}")
        
        if usa_formato_simplificado and not (hasattr(self, 'tpEmis') and self.tpEmis == '9'):
            print(f"[NFC-e] UF {uf_codigo} usa formato SIMPLIFICADO (5 campos)")
        
        # Gerar URL do QR Code
        # CRÍTICO: Remover TODOS os espaços - SEFAZ rejeita espaços no CDATA!
        qrcode_url = self._gerar_qrcode(ambiente, dhEmi=dhEmi, vNF=vNF, vICMS=vICMS, digestValue=digestValue)
        qrcode_url = qrcode_url.strip().replace(' ', '')  # Remover espaços
        url_chave = self._get_url_chave(ambiente).strip()
        
        print(f"[NFC-e] QR Code gerado: {qrcode_url}")
        
        # infNFeSupl PRECISA do namespace obrigatório!
        ns = 'http://www.portalfiscal.inf.br/nfe'
        infNFeSupl = etree.SubElement(root, '{%s}infNFeSupl' % ns)
        qr = etree.SubElement(infNFeSupl, '{%s}qrCode' % ns)
        # CDATA sem espaços - NÃO pode ter espaço antes nem depois da URL!
        qr.text = etree.CDATA(qrcode_url)
        url_node = etree.SubElement(infNFeSupl, '{%s}urlChave' % ns)
        url_node.text = url_chave
        
        # Serializar XML
        xml_result = etree.tostring(root, encoding='unicode', pretty_print=False)
        
        # CORREÇÃO CRÍTICA: Remover espaços dentro do CDATA que lxml pode adicionar
        # De: <![CDATA[ http://... ]]>  Para: <![CDATA[http://...]]>
        import re
        xml_result = re.sub(r'<!\[CDATA\[\s+', '<![CDATA[', xml_result)
        xml_result = re.sub(r'\s+\]\]>', ']]>', xml_result)
        
        # CORREÇÃO OBRIGATÓRIA: infNFeSupl PRECISA declarar xmlns explicitamente!
        # O lxml herda do pai sem redeclarar, mas a SEFAZ exige declaração explícita
        xml_result = xml_result.replace('<infNFeSupl>', '<infNFeSupl xmlns="http://www.portalfiscal.inf.br/nfe">')
        
        return xml_result
    
    def _build_ide(self, parent, cNF, dhEmi, ambiente, contingencia=None):
        """Identificação da NFC-e – SOMENTE CAMPOS OBRIGATÓRIOS (XSD V4.00)
        
        ORDEM DAS TAGS É CRÍTICA! XSD rejeita se estiver fora de ordem.
        Ordem: cUF, cNF, natOp, mod, serie, nNF, dhEmi, tpNF, idDest, cMunFG,
               tpImp, tpEmis, cDV, tpAmb, finNFe, indFinal, indPres, procEmi, verProc
               [dhCont, xJust] - somente se tpEmis=9
        """
        ide = self._sub(parent, 'ide')
        
        # Tags na ordem EXATA do XSD
        self._sub(ide, 'cUF', str(self.empresa.get('codigo_uf', '50')))
        self._sub(ide, 'cNF', str(cNF).zfill(8))
        self._sub(ide, 'natOp', 'VENDA')
        self._sub(ide, 'mod', '65')
        self._sub(ide, 'serie', str(self.venda.get('serie_nfce', 1)))
        self._sub(ide, 'nNF', str(self.venda.get('numero_nfce', 1)))
        self._sub(ide, 'dhEmi', dhEmi.strftime('%Y-%m-%dT%H:%M:%S-04:00'))
        self._sub(ide, 'tpNF', '1')
        self._sub(ide, 'idDest', '1')  # sempre interno
        self._sub(ide, 'cMunFG', str(self.empresa.get('codigo_municipio', '5002704')))
        self._sub(ide, 'tpImp', '4')
        
        # NORMAL = 1 | CONTINGÊNCIA OFF-LINE = 9
        tpEmis = '9' if contingencia else '1'
        self._sub(ide, 'tpEmis', tpEmis)
        
        self._sub(ide, 'cDV', str(self.cDV))
        self._sub(ide, 'tpAmb', '1' if ambiente == 'producao' else '2')
        self._sub(ide, 'finNFe', '1')
        self._sub(ide, 'indFinal', '1')
        self._sub(ide, 'indPres', '1')
        self._sub(ide, 'procEmi', '0')  # 0 = aplicativo do contribuinte
        self._sub(ide, 'verProc', 'SupplyChain1.0')
        
        # CONTINGÊNCIA OFFLINE → obrigatórios (DEVEM VIR APÓS verProc)
        if contingencia:
            dhCont = contingencia.get('dhCont', dhEmi)
            xJust = contingencia.get('xJust', 'Problemas tecnicos - sem conexao com SEFAZ')
            self._sub(ide, 'dhCont', dhCont.strftime('%Y-%m-%dT%H:%M:%S-04:00'))
            self._sub(ide, 'xJust', xJust[:256])
    
    def _build_emit(self, parent):
        """Emitente - apenas campos obrigatórios"""
        emit = self._sub(parent, 'emit')
        
        cnpj = str(self.empresa.get('cnpj', '')).replace('.', '').replace('/', '').replace('-', '')
        self._sub(emit, 'CNPJ', cnpj.zfill(14))
        self._sub(emit, 'xNome', self.empresa.get('razao_social', '')[:60])
        
        # Endereço - apenas obrigatórios
        enderEmit = self._sub(emit, 'enderEmit')
        self._sub(enderEmit, 'xLgr', self.empresa.get('logradouro', 'RUA')[:60])
        self._sub(enderEmit, 'nro', str(self.empresa.get('numero', 'SN'))[:60])
        self._sub(enderEmit, 'xBairro', self.empresa.get('bairro', 'CENTRO')[:60])
        self._sub(enderEmit, 'cMun', str(self.empresa.get('codigo_municipio', '5002704')))
        self._sub(enderEmit, 'xMun', self.empresa.get('municipio', 'CAMPO GRANDE')[:60])
        self._sub(enderEmit, 'UF', self.empresa.get('estado', 'MS'))
        self._sub(enderEmit, 'CEP', str(self.empresa.get('cep', '')).replace('-', '').zfill(8))
        
        ie = str(self.empresa.get('inscricao_estadual', '')).replace('.', '').replace('-', '')
        self._sub(emit, 'IE', ie)
        self._sub(emit, 'CRT', '1')  # Simples Nacional
    
    def _build_det(self, parent, item: Dict, nItem: int) -> Decimal:
        """Detalhe do produto - apenas campos obrigatórios"""
        det = self._sub(parent, 'det', nItem=str(nItem))
        
        prod = self._sub(det, 'prod')
        
        codigo = str(item.get('codigo', item.get('product_id', nItem)))[:60]
        self._sub(prod, 'cProd', codigo)
        self._sub(prod, 'cEAN', 'SEM GTIN')
        
        nome = item.get('nome', item.get('product_name_snapshot', 'PRODUTO'))
        # Limpar nome: remover caracteres inválidos no início (hífen, espaços)
        nome = nome.strip().lstrip('-').lstrip('.').lstrip('*').strip()
        if not nome or len(nome) < 2:
            nome = 'PRODUTO'
        
        # Em HOMOLOGAÇÃO, primeiro item DEVE ter descrição específica (erro 373)
        if nItem == 1 and hasattr(self, 'ambiente') and self.ambiente == 'homologacao':
            nome = 'NOTA FISCAL EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL'
        
        self._sub(prod, 'xProd', nome[:120])
        self._sub(prod, 'NCM', str(item.get('ncm', '00000000')).replace('.', '').zfill(8))
        self._sub(prod, 'CFOP', '5102')
        self._sub(prod, 'uCom', 'UN')
        
        quantidade = quantize_decimal(item.get('quantidade', item.get('quantity', 1)), 4)
        self._sub(prod, 'qCom', str(quantidade))
        
        valor_unit = quantize_decimal(item.get('valor_unitario', item.get('unit_price', 0)), 4)
        self._sub(prod, 'vUnCom', str(valor_unit))
        
        vProd = quantize_decimal(quantidade * valor_unit, 2)
        self._sub(prod, 'vProd', str(vProd))
        
        self._sub(prod, 'cEANTrib', 'SEM GTIN')
        self._sub(prod, 'uTrib', 'UN')
        self._sub(prod, 'qTrib', str(quantidade))
        self._sub(prod, 'vUnTrib', str(valor_unit))
        self._sub(prod, 'indTot', '1')
        
        # Impostos - mínimo obrigatório
        imposto = self._sub(det, 'imposto')
        
        # ICMS Simples Nacional
        icms = self._sub(imposto, 'ICMS')
        icmssn = self._sub(icms, 'ICMSSN102')
        self._sub(icmssn, 'orig', '0')
        self._sub(icmssn, 'CSOSN', '102')
        
        # PIS
        pis = self._sub(imposto, 'PIS')
        pisnt = self._sub(pis, 'PISNT')
        self._sub(pisnt, 'CST', '07')
        
        # COFINS
        cofins = self._sub(imposto, 'COFINS')
        cofinsnt = self._sub(cofins, 'COFINSNT')
        self._sub(cofinsnt, 'CST', '07')
        
        return vProd
    
    def _build_total(self, parent, vProd):
        """Totais - campos obrigatórios"""
        total = self._sub(parent, 'total')
        icmsTot = self._sub(total, 'ICMSTot')
        
        self._sub(icmsTot, 'vBC', '0.00')
        self._sub(icmsTot, 'vICMS', '0.00')
        self._sub(icmsTot, 'vICMSDeson', '0.00')
        self._sub(icmsTot, 'vFCP', '0.00')
        self._sub(icmsTot, 'vBCST', '0.00')
        self._sub(icmsTot, 'vST', '0.00')
        self._sub(icmsTot, 'vFCPST', '0.00')
        self._sub(icmsTot, 'vFCPSTRet', '0.00')
        self._sub(icmsTot, 'vProd', str(quantize_decimal(vProd, 2)))
        self._sub(icmsTot, 'vFrete', '0.00')
        self._sub(icmsTot, 'vSeg', '0.00')
        self._sub(icmsTot, 'vDesc', '0.00')
        self._sub(icmsTot, 'vII', '0.00')
        self._sub(icmsTot, 'vIPI', '0.00')
        self._sub(icmsTot, 'vIPIDevol', '0.00')
        self._sub(icmsTot, 'vPIS', '0.00')
        self._sub(icmsTot, 'vCOFINS', '0.00')
        self._sub(icmsTot, 'vOutro', '0.00')
        self._sub(icmsTot, 'vNF', str(quantize_decimal(vProd, 2)))
    
    def _build_transp(self, parent):
        """Transporte - mínimo obrigatório"""
        transp = self._sub(parent, 'transp')
        self._sub(transp, 'modFrete', '9')
    
    def _build_pag(self, parent, vNF):
        """Pagamento - obrigatório"""
        pag = self._sub(parent, 'pag')
        detPag = self._sub(pag, 'detPag')
        self._sub(detPag, 'tPag', '01')
        self._sub(detPag, 'vPag', str(quantize_decimal(vNF, 2)))
    
    def _build_inf_resp_tec(self, parent):
        """Informações do Responsável Técnico - obrigatório (erro 972)
        
        IMPORTANTE: idCSRT e hashCSRT só devem ser incluídos se o CSRT estiver
        configurado separadamente do CSC. O CSRT é o código do Responsável Técnico,
        diferente do CSC que é o código do Contribuinte.
        
        Se não tiver CSRT cadastrado, NÃO incluir esses campos!
        """
        import base64
        
        infRespTec = self._sub(parent, 'infRespTec')
        
        # CNPJ do responsável técnico (IK Analytics)
        self._sub(infRespTec, 'CNPJ', '40169163000117')
        self._sub(infRespTec, 'xContato', 'Aritana Monteiro')
        self._sub(infRespTec, 'email', 'aritana@ikanalytics.com.br')
        self._sub(infRespTec, 'fone', '67999999999')
        
        # CSRT = Código de Segurança do Responsável Técnico (diferente do CSC!)
        # Só incluir idCSRT e hashCSRT se o CSRT estiver configurado SEPARADAMENTE
        csrt = str(self.empresa.get('csrt_nfce', '')).strip()
        
        if csrt and hasattr(self, 'chave_acesso'):
            # idCSRT fornecido pela SEFAZ ao desenvolvedor
            id_csrt_raw = self.empresa.get('id_csrt_nfce', '1')
            id_csrt = str(int(id_csrt_raw)).zfill(2)
            
            # hashCSRT = Base64(SHA1(CSRT + chave_acesso)) - NÃO URL-encoded!
            texto = csrt + str(self.chave_acesso)
            digest = hashlib.sha1(texto.encode()).digest()
            hash_csrt = base64.b64encode(digest).decode()
            
            self._sub(infRespTec, 'idCSRT', id_csrt)
            self._sub(infRespTec, 'hashCSRT', hash_csrt)
            print(f"[NFC-e] hashCSRT (infRespTec): {hash_csrt}")
        else:
            # Sem CSRT configurado - NÃO incluir idCSRT e hashCSRT
            print("[NFC-e] CSRT não configurado — idCSRT e hashCSRT NÃO serão incluídos no infRespTec")
    
    def get_chave_acesso(self):
        return self.chave_acesso
