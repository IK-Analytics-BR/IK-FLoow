#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gerador de DANFCE (Documento Auxiliar da Nota Fiscal de Consumidor Eletrônica)
Formato cupom térmico ou A4
"""

from io import BytesIO
from lxml import etree
from datetime import datetime
from decimal import Decimal
import qrcode
import base64

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class DanfceGenerator:
    """
    Gerador de DANFCE (cupom NFC-e)
    """
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab não está instalado. Execute: pip install reportlab")
        
        self.styles = getSampleStyleSheet()
        
        # Estilos customizados para cupom
        self.title_style = ParagraphStyle(
            'DanfceTitle',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            spaceAfter=2
        )
        
        self.header_style = ParagraphStyle(
            'DanfceHeader',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=1
        )
        
        self.small_style = ParagraphStyle(
            'DanfceSmall',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=1
        )
        
        self.item_style = ParagraphStyle(
            'DanfceItem',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.black,
            alignment=TA_LEFT,
            spaceAfter=0
        )
    
    def parse_xml(self, xml_string):
        """
        Parse do XML da NFC-e
        """
        try:
            # Limpar XML - remover espaços e quebras de linha antes da declaração
            if isinstance(xml_string, bytes):
                xml_string = xml_string.decode('utf-8', errors='ignore')
            
            # Remover BOM e espaços no início
            xml_string = xml_string.strip()
            if xml_string.startswith('\ufeff'):
                xml_string = xml_string[1:]
            
            # CORRIGIR: Remover declarações XML duplicadas
            # O XML pode ter duas declarações <?xml ...?> - remover a segunda
            import re
            # Encontrar todas as declarações XML
            declaracoes = list(re.finditer(r'<\?xml[^?]*\?>', xml_string))
            if len(declaracoes) > 1:
                # Remover todas as declarações exceto a primeira
                for match in reversed(declaracoes[1:]):
                    xml_string = xml_string[:match.start()] + xml_string[match.end():]
            
            # Limpar quebras de linha extras
            xml_string = xml_string.strip()
            
            xml_bytes = xml_string.encode('utf-8')
            root = etree.fromstring(xml_bytes)
            
            # Namespace da NFe
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            # Buscar infNFe
            inf_nfe = root.find('.//nfe:infNFe', ns)
            if inf_nfe is None:
                # Tentar sem namespace
                inf_nfe = root.find('.//infNFe')
            
            ide = inf_nfe.find('.//nfe:ide', ns) if inf_nfe is not None else None
            emit = inf_nfe.find('.//nfe:emit', ns) if inf_nfe is not None else None
            dest = inf_nfe.find('.//nfe:dest', ns) if inf_nfe is not None else None
            total = inf_nfe.find('.//nfe:total/nfe:ICMSTot', ns) if inf_nfe is not None else None
            pag = inf_nfe.find('.//nfe:pag', ns) if inf_nfe is not None else None
            
            # QR Code - tentar várias formas de encontrar
            inf_supl = inf_nfe.find('.//nfe:infNFeSupl', ns) if inf_nfe is not None else None
            qr_code = None
            url_consulta = None
            
            if inf_supl is not None:
                qr_code = inf_supl.findtext('nfe:qrCode', '', ns)
                url_consulta = inf_supl.findtext('nfe:urlChave', '', ns)
            
            # Tentar sem namespace se não encontrou
            if not qr_code and inf_nfe is not None:
                inf_supl = inf_nfe.find('.//infNFeSupl')
                if inf_supl is not None:
                    qr_el = inf_supl.find('qrCode')
                    if qr_el is not None:
                        qr_code = qr_el.text
                    url_el = inf_supl.find('urlChave')
                    if url_el is not None:
                        url_consulta = url_el.text
            
            # Última tentativa: buscar no XML bruto
            if not qr_code:
                import re
                qr_match = re.search(r'<qrCode>(.*?)</qrCode>', xml_string, re.DOTALL)
                if qr_match:
                    qr_code = qr_match.group(1).strip()
                url_match = re.search(r'<urlChave>(.*?)</urlChave>', xml_string, re.DOTALL)
                if url_match:
                    url_consulta = url_match.group(1).strip()
            
            print(f"[DANFCE] QR Code encontrado: {bool(qr_code)}")
            
            # Protocolo
            prot_nfe = root.find('.//nfe:protNFe/nfe:infProt', ns)
            protocolo = prot_nfe.findtext('nfe:nProt', '', ns) if prot_nfe is not None else ''
            dh_recbto = prot_nfe.findtext('nfe:dhRecbto', '', ns) if prot_nfe is not None else ''
            
            # Itens
            dets = inf_nfe.findall('.//nfe:det', ns) if inf_nfe is not None else []
            itens = []
            for det in dets:
                prod = det.find('.//nfe:prod', ns)
                if prod is not None:
                    item = {
                        'codigo': prod.findtext('nfe:cProd', '', ns),
                        'descricao': prod.findtext('nfe:xProd', '', ns),
                        'unidade': prod.findtext('nfe:uCom', '', ns),
                        'quantidade': float(prod.findtext('nfe:qCom', '0', ns) or '0'),
                        'valor_unitario': float(prod.findtext('nfe:vUnCom', '0', ns) or '0'),
                        'valor_total': float(prod.findtext('nfe:vProd', '0', ns) or '0')
                    }
                    itens.append(item)
            
            # Formas de pagamento
            pagamentos = []
            if pag is not None:
                det_pags = pag.findall('.//nfe:detPag', ns)
                for det_pag in det_pags:
                    tp_pag = det_pag.findtext('nfe:tPag', '', ns)
                    v_pag = float(det_pag.findtext('nfe:vPag', '0', ns) or '0')
                    
                    # Mapeamento de códigos de pagamento
                    formas = {
                        '01': 'Dinheiro', '02': 'Cheque', '03': 'Cartão Crédito',
                        '04': 'Cartão Débito', '05': 'Crédito Loja', '10': 'Vale Alimentação',
                        '11': 'Vale Refeição', '12': 'Vale Presente', '13': 'Vale Combustível',
                        '15': 'Boleto Bancário', '16': 'Dep. Bancário', '17': 'PIX',
                        '18': 'Transf. Carteira Digital', '19': 'Cashback', '90': 'Sem Pagamento',
                        '99': 'Outros'
                    }
                    
                    pagamentos.append({
                        'forma': formas.get(tp_pag, f'Outros ({tp_pag})'),
                        'valor': v_pag
                    })
            
            # Helper function para extrair texto
            def get_text(element, path, default=''):
                if element is None:
                    return default
                el = element.find(path, ns)
                return el.text if el is not None and el.text else default
            
            dados = {
                'chave': inf_nfe.get('Id', '').replace('NFe', '') if inf_nfe is not None else '',
                'numero': get_text(ide, 'nfe:nNF'),
                'serie': get_text(ide, 'nfe:serie'),
                'data_emissao': get_text(ide, 'nfe:dhEmi'),
                'natureza_operacao': get_text(ide, 'nfe:natOp'),
                
                # Emitente
                'emit_razao': get_text(emit, 'nfe:xNome'),
                'emit_fantasia': get_text(emit, 'nfe:xFant'),
                'emit_cnpj': get_text(emit, 'nfe:CNPJ'),
                'emit_ie': get_text(emit, 'nfe:IE'),
                'emit_endereco': get_text(emit, './/nfe:enderEmit/nfe:xLgr'),
                'emit_numero': get_text(emit, './/nfe:enderEmit/nfe:nro'),
                'emit_bairro': get_text(emit, './/nfe:enderEmit/nfe:xBairro'),
                'emit_cidade': get_text(emit, './/nfe:enderEmit/nfe:xMun'),
                'emit_uf': get_text(emit, './/nfe:enderEmit/nfe:UF'),
                'emit_cep': get_text(emit, './/nfe:enderEmit/nfe:CEP'),
                'emit_fone': get_text(emit, './/nfe:enderEmit/nfe:fone'),
                
                # Destinatário
                'dest_nome': get_text(dest, 'nfe:xNome') if dest is not None else 'CONSUMIDOR NÃO IDENTIFICADO',
                'dest_cpf': get_text(dest, 'nfe:CPF') if dest is not None else '',
                'dest_cnpj': get_text(dest, 'nfe:CNPJ') if dest is not None else '',
                
                # Totais
                'total_produtos': float(get_text(total, 'nfe:vProd') or '0'),
                'total_desconto': float(get_text(total, 'nfe:vDesc') or '0'),
                'total_nfce': float(get_text(total, 'nfe:vNF') or '0'),
                
                # Protocolo
                'protocolo': protocolo,
                'data_autorizacao': dh_recbto,
                
                # QR Code
                'qr_code': qr_code,
                'url_consulta': url_consulta or 'http://www.dfe.ms.gov.br/nfce/consulta',
                
                # Itens e pagamentos
                'itens': itens,
                'pagamentos': pagamentos
            }
            
            return dados
            
        except Exception as e:
            print(f"[DANFCE] Erro ao fazer parse do XML: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def gerar_qrcode_image(self, qr_data, size=100):
        """Gera imagem do QR Code"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Converter para BytesIO
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            return img_buffer
        except Exception as e:
            print(f"[DANFCE] Erro ao gerar QR Code: {str(e)}")
            return None
    
    def formatar_chave(self, chave):
        """Formata chave de acesso em grupos de 4"""
        if not chave:
            return ''
        chave = chave.replace(' ', '')
        return ' '.join([chave[i:i+4] for i in range(0, len(chave), 4)])
    
    def formatar_cpf_cnpj(self, doc):
        """Formata CPF ou CNPJ"""
        if not doc:
            return ''
        doc = doc.replace('.', '').replace('-', '').replace('/', '')
        if len(doc) == 11:
            return f'{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}'
        elif len(doc) == 14:
            return f'{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}'
        return doc
    
    def formatar_data(self, data_str):
        """Formata data ISO para dd/mm/yyyy HH:MM:SS"""
        if not data_str:
            return ''
        try:
            # Formato: 2025-12-03T10:30:00-04:00
            dt = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y %H:%M:%S')
        except:
            return data_str
    
    def gerar_pdf(self, xml_string, formato='A4', logo_path=None):
        """
        Gera PDF do DANFCE
        formato: 'A4', '80mm' ou '58mm' (cupom térmico)
        logo_path: caminho para a logo da empresa (opcional)
        """
        dados = self.parse_xml(xml_string)
        
        # Adicionar logo_path aos dados
        if logo_path:
            dados['logo_path'] = logo_path
        
        # Buffer para o PDF
        buffer = BytesIO()
        
        if formato == '80mm':
            # Cupom térmico 80mm
            largura = 80 * mm
            altura = 297 * mm  # Altura máxima, será ajustada
            doc = SimpleDocTemplate(buffer, pagesize=(largura, altura),
                                    leftMargin=2*mm, rightMargin=2*mm,
                                    topMargin=2*mm, bottomMargin=2*mm)
        elif formato == '58mm':
            # Cupom térmico 58mm
            largura = 58 * mm
            altura = 297 * mm
            doc = SimpleDocTemplate(buffer, pagesize=(largura, altura),
                                    leftMargin=1*mm, rightMargin=1*mm,
                                    topMargin=2*mm, bottomMargin=2*mm)
        else:
            # A4 padrão
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                    leftMargin=15*mm, rightMargin=15*mm,
                                    topMargin=15*mm, bottomMargin=15*mm)
        
        elements = []
        
        # ===== LOGO DA EMPRESA =====
        logo_path = dados.get('logo_path')
        if logo_path:
            try:
                import os
                if os.path.exists(logo_path):
                    # Tamanho da logo baseado no formato
                    if formato == '80mm':
                        logo_width = 30*mm
                        logo_height = 15*mm
                    elif formato == '58mm':
                        logo_width = 25*mm
                        logo_height = 12*mm
                    else:
                        logo_width = 50*mm
                        logo_height = 25*mm
                    
                    logo_img = Image(logo_path, width=logo_width, height=logo_height)
                    logo_img.hAlign = 'CENTER'
                    elements.append(logo_img)
                    elements.append(Spacer(1, 2*mm))
            except Exception as e:
                print(f"[DANFCE] Erro ao carregar logo: {e}")
        
        # ===== CABEÇALHO =====
        elements.append(Paragraph("DOCUMENTO AUXILIAR DA NOTA FISCAL", self.title_style))
        elements.append(Paragraph("DE CONSUMIDOR ELETRÔNICA", self.title_style))
        elements.append(Spacer(1, 3*mm))
        
        # Dados do emitente
        emit_nome = dados.get('emit_fantasia') or dados.get('emit_razao', '')
        elements.append(Paragraph(f"<b>{emit_nome}</b>", self.header_style))
        elements.append(Paragraph(f"CNPJ: {self.formatar_cpf_cnpj(dados.get('emit_cnpj', ''))}", self.header_style))
        
        endereco = f"{dados.get('emit_endereco', '')}, {dados.get('emit_numero', '')}"
        elements.append(Paragraph(endereco, self.header_style))
        elements.append(Paragraph(f"{dados.get('emit_bairro', '')} - {dados.get('emit_cidade', '')}/{dados.get('emit_uf', '')}", self.header_style))
        elements.append(Paragraph(f"CEP: {dados.get('emit_cep', '')}", self.header_style))
        
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph("-" * 50, self.header_style))
        elements.append(Spacer(1, 2*mm))
        
        # ===== DADOS DA NOTA =====
        elements.append(Paragraph(f"<b>NFC-e Nº {dados.get('numero', '')} Série {dados.get('serie', '')}</b>", self.header_style))
        elements.append(Paragraph(f"Emissão: {self.formatar_data(dados.get('data_emissao', ''))}", self.header_style))
        
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph("-" * 50, self.header_style))
        
        # ===== CONSUMIDOR =====
        dest_doc = dados.get('dest_cpf') or dados.get('dest_cnpj', '')
        dest_nome = dados.get('dest_nome', 'CONSUMIDOR NÃO IDENTIFICADO')
        if dest_doc:
            elements.append(Paragraph(f"<b>CONSUMIDOR:</b> {dest_nome}", self.small_style))
            elements.append(Paragraph(f"CPF/CNPJ: {self.formatar_cpf_cnpj(dest_doc)}", self.small_style))
        else:
            elements.append(Paragraph("<b>CONSUMIDOR NÃO IDENTIFICADO</b>", self.header_style))
        
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph("-" * 50, self.header_style))
        
        # ===== ITENS =====
        elements.append(Paragraph("<b>ITENS</b>", self.header_style))
        elements.append(Spacer(1, 1*mm))
        
        # Cabeçalho descritivo da grade de itens
        elements.append(Paragraph("<b>ITEM CODIGO  DESCRICAO</b>", self.small_style))
        elements.append(Paragraph("<b>QTD. UN. VL.UNIT(R$) ST TAT  VL.ITEM(R$)</b>", self.small_style))
        elements.append(Spacer(1, 1*mm))
        
        # Layout em duas linhas por item (sem grade)
        for idx, item in enumerate(dados.get('itens', []), 1):
            codigo = str(item.get('codigo', ''))[:10]
            desc = item.get('descricao', '')[:30]  # Descrição
            qtd = item.get('quantidade', 0)
            unidade = item.get('unidade', 'UN')[:2]  # Limitar unidade a 2 chars
            valor_unit = item.get('valor_unitario', 0)
            valor_total = item.get('valor_total', 0)
            
            # Linha 1: Item | Código | Descrição
            linha1 = f"{idx:03d}  {codigo:<10} {desc}"
            elements.append(Paragraph(linha1, self.small_style))
            
            # Linha 2: Qtd | Unidade | Valor Unit | ST | TAT | Valor Total
            # ST e TAT como -- pois não temos esses dados no XML padrão
            linha2 = f"{qtd:>6.2f} {unidade:<2} {valor_unit:>9.2f}  --  --  {valor_total:>10.2f}"
            elements.append(Paragraph(linha2, self.small_style))
            
            elements.append(Spacer(1, 0.5*mm))
        
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph("-" * 50, self.header_style))
        
        # ===== TOTAIS =====
        elements.append(Paragraph(f"Qtd. Total de Itens: {len(dados.get('itens', []))}", self.small_style))
        elements.append(Paragraph(f"<b>Valor Total: R$ {dados.get('total_nfce', 0):.2f}</b>", self.title_style))
        
        if dados.get('total_desconto', 0) > 0:
            elements.append(Paragraph(f"Desconto: R$ {dados.get('total_desconto', 0):.2f}", self.small_style))
        
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph("-" * 50, self.header_style))
        
        # ===== FORMAS DE PAGAMENTO =====
        elements.append(Paragraph("<b>FORMAS DE PAGAMENTO</b>", self.header_style))
        for pag in dados.get('pagamentos', []):
            elements.append(Paragraph(f"{pag.get('forma', '')}: R$ {pag.get('valor', 0):.2f}", self.small_style))
        
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph("-" * 50, self.header_style))
        
        # ===== INFORMAÇÕES FISCAIS =====
        elements.append(Paragraph("<b>CONSULTE PELA CHAVE DE ACESSO</b>", self.header_style))
        elements.append(Paragraph(dados.get('url_consulta', ''), self.small_style))
        elements.append(Spacer(1, 2*mm))
        
        # Chave de acesso formatada
        chave_formatada = self.formatar_chave(dados.get('chave', ''))
        elements.append(Paragraph(f"<b>CHAVE DE ACESSO</b>", self.header_style))
        
        # Quebrar em duas linhas se necessário
        chave = dados.get('chave', '')
        if len(chave) > 22:
            elements.append(Paragraph(chave[:22], self.small_style))
            elements.append(Paragraph(chave[22:], self.small_style))
        else:
            elements.append(Paragraph(chave, self.small_style))
        
        elements.append(Spacer(1, 3*mm))
        
        # ===== QR CODE =====
        qr_data = dados.get('qr_code', '')
        if qr_data:
            qr_img = self.gerar_qrcode_image(qr_data, size=100)
            if qr_img:
                img_width = 40*mm if formato == '80mm' else 50*mm
                elements.append(Image(qr_img, width=img_width, height=img_width))
        
        elements.append(Spacer(1, 2*mm))
        
        # ===== PROTOCOLO =====
        if dados.get('protocolo'):
            elements.append(Paragraph("-" * 50, self.header_style))
            elements.append(Paragraph(f"<b>Protocolo de Autorização:</b> {dados.get('protocolo', '')}", self.small_style))
            elements.append(Paragraph(f"Data: {self.formatar_data(dados.get('data_autorizacao', ''))}", self.small_style))
        
        # Mensagem fiscal
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph("NFC-e - Documento Auxiliar da Nota Fiscal de Consumidor Eletrônica", self.small_style))
        
        # Gerar PDF
        doc.build(elements)
        
        buffer.seek(0)
        return buffer.getvalue()
    
    def gerar_pdf_from_venda(self, venda_id, db):
        """
        Gera PDF a partir do ID da venda
        """
        # Buscar XML da NFC-e
        venda = db.fetch_one("""
            SELECT xml_nfce, numero_nfce, chave_acesso_nfce
            FROM sales WHERE id = %s
        """, (venda_id,))
        
        if not venda or not venda.get('xml_nfce'):
            raise Exception(f"XML da NFC-e não encontrado para venda {venda_id}")
        
        return self.gerar_pdf(venda['xml_nfce'])
