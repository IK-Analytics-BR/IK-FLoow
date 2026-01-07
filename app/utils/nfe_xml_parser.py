"""
Parser de XML de NF-e (Nota Fiscal Eletrônica)
Extrai dados do XML e retorna dict Python
"""
import xml.etree.ElementTree as ET
from datetime import datetime
import re

class NFeXMLParser:
    """
    Parser para XMLs de NF-e versão 4.00
    """
    
    # Namespace padrão do XML de NF-e
    NS = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
    
    def __init__(self, xml_path=None):
        """
        Inicializa o parser com o caminho do XML (opcional)
        
        Args:
            xml_path (str, optional): Caminho completo do arquivo XML
        """
        self.xml_path = xml_path
        self.tree = None
        self.root = None
        
    def parse(self, xml_path=None):
        """
        Faz o parse do XML e extrai todos os dados
        
        Args:
            xml_path (str, optional): Caminho do XML. Se não fornecido, usa o do __init__
        
        Returns:
            dict: Dicionário com dados da nota e itens
        """
        # Se xml_path foi passado como parâmetro, usar ele
        if xml_path:
            self.xml_path = xml_path
            
        if not self.xml_path:
            raise ValueError("Caminho do XML não fornecido")
            
        try:
            # Carregar XML
            self.tree = ET.parse(self.xml_path)
            self.root = self.tree.getroot()
            
            # Extrair dados
            nota_data = self._extrair_cabecalho()
            itens_data = self._extrair_itens()
            
            return {
                'nota': nota_data,
                'itens': itens_data,
                'xml_original': self._get_xml_string()
            }
            
        except Exception as e:
            raise Exception(f"Erro ao fazer parse do XML: {str(e)}")
    
    def _find(self, element, path):
        """
        Busca elemento no XML considerando namespace
        
        Args:
            element: Elemento XML
            path (str): Caminho do elemento
            
        Returns:
            Element ou None
        """
        if element is None:
            return None
        
        # Tentar com namespace
        result = element.find(path, self.NS)
        if result is not None:
            return result
        
        # Tentar sem namespace
        result = element.find(path.replace('nfe:', ''))
        return result
    
    def _get_text(self, element, path, default=''):
        """
        Obtém texto de um elemento
        
        Args:
            element: Elemento XML
            path (str): Caminho do elemento
            default: Valor padrão se não encontrar
            
        Returns:
            str: Texto do elemento ou valor padrão
        """
        el = self._find(element, path)
        if el is not None and el.text:
            return el.text.strip()
        return default
    
    def _extrair_cabecalho(self):
        """
        Extrai dados do cabeçalho da NF-e
        
        Returns:
            dict: Dados do cabeçalho
        """
        # Localizar nó principal
        nfe = self._find(self.root, './/nfe:NFe')
        if nfe is None:
            nfe = self.root.find('.//NFe')
        
        if nfe is None:
            raise Exception("Elemento NFe não encontrado no XML. Pode ser um XML de cancelamento/inutilização.")
        
        inf_nfe = self._find(nfe, 'nfe:infNFe')
        if inf_nfe is None:
            inf_nfe = nfe.find('infNFe')
        
        if inf_nfe is None:
            raise Exception("Elemento infNFe não encontrado. XML pode estar incompleto ou corrompido.")
        
        # Extrair chave de acesso do atributo Id
        chave_acesso = inf_nfe.get('Id', '')
        if chave_acesso.startswith('NFe'):
            chave_acesso = chave_acesso[3:]  # Remove 'NFe' do início
        
        # Identificação
        ide = self._find(inf_nfe, 'nfe:ide')
        
        # Emitente
        emit = self._find(inf_nfe, 'nfe:emit')
        emit_end = self._find(emit, 'nfe:enderEmit')
        
        # Destinatário
        dest = self._find(inf_nfe, 'nfe:dest')
        dest_end = self._find(dest, 'nfe:enderDest')
        
        # Totais
        total = self._find(inf_nfe, 'nfe:total')
        icms_tot = self._find(total, 'nfe:ICMSTot')
        
        # Informações complementares
        inf_adic = self._find(inf_nfe, 'nfe:infAdic')
        
        # Montar dict
        nota = {
            # Identificação
            'chave_acesso': chave_acesso,
            'numero_nota': self._get_text(ide, 'nfe:nNF'),
            'serie': self._get_text(ide, 'nfe:serie'),
            'modelo': self._get_text(ide, 'nfe:mod'),
            'tipo_operacao': self._get_text(ide, 'nfe:tpNF'),
            'data_emissao': self._parse_datetime(self._get_text(ide, 'nfe:dhEmi')),
            'data_saida': self._parse_datetime(self._get_text(ide, 'nfe:dhSaiEnt')),
            'natureza_operacao': self._get_text(ide, 'nfe:natOp'),
            
            # Emitente
            'emit_cnpj': self._limpar_cnpj(self._get_text(emit, 'nfe:CNPJ')),
            'emit_razao_social': self._get_text(emit, 'nfe:xNome'),
            'emit_nome_fantasia': self._get_text(emit, 'nfe:xFant'),
            'emit_ie': self._get_text(emit, 'nfe:IE'),
            'emit_logradouro': self._get_text(emit_end, 'nfe:xLgr'),
            'emit_numero': self._get_text(emit_end, 'nfe:nro'),
            'emit_complemento': self._get_text(emit_end, 'nfe:xCpl'),
            'emit_bairro': self._get_text(emit_end, 'nfe:xBairro'),
            'emit_municipio': self._get_text(emit_end, 'nfe:xMun'),
            'emit_uf': self._get_text(emit_end, 'nfe:UF'),
            'emit_cep': self._get_text(emit_end, 'nfe:CEP'),
            'emit_telefone': self._get_text(emit, 'nfe:fone'),
            
            # Destinatário
            'dest_cnpj_cpf': self._limpar_cnpj(
                self._get_text(dest, 'nfe:CNPJ') or self._get_text(dest, 'nfe:CPF')
            ),
            'dest_razao_social': self._get_text(dest, 'nfe:xNome'),
            'dest_nome_fantasia': self._get_text(dest, 'nfe:xFant'),
            'dest_ie': self._get_text(dest, 'nfe:IE'),
            'dest_logradouro': self._get_text(dest_end, 'nfe:xLgr'),
            'dest_numero': self._get_text(dest_end, 'nfe:nro'),
            'dest_complemento': self._get_text(dest_end, 'nfe:xCpl'),
            'dest_bairro': self._get_text(dest_end, 'nfe:xBairro'),
            'dest_municipio': self._get_text(dest_end, 'nfe:xMun'),
            'dest_uf': self._get_text(dest_end, 'nfe:UF'),
            'dest_cep': self._get_text(dest_end, 'nfe:CEP'),
            'dest_telefone': self._get_text(dest, 'nfe:fone'),
            'dest_email': self._get_text(dest, 'nfe:email'),
            
            # Totais
            'total_produtos': self._parse_decimal(self._get_text(icms_tot, 'nfe:vProd')),
            'total_desconto': self._parse_decimal(self._get_text(icms_tot, 'nfe:vDesc')),
            'total_frete': self._parse_decimal(self._get_text(icms_tot, 'nfe:vFrete')),
            'total_seguro': self._parse_decimal(self._get_text(icms_tot, 'nfe:vSeg')),
            'total_outras_despesas': self._parse_decimal(self._get_text(icms_tot, 'nfe:vOutro')),
            'total_ipi': self._parse_decimal(self._get_text(icms_tot, 'nfe:vIPI')),
            'total_icms': self._parse_decimal(self._get_text(icms_tot, 'nfe:vICMS')),
            'total_icms_st': self._parse_decimal(self._get_text(icms_tot, 'nfe:vST')),
            'total_pis': self._parse_decimal(self._get_text(icms_tot, 'nfe:vPIS')),
            'total_cofins': self._parse_decimal(self._get_text(icms_tot, 'nfe:vCOFINS')),
            'total_nota': self._parse_decimal(self._get_text(icms_tot, 'nfe:vNF')),
            
            # Informações complementares
            'informacoes_complementares': self._get_text(inf_adic, 'nfe:infCpl'),
        }
        
        return nota
    
    def _extrair_itens(self):
        """
        Extrai dados dos itens da NF-e
        
        Returns:
            list: Lista de dicts com dados dos itens
        """
        # Localizar nó principal
        nfe = self._find(self.root, './/nfe:NFe')
        if nfe is None:
            nfe = self.root.find('.//NFe')
        
        inf_nfe = self._find(nfe, 'nfe:infNFe')
        if inf_nfe is None:
            inf_nfe = nfe.find('infNFe')
        
        # Buscar todos os itens
        dets = inf_nfe.findall('nfe:det', self.NS)
        if not dets:
            dets = inf_nfe.findall('det')
        
        itens = []
        
        for det in dets:
            # Número do item
            num_item = det.get('nItem', '0')
            
            # Produto
            prod = self._find(det, 'nfe:prod')
            
            # Impostos
            imposto = self._find(det, 'nfe:imposto')
            
            # ICMS
            icms_data = self._extrair_icms(imposto)
            
            # IPI
            ipi_data = self._extrair_ipi(imposto)
            
            # PIS
            pis_data = self._extrair_pis(imposto)
            
            # COFINS
            cofins_data = self._extrair_cofins(imposto)
            
            # Montar item
            item = {
                'numero_item': int(num_item),
                
                # Produto
                'codigo_produto': self._get_text(prod, 'nfe:cProd'),
                'codigo_ean': self._get_text(prod, 'nfe:cEAN'),
                'codigo_ean_tributavel': self._get_text(prod, 'nfe:cEANTrib'),
                'descricao': self._get_text(prod, 'nfe:xProd'),
                'ncm': self._get_text(prod, 'nfe:NCM'),
                'cest': self._get_text(prod, 'nfe:CEST'),
                'cfop': self._get_text(prod, 'nfe:CFOP'),
                'unidade_comercial': self._get_text(prod, 'nfe:uCom'),
                'unidade_tributavel': self._get_text(prod, 'nfe:uTrib'),
                
                # Quantidades e valores
                'quantidade_comercial': self._parse_decimal(self._get_text(prod, 'nfe:qCom')),
                'valor_unitario_comercial': self._parse_decimal(self._get_text(prod, 'nfe:vUnCom')),
                'quantidade_tributavel': self._parse_decimal(self._get_text(prod, 'nfe:qTrib')),
                'valor_unitario_tributavel': self._parse_decimal(self._get_text(prod, 'nfe:vUnTrib')),
                'valor_total_bruto': self._parse_decimal(self._get_text(prod, 'nfe:vProd')),
                'valor_desconto': self._parse_decimal(self._get_text(prod, 'nfe:vDesc')),
                'valor_frete': self._parse_decimal(self._get_text(prod, 'nfe:vFrete')),
                'valor_seguro': self._parse_decimal(self._get_text(prod, 'nfe:vSeg')),
                'valor_outras_despesas': self._parse_decimal(self._get_text(prod, 'nfe:vOutro')),
                'valor_total_produto': self._parse_decimal(self._get_text(prod, 'nfe:vProd')),
            }
            
            # Adicionar dados de impostos
            item.update(icms_data)
            item.update(ipi_data)
            item.update(pis_data)
            item.update(cofins_data)
            
            itens.append(item)
        
        return itens
    
    def _extrair_icms(self, imposto):
        """Extrai dados do ICMS"""
        if imposto is None:
            return {}
        
        icms = self._find(imposto, 'nfe:ICMS')
        if icms is None:
            return {}
        
        # ICMS pode ter vários tipos (ICMS00, ICMS10, etc)
        # Procurar o primeiro filho
        icms_tipo = None
        for child in icms:
            icms_tipo = child
            break
        
        if icms_tipo is None:
            return {}
        
        return {
            'icms_origem': self._get_text(icms_tipo, 'nfe:orig'),
            'icms_cst': self._get_text(icms_tipo, 'nfe:CST') or self._get_text(icms_tipo, 'nfe:CSOSN'),
            'icms_base_calculo': self._parse_decimal(self._get_text(icms_tipo, 'nfe:vBC')),
            'icms_aliquota': self._parse_decimal(self._get_text(icms_tipo, 'nfe:pICMS')),
            'icms_valor': self._parse_decimal(self._get_text(icms_tipo, 'nfe:vICMS')),
            'icms_st_base_calculo': self._parse_decimal(self._get_text(icms_tipo, 'nfe:vBCST')),
            'icms_st_aliquota': self._parse_decimal(self._get_text(icms_tipo, 'nfe:pICMSST')),
            'icms_st_valor': self._parse_decimal(self._get_text(icms_tipo, 'nfe:vICMSST')),
        }
    
    def _extrair_ipi(self, imposto):
        """Extrai dados do IPI"""
        if imposto is None:
            return {}
        
        ipi = self._find(imposto, 'nfe:IPI')
        if ipi is None:
            return {}
        
        ipi_trib = self._find(ipi, 'nfe:IPITrib')
        
        return {
            'ipi_cst': self._get_text(ipi_trib, 'nfe:CST'),
            'ipi_base_calculo': self._parse_decimal(self._get_text(ipi_trib, 'nfe:vBC')),
            'ipi_aliquota': self._parse_decimal(self._get_text(ipi_trib, 'nfe:pIPI')),
            'ipi_valor': self._parse_decimal(self._get_text(ipi_trib, 'nfe:vIPI')),
        }
    
    def _extrair_pis(self, imposto):
        """Extrai dados do PIS"""
        if imposto is None:
            return {}
        
        pis = self._find(imposto, 'nfe:PIS')
        if pis is None:
            return {}
        
        # PIS pode ter vários tipos
        pis_tipo = None
        for child in pis:
            pis_tipo = child
            break
        
        if pis_tipo is None:
            return {}
        
        return {
            'pis_cst': self._get_text(pis_tipo, 'nfe:CST'),
            'pis_base_calculo': self._parse_decimal(self._get_text(pis_tipo, 'nfe:vBC')),
            'pis_aliquota': self._parse_decimal(self._get_text(pis_tipo, 'nfe:pPIS')),
            'pis_valor': self._parse_decimal(self._get_text(pis_tipo, 'nfe:vPIS')),
        }
    
    def _extrair_cofins(self, imposto):
        """Extrai dados do COFINS"""
        if imposto is None:
            return {}
        
        cofins = self._find(imposto, 'nfe:COFINS')
        if cofins is None:
            return {}
        
        # COFINS pode ter vários tipos
        cofins_tipo = None
        for child in cofins:
            cofins_tipo = child
            break
        
        if cofins_tipo is None:
            return {}
        
        return {
            'cofins_cst': self._get_text(cofins_tipo, 'nfe:CST'),
            'cofins_base_calculo': self._parse_decimal(self._get_text(cofins_tipo, 'nfe:vBC')),
            'cofins_aliquota': self._parse_decimal(self._get_text(cofins_tipo, 'nfe:pCOFINS')),
            'cofins_valor': self._parse_decimal(self._get_text(cofins_tipo, 'nfe:vCOFINS')),
        }
    
    def _get_xml_string(self):
        """
        Retorna o XML completo como string
        
        Returns:
            str: XML original
        """
        try:
            with open(self.xml_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ''
    
    def _parse_datetime(self, dt_string):
        """
        Converte string de data/hora do XML para formato MySQL
        
        Args:
            dt_string (str): Data no formato ISO 8601
            
        Returns:
            str: Data no formato 'YYYY-MM-DD HH:MM:SS' ou None
        """
        if not dt_string:
            return None
        
        try:
            # Remover timezone se houver
            dt_string = re.sub(r'[-+]\d{2}:\d{2}$', '', dt_string)
            
            # Parse
            dt = datetime.fromisoformat(dt_string)
            
            # Retornar no formato MySQL
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return None
    
    def _parse_decimal(self, value, default=0.0):
        """
        Converte string para decimal com validação
        
        Args:
            value (str): Valor como string
            default: Valor padrão se conversão falhar
            
        Returns:
            float: Valor convertido ou valor padrão
        """
        if not value:
            return default
        
        try:
            # Converter para float
            num = float(value)
            
            # Validar se não é infinito ou NaN
            if not (num == num and abs(num) != float('inf')):
                return default
            
            return num
        except:
            return default
    
    def _limpar_cnpj(self, cnpj):
        """
        Remove formatação do CNPJ/CPF
        
        Args:
            cnpj (str): CNPJ/CPF formatado
            
        Returns:
            str: Apenas dígitos
        """
        if not cnpj:
            return ''
        
        return re.sub(r'[^\d]', '', cnpj)


# Função auxiliar para uso rápido
def parse_nfe_xml(xml_path):
    """
    Parse rápido de um XML de NF-e
    
    Args:
        xml_path (str): Caminho do arquivo XML
        
    Returns:
        dict: Dados extraídos
    """
    parser = NFeXMLParser(xml_path)
    return parser.parse()
