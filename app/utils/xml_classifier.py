"""
Classificador rápido de XMLs de NF-e
Identifica o tipo sem fazer parse completo
"""
import xml.etree.ElementTree as ET


class XMLClassifier:
    """
    Classifica XMLs de NF-e rapidamente
    """
    
    # Namespaces
    NS_NFE = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
    
    # Códigos de eventos
    TIPO_CANCELAMENTO = '110111'
    TIPO_CARTA_CORRECAO = '110110'
    TIPO_CONFIRMACAO = '210200'
    TIPO_CIENCIA = '210210'
    TIPO_DESCONHECIMENTO = '210220'
    TIPO_NAO_REALIZACAO = '210240'
    
    @staticmethod
    def classificar(xml_path):
        """
        Classifica um XML rapidamente
        
        Args:
            xml_path (str): Caminho do XML
            
        Returns:
            dict: {
                'tipo': 'nfe' | 'cancelamento' | 'inutilizacao' | 'carta_correcao' | 'confirmacao' | 'desconhecido',
                'chave': str (se aplicável),
                'numero': str (se aplicável)
            }
        """
        try:
            # Parse rápido (só lê estrutura, não valida)
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Remover namespace para facilitar busca
            tag = root.tag
            if '}' in tag:
                ns = tag.split('}')[0] + '}'
            else:
                ns = ''
            
            # IMPORTANTE: Verificar EVENTOS primeiro (antes de NF-e)
            # Arquivos procEventoNFe.xml são eventos, não NF-e!
            if 'procEventoNFe' in root.tag or 'evento' in root.tag.lower() or root.find('.//{http://www.portalfiscal.inf.br/nfe}evento') is not None or root.find('.//{http://www.portalfiscal.inf.br/nfe}procEventoNFe') is not None:
                tipo_evento, chave = XMLClassifier._identificar_evento(root, ns)
                
                return {
                    'tipo': tipo_evento,
                    'chave': chave,
                    'numero': None
                }
            
            # Verificar se é NF-e
            if 'NFe' in root.tag or root.find('.//{http://www.portalfiscal.inf.br/nfe}NFe') is not None:
                # É uma NF-e
                chave = XMLClassifier._extrair_chave_nfe(root, ns)
                numero = XMLClassifier._extrair_numero_nfe(root, ns)
                status = XMLClassifier._verificar_status_nfe(root, ns)
                
                return {
                    'tipo': 'nfe',
                    'chave': chave,
                    'numero': numero,
                    'status': status
                }
            
            # Verificar se é inutilização
            if 'inut' in root.tag.lower() or root.find('.//{http://www.portalfiscal.inf.br/nfe}retInutNFe') is not None:
                return {
                    'tipo': 'inutilizacao',
                    'chave': None,
                    'numero': None
                }
            
            # Verificar se é procNFe (NF-e processada)
            if 'procNFe' in root.tag or root.find('.//{http://www.portalfiscal.inf.br/nfe}procNFe') is not None:
                chave = XMLClassifier._extrair_chave_nfe(root, ns)
                numero = XMLClassifier._extrair_numero_nfe(root, ns)
                status = XMLClassifier._verificar_status_nfe(root, ns)
                
                return {
                    'tipo': 'nfe',
                    'chave': chave,
                    'numero': numero,
                    'status': status
                }
            
            # Não identificado
            return {
                'tipo': 'desconhecido',
                'chave': None,
                'numero': None
            }
            
        except Exception as e:
            return {
                'tipo': 'erro',
                'chave': None,
                'numero': None,
                'erro': str(e)
            }
    
    @staticmethod
    def _extrair_chave_nfe(root, ns):
        """Extrai chave de acesso da NF-e"""
        # Tentar vários caminhos possíveis
        paths = [
            f'.//{ns}infNFe',
            './/infNFe',
            './/{http://www.portalfiscal.inf.br/nfe}infNFe'
        ]
        
        for path in paths:
            try:
                elem = root.find(path)
                if elem is not None and 'Id' in elem.attrib:
                    chave = elem.attrib['Id'].replace('NFe', '')
                    return chave
            except:
                continue
        
        return None
    
    @staticmethod
    def _extrair_numero_nfe(root, ns):
        """Extrai número da NF-e"""
        paths = [
            f'.//{ns}ide/{ns}nNF',
            './/ide/nNF',
            './/{http://www.portalfiscal.inf.br/nfe}ide/{http://www.portalfiscal.inf.br/nfe}nNF'
        ]
        
        for path in paths:
            try:
                elem = root.find(path)
                if elem is not None and elem.text:
                    return elem.text
            except:
                continue
        
        return None
    
    @staticmethod
    def _verificar_status_nfe(root, ns):
        """
        Verifica status da NF-e no protocolo
        
        Returns:
            str: 'autorizada', 'cancelada', 'denegada', 'rejeitada', 'inutilizada', None
        """
        # Procurar pelo retorno do protocolo (procNFe)
        # Tentar múltiplos caminhos possíveis
        paths_cstat = [
            # Com namespace
            f'.//{ns}protNFe/{ns}infProt/{ns}cStat',
            f'.//{ns}infProt/{ns}cStat',
            # Sem namespace
            './/protNFe/infProt/cStat',
            './/infProt/cStat',
            './/cStat',
            # Namespace explícito
            './/{http://www.portalfiscal.inf.br/nfe}protNFe/{http://www.portalfiscal.inf.br/nfe}infProt/{http://www.portalfiscal.inf.br/nfe}cStat',
            './/{http://www.portalfiscal.inf.br/nfe}infProt/{http://www.portalfiscal.inf.br/nfe}cStat',
            './/{http://www.portalfiscal.inf.br/nfe}cStat'
        ]
        
        cstat = None
        for path in paths_cstat:
            try:
                elem = root.find(path)
                if elem is not None and elem.text:
                    cstat = elem.text
                    break
            except:
                continue
        
        # Se não encontrou, tentar buscar todos os elementos cStat
        if not cstat:
            try:
                for elem in root.iter():
                    if 'cStat' in elem.tag and elem.text:
                        cstat = elem.text
                        break
            except:
                pass
        
        # Interpretar código de status
        if cstat:
            if cstat == '100':
                return 'autorizada'
            elif cstat in ['101', '151', '135']:  # Cancelada
                return 'cancelada'
            elif cstat in ['110', '301', '302']:  # Denegada
                return 'denegada'
            elif cstat in ['102']:  # Inutilizada
                return 'inutilizada'
            elif int(cstat) >= 200 and int(cstat) <= 999:  # Rejeitada
                return 'rejeitada'
        
        # Se não encontrou protocolo, buscar por evento de cancelamento no mesmo arquivo
        paths_evento_canc = [
            f'.//{ns}procEventoNFe',
            './/procEventoNFe',
            './/{http://www.portalfiscal.inf.br/nfe}procEventoNFe'
        ]
        
        for path in paths_evento_canc:
            try:
                elem = root.find(path)
                if elem is not None:
                    # Verificar se é evento de cancelamento
                    tp_evento = elem.find('.//{http://www.portalfiscal.inf.br/nfe}tpEvento')
                    if tp_evento is not None and tp_evento.text == '110111':
                        return 'cancelada'
            except:
                continue
        
        return 'autorizada'  # Padrão: se tem NF-e mas não tem status claro, assume autorizada
    
    @staticmethod
    def _identificar_evento(root, ns):
        """Identifica tipo de evento"""
        # Procurar tpEvento
        paths = [
            f'.//{ns}infEvento/{ns}tpEvento',
            './/infEvento/tpEvento',
            './/{http://www.portalfiscal.inf.br/nfe}infEvento/{http://www.portalfiscal.inf.br/nfe}tpEvento'
        ]
        
        tp_evento = None
        for path in paths:
            try:
                elem = root.find(path)
                if elem is not None and elem.text:
                    tp_evento = elem.text
                    break
            except:
                continue
        
        # Identificar tipo
        tipo = 'evento'
        if tp_evento == XMLClassifier.TIPO_CANCELAMENTO:
            tipo = 'cancelamento'
        elif tp_evento == XMLClassifier.TIPO_CARTA_CORRECAO:
            tipo = 'carta_correcao'
        elif tp_evento == XMLClassifier.TIPO_CONFIRMACAO:
            tipo = 'confirmacao'
        elif tp_evento == XMLClassifier.TIPO_CIENCIA:
            tipo = 'ciencia'
        elif tp_evento == XMLClassifier.TIPO_DESCONHECIMENTO:
            tipo = 'desconhecimento'
        elif tp_evento == XMLClassifier.TIPO_NAO_REALIZACAO:
            tipo = 'nao_realizacao'
        
        # Extrair chave da NF-e relacionada
        paths_chave = [
            f'.//{ns}infEvento/{ns}chNFe',
            './/infEvento/chNFe',
            './/{http://www.portalfiscal.inf.br/nfe}infEvento/{http://www.portalfiscal.inf.br/nfe}chNFe'
        ]
        
        chave = None
        for path in paths_chave:
            try:
                elem = root.find(path)
                if elem is not None and elem.text:
                    chave = elem.text
                    break
            except:
                continue
        
        return tipo, chave


def classificar_xml(xml_path):
    """
    Função helper para classificar um XML
    
    Args:
        xml_path (str): Caminho do XML
        
    Returns:
        dict: Informações de classificação
    """
    return XMLClassifier.classificar(xml_path)
