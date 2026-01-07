"""
Parser de Eventos de NF-e
Extrai dados de cancelamentos, inutilizações e cartas de correção
"""
import xml.etree.ElementTree as ET
from datetime import datetime
import re


class NFeEventoParser:
    """
    Parser para eventos de NF-e (cancelamento, inutilização, carta de correção)
    """
    
    # Namespace padrão
    NS = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
    
    # Tipos de eventos
    TIPO_CANCELAMENTO = '110111'
    TIPO_CARTA_CORRECAO = '110110'
    TIPO_CONFIRMACAO = '210200'
    
    def __init__(self, xml_path):
        """
        Inicializa o parser
        
        Args:
            xml_path (str): Caminho do arquivo XML
        """
        self.xml_path = xml_path
        self.tree = None
        self.root = None
        
    def parse(self):
        """
        Faz parse do XML de evento
        
        Returns:
            dict: Dados do evento ou None se não for evento
        """
        try:
            # Carregar XML
            self.tree = ET.parse(self.xml_path)
            self.root = self.tree.getroot()
            
            # Detectar tipo de documento
            tipo = self._detectar_tipo()
            
            if tipo == 'cancelamento' or tipo == 'carta_correcao':
                return self._parse_evento()
            elif tipo == 'inutilizacao':
                return self._parse_inutilizacao()
            else:
                return None
                
        except Exception as e:
            raise Exception(f"Erro ao fazer parse do evento: {str(e)}")
    
    def _detectar_tipo(self):
        """
        Detecta tipo de documento XML
        
        Returns:
            str: 'cancelamento', 'inutilizacao', 'carta_correcao' ou None
        """
        # Procurar por evento
        evento = self.root.find('.//evento') or self.root.find('.//nfe:evento', self.NS)
        if evento is not None:
            # É um evento, verificar tipo
            inf_evento = evento.find('.//infEvento') or evento.find('.//nfe:infEvento', self.NS)
            if inf_evento is not None:
                tp_evento = self._get_text(inf_evento, './/tpEvento') or self._get_text(inf_evento, './/nfe:tpEvento')
                
                if tp_evento == self.TIPO_CANCELAMENTO:
                    return 'cancelamento'
                elif tp_evento == self.TIPO_CARTA_CORRECAO:
                    return 'carta_correcao'
        
        # Procurar por inutilização
        inut = self.root.find('.//retInutNFe') or self.root.find('.//nfe:retInutNFe', self.NS)
        if inut is not None:
            return 'inutilizacao'
        
        return None
    
    def _parse_evento(self):
        """
        Parse de evento (cancelamento ou carta de correção)
        
        Returns:
            dict: Dados do evento
        """
        # Localizar elementos
        evento = self.root.find('.//evento') or self.root.find('.//nfe:evento', self.NS)
        inf_evento = evento.find('.//infEvento') or evento.find('.//nfe:infEvento', self.NS)
        det_evento = inf_evento.find('.//detEvento') or inf_evento.find('.//nfe:detEvento', self.NS)
        
        # Retorno da SEFAZ
        ret_evento = self.root.find('.//retEvento') or self.root.find('.//nfe:retEvento', self.NS)
        inf_ret = None
        if ret_evento is not None:
            inf_ret = ret_evento.find('.//infEvento') or ret_evento.find('.//nfe:infEvento', self.NS)
        
        # Extrair dados
        tp_evento = self._get_text(inf_evento, './/tpEvento') or self._get_text(inf_evento, './/nfe:tpEvento')
        
        tipo_evento = 'cancelamento' if tp_evento == self.TIPO_CANCELAMENTO else 'carta_correcao'
        
        # Chave da NF-e
        chave_nfe = self._get_text(inf_evento, './/chNFe') or self._get_text(inf_evento, './/nfe:chNFe')
        
        # Justificativa/Correção
        justificativa = ''
        if tipo_evento == 'cancelamento':
            justificativa = self._get_text(det_evento, './/xJust') or self._get_text(det_evento, './/nfe:xJust')
        else:  # carta de correção
            justificativa = self._get_text(det_evento, './/xCorrecao') or self._get_text(det_evento, './/nfe:xCorrecao')
        
        # Dados do retorno
        status_sefaz = ''
        codigo_status = ''
        motivo_status = ''
        data_autorizacao = None
        numero_protocolo = ''
        
        if inf_ret is not None:
            codigo_status = self._get_text(inf_ret, './/cStat') or self._get_text(inf_ret, './/nfe:cStat')
            motivo_status = self._get_text(inf_ret, './/xMotivo') or self._get_text(inf_ret, './/nfe:xMotivo')
            numero_protocolo = self._get_text(inf_ret, './/nProt') or self._get_text(inf_ret, './/nfe:nProt')
            
            dh_reg = self._get_text(inf_ret, './/dhRegEvento') or self._get_text(inf_ret, './/nfe:dhRegEvento')
            data_autorizacao = self._parse_datetime(dh_reg)
            
            # Status
            if codigo_status in ['135', '136', '155']:  # Códigos de sucesso
                status_sefaz = 'autorizado'
            else:
                status_sefaz = 'rejeitado'
        
        # Data do evento
        dh_evento = self._get_text(inf_evento, './/dhEvento') or self._get_text(inf_evento, './/nfe:dhEvento')
        
        # Sequencial
        n_seq = self._get_text(inf_evento, './/nSeqEvento') or self._get_text(inf_evento, './/nfe:nSeqEvento')
        
        evento_data = {
            'tipo_evento': tipo_evento,
            'codigo_evento': tp_evento,
            'chave_nfe': chave_nfe,
            'numero_protocolo': numero_protocolo,
            'data_evento': self._parse_datetime(dh_evento),
            'sequencial_evento': int(n_seq) if n_seq else None,
            'justificativa': justificativa,
            'status_sefaz': status_sefaz,
            'codigo_status': codigo_status,
            'motivo_status': motivo_status,
            'data_autorizacao': data_autorizacao,
            'xml_original': self._get_xml_string()
        }
        
        return evento_data
    
    def _parse_inutilizacao(self):
        """
        Parse de inutilização
        
        Returns:
            dict: Dados da inutilização
        """
        # Localizar elementos
        ret_inut = self.root.find('.//retInutNFe') or self.root.find('.//nfe:retInutNFe', self.NS)
        inf_inut = ret_inut.find('.//infInut') or ret_inut.find('.//nfe:infInut', self.NS)
        
        # Extrair dados
        inut_data = {
            'tipo_evento': 'inutilizacao',
            'codigo_evento': None,
            'chave_nfe': None,
            'numero_protocolo': self._get_text(inf_inut, './/nProt') or self._get_text(inf_inut, './/nfe:nProt'),
            'data_evento': None,
            'sequencial_evento': None,
            'justificativa': self._get_text(inf_inut, './/xJust') or self._get_text(inf_inut, './/nfe:xJust'),
            
            # Específicos de inutilização
            'cnpj_emitente': self._get_text(inf_inut, './/CNPJ') or self._get_text(inf_inut, './/nfe:CNPJ'),
            'serie': self._get_text(inf_inut, './/serie') or self._get_text(inf_inut, './/nfe:serie'),
            'numero_inicial': self._get_text(inf_inut, './/nNFIni') or self._get_text(inf_inut, './/nfe:nNFIni'),
            'numero_final': self._get_text(inf_inut, './/nNFFin') or self._get_text(inf_inut, './/nfe:nNFFin'),
            'ano': self._get_text(inf_inut, './/ano') or self._get_text(inf_inut, './/nfe:ano'),
            'modelo': self._get_text(inf_inut, './/mod') or self._get_text(inf_inut, './/nfe:mod'),
            
            # Status
            'status_sefaz': 'autorizado' if self._get_text(inf_inut, './/cStat') == '102' else 'rejeitado',
            'codigo_status': self._get_text(inf_inut, './/cStat') or self._get_text(inf_inut, './/nfe:cStat'),
            'motivo_status': self._get_text(inf_inut, './/xMotivo') or self._get_text(inf_inut, './/nfe:xMotivo'),
            
            # Data
            'data_autorizacao': self._parse_datetime(
                self._get_text(inf_inut, './/dhRecbto') or self._get_text(inf_inut, './/nfe:dhRecbto')
            ),
            
            'xml_original': self._get_xml_string()
        }
        
        return inut_data
    
    def _get_text(self, element, path, default=''):
        """
        Obtém texto de um elemento
        
        Args:
            element: Elemento XML
            path (str): Caminho do elemento
            default: Valor padrão
            
        Returns:
            str: Texto do elemento ou valor padrão
        """
        if element is None:
            return default
        
        el = element.find(path, self.NS)
        if el is None:
            el = element.find(path.replace('.//nfe:', './/'))
        
        if el is not None and el.text:
            return el.text.strip()
        return default
    
    def _get_xml_string(self):
        """
        Retorna XML completo como string
        
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
        Converte string de data/hora para formato MySQL
        
        Args:
            dt_string (str): Data no formato ISO 8601
            
        Returns:
            str: Data no formato 'YYYY-MM-DD HH:MM:SS' ou None
        """
        if not dt_string:
            return None
        
        try:
            # Remover timezone
            dt_string = re.sub(r'[-+]\d{2}:\d{2}$', '', dt_string)
            
            # Parse
            dt = datetime.fromisoformat(dt_string)
            
            # Retornar no formato MySQL
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return None


# Função auxiliar
def parse_nfe_evento(xml_path):
    """
    Parse rápido de um evento de NF-e
    
    Args:
        xml_path (str): Caminho do arquivo XML
        
    Returns:
        dict: Dados extraídos ou None
    """
    parser = NFeEventoParser(xml_path)
    return parser.parse()
