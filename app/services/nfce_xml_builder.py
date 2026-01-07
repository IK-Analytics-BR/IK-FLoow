"""
Gerador de XML para NFC-e (Modelo 65)
Baseado no nfe_xml_builder.py, adaptado para NFC-e
"""

from lxml import etree
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from copy import deepcopy
import random
import hashlib
import base64
from typing import Dict, List, Optional

def quantize_decimal(value, places=2):
    """Arredonda decimal para N casas"""
    if value is None:
        return Decimal('0.00')
    return Decimal(str(value)).quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)


class NFCeXMLBuilder:
    """
    Construtor de XML para NFC-e (Modelo 65)
    """
    
    NFE_NS = "http://www.portalfiscal.inf.br/nfe"
    NSMAP = {None: NFE_NS}
    
    def __init__(self, empresa: Dict, cliente: Optional[Dict], itens: List[Dict], venda: Dict):
        self.empresa = empresa
        self.cliente = cliente  # Pode ser None para NFC-e < R$ 200
        self.itens = itens
        self.venda = venda
        self.chave_acesso = None
        self.cDV = None
        self.tpEmis = '1'  # Normal por padrão
        self.dhCont = None
        self.xJust = None
        
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
    
    def _gerar_chave_acesso(self, cNF, dhEmi, contingencia=False):
        """Gera chave de acesso de 44 dígitos"""
        cUF = str(self.empresa.get('codigo_uf', '50')).zfill(2)
        AAMM = dhEmi.strftime('%y%m')
        CNPJ = str(self.empresa.get('cnpj', '')).replace('.', '').replace('/', '').replace('-', '').zfill(14)
        mod = '65'  # NFC-e
        serie = str(self.venda.get('serie_nfce', 1)).zfill(3)
        nNF = str(self.venda.get('numero_nfce', 1)).zfill(9)
        tpEmis = '9' if contingencia else '1'  # 9=Contingência, 1=Normal
        self.tpEmis = tpEmis
        cNF_str = str(cNF).zfill(8)
        
        chave_sem_dv = f"{cUF}{AAMM}{CNPJ}{mod}{serie}{nNF}{tpEmis}{cNF_str}"
        dv = self._calcular_dv(chave_sem_dv)
        
        self.cDV = dv
        self.chave_acesso = chave_sem_dv + str(dv)
        
        return self.chave_acesso
    
    def _gerar_qrcode(self, ambiente: str, dhEmi=None, vNF=None, digestValue=None):
        """
        Gera URL do QR Code para NFC-e - Versão 2.0
        Conforme NT 2016.002
        
        Para contingência (tpEmis=9): usa formato V2 OFFLINE com 8 campos
        Para emissão normal: usa formato V2 ONLINE com 5 campos
        """
        csc = self.empresa.get('csc_nfce', '')
        # ID do CSC: remover zeros à esquerda
        id_csc_raw = self.empresa.get('id_csc_nfce', '1')
        id_csc = str(int(id_csc_raw)) if id_csc_raw else '1'
        
        # tpAmb: 1=Produção, 2=Homologação
        tpAmb = '1' if ambiente == 'producao' else '2'
        
        chave = self.chave_acesso
        nVersao = '2'  # Versão 2 do QR Code
        url_base = "http://www.dfe.ms.gov.br/nfce/qrcode"
        
        if self.tpEmis == '9':
            # CONTINGÊNCIA - QR Code V2 OFFLINE (8 campos)
            # Pattern XSD: chave|2|tpAmb|DIA|vNF|digVal(56)|idCSC|hash(40)
            
            # DIA da emissão (2 dígitos: 01-31)
            if dhEmi:
                if isinstance(dhEmi, str):
                    dia = dhEmi[8:10]  # Extrai DD de YYYY-MM-DD
                else:
                    dia = dhEmi.strftime('%d')
            else:
                dia = datetime.now().strftime('%d')
            
            # vNF (valor da nota)
            vNF_str = str(vNF) if vNF else '0.00'
            
            # digVal - Converter Base64 para HEX ASCII (28 chars → 56 hex)
            if digestValue:
                digVal_hex = ''.join(format(ord(c), '02X') for c in digestValue)
            else:
                digVal_hex = '0' * 56
            
            # Hash = SHA1(chave|2|tpAmb|DIA|vNF|digVal|idCSC + CSC) em HEX
            texto_hash = f"{chave}|{nVersao}|{tpAmb}|{dia}|{vNF_str}|{digVal_hex}|{id_csc}{csc}"
            hash_hex = hashlib.sha1(texto_hash.encode()).hexdigest().upper()
            
            qr_code_url = f"{url_base}?p={chave}|{nVersao}|{tpAmb}|{dia}|{vNF_str}|{digVal_hex}|{id_csc}|{hash_hex}"
            
            print(f"[QR-DEBUG] CONTINGÊNCIA V2 OFFLINE (8 campos)")
            print(f"[QR-DEBUG] DIA={dia}, vNF={vNF_str}, digVal={digVal_hex[:20]}...")
        else:
            # EMISSÃO NORMAL - QR Code V2 ONLINE (5 campos)
            texto_hash = f"{chave}|{nVersao}|{tpAmb}|{id_csc}{csc}"
            digest = hashlib.sha1(texto_hash.encode()).hexdigest().upper()
            qr_code_url = f"{url_base}?p={chave}|{nVersao}|{tpAmb}|{id_csc}|{digest}"
        
        return qr_code_url
    
    def _get_url_chave(self, ambiente: str):
        """Retorna URL para consulta pela chave - MS oficial"""
        # URL oficial MS: www.dfe.ms.gov.br/nfce/consulta (mesma para homolog e prod)
        return "http://www.dfe.ms.gov.br/nfce/consulta"
    
    def get_chave_acesso(self):
        """Retorna a chave de acesso gerada"""
        return self.chave_acesso
    
    def build(self, ambiente: str = 'homologacao', contingencia: bool = False) -> str:
        """
        Constrói o XML da NFC-e
        
        Args:
            ambiente: 'homologacao' ou 'producao'
            contingencia: True para emissão em contingência (tpEmis=9)
        """
        self.ambiente = ambiente  # Salvar para uso no _build_det
        dhEmi = datetime.now()
        cNF = self._gerar_codigo_numerico()
        chave = self._gerar_chave_acesso(cNF, dhEmi, contingencia=contingencia)
        
        # Guardar dados para contingência
        if contingencia:
            self.dhCont = datetime.now()
            self.xJust = 'Problemas tecnicos - SEFAZ indisponivel'
        
        # Raiz
        nfe = etree.Element('NFe', nsmap=self.NSMAP)
        infNFe = self._sub(nfe, 'infNFe', versao='4.00', Id=f'NFe{chave}')
        
        # === IDE ===
        self._build_ide(infNFe, cNF, dhEmi, ambiente)
        
        # === EMIT ===
        self._build_emit(infNFe)
        
        # === DEST (opcional para NFC-e < R$ 200) ===
        if self.cliente:
            self._build_dest(infNFe, ambiente)
        
        # === DET (itens) ===
        total_produtos = Decimal('0')
        total_desconto = Decimal('0')
        total_icms = Decimal('0')
        total_trib = Decimal('0')
        
        for i, item in enumerate(self.itens, 1):
            valores = self._build_det(infNFe, item, i)
            total_produtos += valores['vProd']
            total_desconto += valores['vDesc']
            total_icms += valores['vICMS']
            total_trib += valores['vTotTrib']
        
        # === TOTAL ===
        self._build_total(infNFe, total_produtos, total_desconto, total_icms, total_trib)
        
        # === TRANSP ===
        self._build_transp(infNFe)
        
        # === PAG ===
        self._build_pag(infNFe, total_produtos - total_desconto)
        
        # === INFADIC ===
        self._build_infadic(infNFe, ambiente)
        
        # === INFRESPTEC ===
        self._build_infresptec(infNFe)
        
        # NÃO adicionar infNFeSupl aqui - será adicionado ANTES da assinatura
        # pelo método adicionar_qrcode() (ordem: infNFe → infNFeSupl → Signature)
        
        return etree.tostring(nfe, encoding='unicode', pretty_print=False)
    
    def adicionar_qrcode(self, xml_nfe: str, ambiente: str = 'homologacao') -> str:
        """Adiciona infNFeSupl (QR Code) ao XML da NFC-e ANTES da assinatura.
        Ordem final esperada pelo XSD: infNFe → infNFeSupl → Signature.
        """
        # Parser preservando CDATA
        parser = etree.XMLParser(strip_cdata=False, remove_blank_text=True)
        root = etree.fromstring(xml_nfe.encode('utf-8'), parser=parser)
        
        ns = self.NFE_NS
        infNFe = root.find(f'.//{{{ns}}}infNFe')
        
        # Extrair dados para QR Code de contingência
        dhEmi = None
        vNF = None
        digestValue = None
        
        dhEmi_elem = root.find(f'.//{{{ns}}}dhEmi')
        if dhEmi_elem is not None:
            dhEmi = dhEmi_elem.text
        
        vNF_elem = root.find(f'.//{{{ns}}}vNF')
        if vNF_elem is not None:
            vNF = vNF_elem.text
        
        # Para contingência, calcular DigestValue (SHA-1 Base64 do infNFe)
        if self.tpEmis == '9' and infNFe is not None:
            infNFe_copy = deepcopy(infNFe)
            c14n = etree.tostring(infNFe_copy, method='c14n', exclusive=False, with_comments=False)
            digest_bytes = hashlib.sha1(c14n).digest()
            digestValue = base64.b64encode(digest_bytes).decode('ascii')
            print(f"[NFC-e] DigestValue calculado (SHA-1 Base64): {digestValue}")

        # Gerar valores do QR Code - CRÍTICO: remover espaços em branco!
        qrcode_url = self._gerar_qrcode(ambiente, dhEmi=dhEmi, vNF=vNF, digestValue=digestValue).strip()
        url_chave = self._get_url_chave(ambiente).strip()

        # Criar infNFeSupl com namespace obrigatório
        infNFeSupl = etree.SubElement(root, '{%s}infNFeSupl' % ns)

        # qrCode em CDATA, SEM espaços extras
        qr = etree.SubElement(infNFeSupl, '{%s}qrCode' % ns)
        qr.text = etree.CDATA(qrcode_url)

        # urlChave simples
        url_node = etree.SubElement(infNFeSupl, '{%s}urlChave' % ns)
        url_node.text = url_chave

        # Serializar
        xml_result = etree.tostring(root, encoding='unicode', pretty_print=False)
        
        # Garantir namespace explícito no infNFeSupl
        xml_result = xml_result.replace('<infNFeSupl>', '<infNFeSupl xmlns="http://www.portalfiscal.inf.br/nfe">')
        
        return xml_result
    
    def _build_ide(self, parent, cNF, dhEmi, ambiente):
        """Identificação da NFC-e"""
        ide = self._sub(parent, 'ide')
        
        self._sub(ide, 'cUF', str(self.empresa.get('codigo_uf', '50')))
        self._sub(ide, 'cNF', str(cNF).zfill(8))
        self._sub(ide, 'natOp', self.venda.get('natureza_operacao', 'VENDA'))
        self._sub(ide, 'mod', '65')  # NFC-e
        self._sub(ide, 'serie', str(self.venda.get('serie_nfce', 1)))
        self._sub(ide, 'nNF', str(self.venda.get('numero_nfce', 1)))
        self._sub(ide, 'dhEmi', dhEmi.strftime('%Y-%m-%dT%H:%M:%S-04:00'))
        self._sub(ide, 'tpNF', '1')  # Saída
        self._sub(ide, 'idDest', '1')  # Operação interna
        self._sub(ide, 'cMunFG', str(self.empresa.get('codigo_municipio', '5002704')))
        self._sub(ide, 'tpImp', '4')  # DANFE NFC-e
        self._sub(ide, 'tpEmis', self.tpEmis)  # 1=Normal, 9=Contingência
        self._sub(ide, 'cDV', str(self.cDV))
        self._sub(ide, 'tpAmb', '1' if ambiente == 'producao' else '2')
        self._sub(ide, 'finNFe', '1')  # Normal
        self._sub(ide, 'indFinal', '1')  # Consumidor final (obrigatório NFC-e)
        self._sub(ide, 'indPres', '1')  # Presencial (obrigatório NFC-e)
        self._sub(ide, 'procEmi', '0')  # Aplicativo contribuinte
        self._sub(ide, 'verProc', 'SupplyChain1.0')
        
        # Campos obrigatórios para contingência (tpEmis=9)
        if self.tpEmis == '9' and self.dhCont:
            self._sub(ide, 'dhCont', self.dhCont.strftime('%Y-%m-%dT%H:%M:%S-04:00'))
            self._sub(ide, 'xJust', self.xJust or 'Problemas tecnicos - SEFAZ indisponivel')
        
    def _build_emit(self, parent):
        """Emitente"""
        emit = self._sub(parent, 'emit')
        
        cnpj = str(self.empresa.get('cnpj', '')).replace('.', '').replace('/', '').replace('-', '')
        self._sub(emit, 'CNPJ', cnpj.zfill(14))
        self._sub(emit, 'xNome', self.empresa.get('razao_social', '')[:60])
        
        if self.empresa.get('nome_fantasia'):
            self._sub(emit, 'xFant', self.empresa.get('nome_fantasia')[:60])
        
        # Endereço
        enderEmit = self._sub(emit, 'enderEmit')
        self._sub(enderEmit, 'xLgr', self.empresa.get('logradouro', '')[:60])
        self._sub(enderEmit, 'nro', str(self.empresa.get('numero', 'S/N'))[:60])
        if self.empresa.get('complemento'):
            self._sub(enderEmit, 'xCpl', self.empresa.get('complemento')[:60])
        self._sub(enderEmit, 'xBairro', self.empresa.get('bairro', '')[:60])
        self._sub(enderEmit, 'cMun', str(self.empresa.get('codigo_municipio', '5002704')))
        self._sub(enderEmit, 'xMun', self.empresa.get('municipio', '')[:60])
        self._sub(enderEmit, 'UF', self.empresa.get('estado', 'MS'))
        self._sub(enderEmit, 'CEP', str(self.empresa.get('cep', '')).replace('-', '').zfill(8))
        self._sub(enderEmit, 'cPais', '1058')
        self._sub(enderEmit, 'xPais', 'BRASIL')
        
        ie = str(self.empresa.get('inscricao_estadual', '')).replace('.', '').replace('-', '')
        self._sub(emit, 'IE', ie)
        
        # CRT - Código Regime Tributário (1=Simples Nacional, 2=SN Excesso, 3=Normal)
        crt = self.empresa.get('regime_tributario', '1')
        # Converter texto para código se necessário
        crt_map = {
            'simples nacional': '1',
            'simples': '1',
            'lucro presumido': '3',
            'lucro real': '3',
            'normal': '3'
        }
        if isinstance(crt, str) and crt.lower() in crt_map:
            crt = crt_map[crt.lower()]
        self._sub(emit, 'CRT', str(crt) if str(crt) in ['1', '2', '3'] else '1')
    
    def _build_dest(self, parent, ambiente):
        """Destinatário (opcional para NFC-e)
        Para NFC-e em homologação sem cliente, NÃO incluir dest.
        Se incluir dest, precisa ter CPF/CNPJ válido.
        """
        # Em homologação, não incluir dest se não tiver cliente com documento
        if not self.cliente:
            return
        
        # Verificar se tem CPF/CNPJ válido
        # O cliente pode ter campos separados 'cpf' e 'cnpj' OU campo único 'cpf_cnpj'
        cpf = str(self.cliente.get('cpf', '') or '').replace('.', '').replace('-', '')
        cnpj = str(self.cliente.get('cnpj', '') or '').replace('.', '').replace('/', '').replace('-', '')
        cpf_cnpj = str(self.cliente.get('cpf_cnpj', '') or '').replace('.', '').replace('/', '').replace('-', '')
        
        # Determinar qual documento usar
        doc = ''
        if len(cpf) == 11:
            doc = cpf
        elif len(cnpj) == 14:
            doc = cnpj
        elif len(cpf_cnpj) == 11 or len(cpf_cnpj) == 14:
            doc = cpf_cnpj
        
        # Se não tem documento válido, não incluir dest (opcional para NFC-e < R$ 200)
        if len(doc) not in [11, 14]:
            return
            
        dest = self._sub(parent, 'dest')
        
        # CPF ou CNPJ
        if len(doc) == 11:
            self._sub(dest, 'CPF', doc)
        elif len(doc) == 14:
            self._sub(dest, 'CNPJ', doc)
        
        # Nome (obrigatório em produção se identificado)
        if ambiente == 'producao':
            self._sub(dest, 'xNome', self.cliente.get('nome', 'CONSUMIDOR')[:60])
        else:
            self._sub(dest, 'xNome', 'NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL')
        
        # Indicador IE: 9 = Não contribuinte
        self._sub(dest, 'indIEDest', '9')
    
    def _build_det(self, parent, item: Dict, nItem: int) -> Dict:
        """Detalhe do produto"""
        det = self._sub(parent, 'det', nItem=str(nItem))
        
        # Produto
        prod = self._sub(det, 'prod')
        
        codigo = str(item.get('codigo', item.get('product_id', nItem)))[:60]
        self._sub(prod, 'cProd', codigo)
        
        # EAN
        ean = str(item.get('ean', item.get('barcode', ''))).strip()
        if not ean or len(ean) < 8 or not ean.isdigit():
            ean = 'SEM GTIN'
        self._sub(prod, 'cEAN', ean)
        
        # Sanitizar nome do produto (remover caracteres especiais no início)
        nome_prod = item.get('nome', item.get('product_name_snapshot', 'PRODUTO'))
        # Remover hífens, pontos, asteriscos e espaços no início
        nome_prod = nome_prod.strip().lstrip('-').lstrip('.').lstrip('*').strip()
        if not nome_prod or len(nome_prod) < 2:
            nome_prod = 'PRODUTO'
        
        # Em HOMOLOGAÇÃO, primeiro item DEVE ter descrição específica (erro 373)
        if nItem == 1 and hasattr(self, 'ambiente') and self.ambiente == 'homologacao':
            nome_prod = 'NOTA FISCAL EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL'
        
        self._sub(prod, 'xProd', nome_prod[:120])
        self._sub(prod, 'NCM', str(item.get('ncm', '00000000')).replace('.', '').zfill(8))
        
        if item.get('cest'):
            self._sub(prod, 'CEST', str(item.get('cest')).replace('.', '').zfill(7))
        
        # CFOP para NFC-e: forçar 5102 (venda interna consumidor final)
        cfop = '5102'  # Forçado para teste
        self._sub(prod, 'CFOP', cfop)
        
        unidade = str(item.get('unidade', item.get('unit_measure', 'UN')))[:6]
        self._sub(prod, 'uCom', unidade)
        
        quantidade = quantize_decimal(item.get('quantidade', item.get('quantity', 1)), 4)
        self._sub(prod, 'qCom', str(quantidade))
        
        # Valor unitário com 4 casas decimais (evita rejeição 215)
        valor_unit = quantize_decimal(item.get('valor_unitario', item.get('unit_price', 0)), 4)
        self._sub(prod, 'vUnCom', str(valor_unit))
        
        vProd = quantize_decimal(quantidade * valor_unit, 2)
        self._sub(prod, 'vProd', str(vProd))
        
        # EAN tributável
        self._sub(prod, 'cEANTrib', ean)
        self._sub(prod, 'uTrib', unidade)
        self._sub(prod, 'qTrib', str(quantidade))
        self._sub(prod, 'vUnTrib', str(valor_unit))  # 4 casas decimais
        
        # Desconto
        vDesc = quantize_decimal(item.get('desconto', item.get('discount_value', 0)), 2)
        if vDesc > 0:
            self._sub(prod, 'vDesc', str(vDesc))
        
        self._sub(prod, 'indTot', '1')
        
        # Impostos
        valores_imp = self._build_imposto(det, item, vProd)
        
        return {
            'vProd': vProd,
            'vDesc': vDesc,
            'vICMS': valores_imp['vICMS'],
            'vTotTrib': valores_imp['vTotTrib']
        }
    
    def _build_imposto(self, det, item: Dict, vProd: Decimal) -> Dict:
        """Impostos do item"""
        imposto = self._sub(det, 'imposto')
        
        # Valor aproximado tributos (Lei da Transparência)
        aliq_aprox = Decimal(str(item.get('aliquota_aprox_tributos', '18')))
        vTotTrib = quantize_decimal(vProd * aliq_aprox / 100, 2)
        self._sub(imposto, 'vTotTrib', str(vTotTrib))
        
        # ICMS
        icms = self._sub(imposto, 'ICMS')
        
        # CRT com conversão de texto para número
        crt = self.empresa.get('regime_tributario', '1')
        crt_map = {'simples nacional': '1', 'simples': '1', 'lucro presumido': '3', 'lucro real': '3', 'normal': '3'}
        if isinstance(crt, str) and crt.lower() in crt_map:
            crt = crt_map[crt.lower()]
        crt = str(crt) if str(crt) in ['1', '2', '3'] else '1'
        
        origem = str(item.get('origem_mercadoria', '0'))
        
        if crt == '1':  # Simples Nacional
            icmssn = self._sub(icms, 'ICMSSN102')
            self._sub(icmssn, 'orig', origem)
            self._sub(icmssn, 'CSOSN', '102')  # Tributada sem permissão de crédito
            vICMS = Decimal('0')
        else:
            icms00 = self._sub(icms, 'ICMS00')
            self._sub(icms00, 'orig', origem)
            self._sub(icms00, 'CST', '00')
            self._sub(icms00, 'modBC', '3')
            self._sub(icms00, 'vBC', str(vProd))
            pICMS = Decimal(str(item.get('aliquota_icms', '18')))
            self._sub(icms00, 'pICMS', str(pICMS))
            vICMS = quantize_decimal(vProd * pICMS / 100, 2)
            self._sub(icms00, 'vICMS', str(vICMS))
        
        # PIS
        pis = self._sub(imposto, 'PIS')
        pisnt = self._sub(pis, 'PISNT')
        self._sub(pisnt, 'CST', '07')  # Isento
        
        # COFINS
        cofins = self._sub(imposto, 'COFINS')
        cofinsnt = self._sub(cofins, 'COFINSNT')
        self._sub(cofinsnt, 'CST', '07')  # Isento
        
        return {'vICMS': vICMS if crt != '1' else Decimal('0'), 'vTotTrib': vTotTrib}
    
    def _build_total(self, parent, vProd, vDesc, vICMS, vTotTrib):
        """Totais - Layout específico para NFC-e (modelo 65)
        NFC-e é sempre operação INTERNA, então NÃO inclui campos de DIFAL:
        - vFCPUFDest, vICMSUFDest, vICMSUFRemet (EC 87/2015 - só para interestadual)
        """
        total = self._sub(parent, 'total')
        icmsTot = self._sub(total, 'ICMSTot')
        
        vNF = vProd - vDesc
        
        # Campos obrigatórios para NFC-e conforme layout 4.00
        self._sub(icmsTot, 'vBC', str(quantize_decimal(vProd, 2)) if vICMS > 0 else '0.00')
        self._sub(icmsTot, 'vICMS', str(quantize_decimal(vICMS, 2)))
        self._sub(icmsTot, 'vICMSDeson', '0.00')
        # NÃO incluir vFCPUFDest, vICMSUFDest, vICMSUFRemet - são para operação interestadual (NF-e)
        self._sub(icmsTot, 'vFCP', '0.00')
        self._sub(icmsTot, 'vBCST', '0.00')
        self._sub(icmsTot, 'vST', '0.00')
        self._sub(icmsTot, 'vFCPST', '0.00')
        self._sub(icmsTot, 'vFCPSTRet', '0.00')
        self._sub(icmsTot, 'vProd', str(quantize_decimal(vProd, 2)))
        self._sub(icmsTot, 'vFrete', '0.00')
        self._sub(icmsTot, 'vSeg', '0.00')
        self._sub(icmsTot, 'vDesc', str(quantize_decimal(vDesc, 2)))
        self._sub(icmsTot, 'vII', '0.00')
        self._sub(icmsTot, 'vIPI', '0.00')
        self._sub(icmsTot, 'vIPIDevol', '0.00')
        self._sub(icmsTot, 'vPIS', '0.00')
        self._sub(icmsTot, 'vCOFINS', '0.00')
        self._sub(icmsTot, 'vOutro', '0.00')
        self._sub(icmsTot, 'vNF', str(quantize_decimal(vNF, 2)))
        self._sub(icmsTot, 'vTotTrib', str(quantize_decimal(vTotTrib, 2)))
    
    def _build_transp(self, parent):
        """Transporte - Sem frete para NFC-e"""
        transp = self._sub(parent, 'transp')
        self._sub(transp, 'modFrete', '9')  # Sem frete
    
    def _build_pag(self, parent, vNF):
        """Pagamento"""
        pag = self._sub(parent, 'pag')
        detPag = self._sub(pag, 'detPag')
        
        # Forma de pagamento
        tPag = self.venda.get('forma_pagamento', '01')  # 01=Dinheiro
        self._sub(detPag, 'tPag', str(tPag).zfill(2))
        self._sub(detPag, 'vPag', str(quantize_decimal(vNF, 2)))
    
    def _build_infadic(self, parent, ambiente):
        """Informações adicionais"""
        infAdic = self._sub(parent, 'infAdic')
        
        obs = "Documento emitido por ME ou EPP optante pelo Simples Nacional."
        if ambiente != 'producao':
            obs = "EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL. " + obs
        
        self._sub(infAdic, 'infCpl', obs[:5000])
    
    def _build_infresptec(self, parent):
        """Responsável técnico"""
        infRespTec = self._sub(parent, 'infRespTec')
        self._sub(infRespTec, 'CNPJ', '40169163000117')
        self._sub(infRespTec, 'xContato', 'SUPORTE TECNICO')
        self._sub(infRespTec, 'email', 'suporte@ikanalytics.com.br')
        self._sub(infRespTec, 'fone', '6733333333')
    
    # NOTA: infNFeSupl (QR Code) é adicionado ANTES da assinatura
    # pelo método adicionar_qrcode() - ordem: infNFe → infNFeSupl → Signature
    
    def get_chave_acesso(self):
        """Retorna a chave de acesso gerada"""
        return self.chave_acesso
