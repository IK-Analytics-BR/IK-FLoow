#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gerador de DANFE (Documento Auxiliar da Nota Fiscal Eletrônica)
Versão simplificada usando ReportLab
"""

from io import BytesIO
from lxml import etree
from datetime import datetime
from decimal import Decimal

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class DanfeGenerator:
    """
    Gerador de DANFE simplificado
    """
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab não está instalado. Execute: pip install reportlab")
        
        self.styles = getSampleStyleSheet()
        self.width, self.height = A4
        
        # Estilos customizados
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#000000'),
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#000000'),
            alignment=TA_LEFT
        )
        
        self.small_style = ParagraphStyle(
            'CustomSmall',
            parent=self.styles['Normal'],
            fontSize=7,
            textColor=colors.HexColor('#333333'),
            alignment=TA_LEFT
        )
    
    def parse_xml(self, xml_string):
        """
        Parse do XML da NFe
        """
        try:
            root = etree.fromstring(xml_string.encode('utf-8') if isinstance(xml_string, str) else xml_string)
            
            # Namespace da NFe
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            # Extrair dados
            inf_nfe = root.find('.//nfe:infNFe', ns)
            ide = inf_nfe.find('.//nfe:ide', ns)
            emit = inf_nfe.find('.//nfe:emit', ns)
            dest = inf_nfe.find('.//nfe:dest', ns)
            total = inf_nfe.find('.//nfe:total/nfe:ICMSTot', ns)
            
            # Itens
            dets = inf_nfe.findall('.//nfe:det', ns)
            itens = []
            for det in dets:
                prod = det.find('.//nfe:prod', ns)
                imposto = det.find('.//nfe:imposto', ns)
                
                item = {
                    'codigo': prod.findtext('nfe:cProd', '', ns),
                    'descricao': prod.findtext('nfe:xProd', '', ns),
                    'ncm': prod.findtext('nfe:NCM', '', ns),
                    'cfop': prod.findtext('nfe:CFOP', '', ns),
                    'unidade': prod.findtext('nfe:uCom', '', ns),
                    'quantidade': prod.findtext('nfe:qCom', '0', ns),
                    'valor_unitario': prod.findtext('nfe:vUnCom', '0', ns),
                    'valor_total': prod.findtext('nfe:vProd', '0', ns)
                }
                itens.append(item)
            
            dados = {
                'chave': inf_nfe.get('Id', '').replace('NFe', ''),
                'numero': ide.findtext('nfe:nNF', '', ns),
                'serie': ide.findtext('nfe:serie', '', ns),
                'data_emissao': ide.findtext('nfe:dhEmi', '', ns)[:10],
                'natureza': ide.findtext('nfe:natOp', '', ns),
                
                # Emitente
                'emit_nome': emit.findtext('nfe:xNome', '', ns),
                'emit_cnpj': emit.findtext('nfe:CNPJ', '', ns),
                'emit_ie': emit.findtext('nfe:IE', '', ns),
                'emit_endereco': f"{emit.findtext('.//nfe:xLgr', '', ns)}, {emit.findtext('.//nfe:nro', '', ns)}",
                'emit_bairro': emit.findtext('.//nfe:xBairro', '', ns),
                'emit_municipio': emit.findtext('.//nfe:xMun', '', ns),
                'emit_uf': emit.findtext('.//nfe:UF', '', ns),
                'emit_cep': emit.findtext('.//nfe:CEP', '', ns),
                'emit_fone': emit.findtext('.//nfe:fone', '', ns),
                
                # Destinatário
                'dest_nome': dest.findtext('nfe:xNome', '', ns) if dest is not None else '',
                'dest_cnpj': dest.findtext('nfe:CNPJ', '', ns) if dest is not None else '',
                'dest_cpf': dest.findtext('nfe:CPF', '', ns) if dest is not None else '',
                'dest_endereco': f"{dest.findtext('.//nfe:xLgr', '', ns)}, {dest.findtext('.//nfe:nro', '', ns)}" if dest is not None else '',
                'dest_bairro': dest.findtext('.//nfe:xBairro', '', ns) if dest is not None else '',
                'dest_municipio': dest.findtext('.//nfe:xMun', '', ns) if dest is not None else '',
                'dest_uf': dest.findtext('.//nfe:UF', '', ns) if dest is not None else '',
                'dest_cep': dest.findtext('.//nfe:CEP', '', ns) if dest is not None else '',
                
                # Totais
                'valor_produtos': total.findtext('nfe:vProd', '0', ns),
                'valor_frete': total.findtext('nfe:vFrete', '0', ns),
                'valor_desconto': total.findtext('nfe:vDesc', '0', ns),
                'valor_total': total.findtext('nfe:vNF', '0', ns),
                
                # Itens
                'itens': itens
            }
            
            return dados
            
        except Exception as e:
            print(f"[DANFE] Erro ao parsear XML: {e}")
            raise
    
    def formatar_cnpj_cpf(self, doc):
        """
        Formata CNPJ ou CPF
        """
        doc = ''.join(c for c in doc if c.isdigit())
        if len(doc) == 14:  # CNPJ
            return f"{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}"
        elif len(doc) == 11:  # CPF
            return f"{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}"
        return doc
    
    def formatar_chave(self, chave):
        """
        Formata chave de acesso (grupos de 4 dígitos)
        """
        chave = ''.join(c for c in chave if c.isdigit())
        return ' '.join([chave[i:i+4] for i in range(0, len(chave), 4)])
    
    def gerar_pdf_simplificado(self, xml_string):
        """
        Gera DANFE simplificado em PDF
        Retorna bytes do PDF
        """
        # Parse do XML
        dados = self.parse_xml(xml_string)
        
        # Criar PDF em memória
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=10*mm, bottomMargin=10*mm)
        elements = []
        
        # ========================================
        # CABEÇALHO
        # ========================================
        
        # Título
        elements.append(Paragraph("<b>DANFE</b>", self.title_style))
        elements.append(Paragraph("Documento Auxiliar da Nota Fiscal Eletrônica", self.small_style))
        elements.append(Spacer(1, 5*mm))
        
        # Dados principais
        header_data = [
            ['<b>NÚMERO</b>', '<b>SÉRIE</b>', '<b>DATA EMISSÃO</b>', '<b>CHAVE DE ACESSO</b>'],
            [dados['numero'], dados['serie'], dados['data_emissao'], self.formatar_chave(dados['chave'])]
        ]
        
        header_table = Table(header_data, colWidths=[30*mm, 20*mm, 30*mm, 110*mm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#CCCCCC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 3*mm))
        
        # ========================================
        # EMITENTE
        # ========================================
        
        emit_data = [
            ['<b>EMITENTE</b>'],
            [f"<b>{dados['emit_nome']}</b>"],
            [f"CNPJ: {self.formatar_cnpj_cpf(dados['emit_cnpj'])}  |  IE: {dados['emit_ie']}"],
            [f"{dados['emit_endereco']}, {dados['emit_bairro']}"],
            [f"{dados['emit_municipio']}/{dados['emit_uf']}  |  CEP: {dados['emit_cep']}  |  Fone: {dados['emit_fone']}"]
        ]
        
        emit_table = Table(emit_data, colWidths=[190*mm])
        emit_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEEEEE')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(emit_table)
        elements.append(Spacer(1, 3*mm))
        
        # ========================================
        # DESTINATÁRIO
        # ========================================
        
        doc_dest = dados['dest_cnpj'] or dados['dest_cpf']
        tipo_doc = 'CNPJ' if len(doc_dest) == 14 else 'CPF'
        
        dest_data = [
            ['<b>DESTINATÁRIO</b>'],
            [f"<b>{dados['dest_nome']}</b>"],
            [f"{tipo_doc}: {self.formatar_cnpj_cpf(doc_dest)}"],
            [f"{dados['dest_endereco']}, {dados['dest_bairro']}"],
            [f"{dados['dest_municipio']}/{dados['dest_uf']}  |  CEP: {dados['dest_cep']}"]
        ]
        
        dest_table = Table(dest_data, colWidths=[190*mm])
        dest_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEEEEE')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(dest_table)
        elements.append(Spacer(1, 3*mm))
        
        # ========================================
        # PRODUTOS/SERVIÇOS
        # ========================================
        
        items_header = [['<b>CÓD</b>', '<b>DESCRIÇÃO</b>', '<b>NCM</b>', '<b>CFOP</b>', '<b>UN</b>', '<b>QTD</b>', '<b>VL.UNIT</b>', '<b>VL.TOTAL</b>']]
        
        for item in dados['itens']:
            items_header.append([
                item['codigo'][:10],
                item['descricao'][:40],
                item['ncm'],
                item['cfop'],
                item['unidade'],
                f"{float(item['quantidade']):.2f}",
                f"R$ {float(item['valor_unitario']):.2f}",
                f"R$ {float(item['valor_total']):.2f}"
            ])
        
        items_table = Table(items_header, colWidths=[15*mm, 70*mm, 15*mm, 12*mm, 10*mm, 15*mm, 20*mm, 23*mm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#CCCCCC')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (5, 1), (7, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 3*mm))
        
        # ========================================
        # TOTAIS
        # ========================================
        
        totais_data = [
            ['<b>VALOR PRODUTOS</b>', '<b>FRETE</b>', '<b>DESCONTO</b>', '<b>VALOR TOTAL</b>'],
            [
                f"R$ {float(dados['valor_produtos']):.2f}",
                f"R$ {float(dados['valor_frete']):.2f}",
                f"R$ {float(dados['valor_desconto']):.2f}",
                f"R$ {float(dados['valor_total']):.2f}"
            ]
        ]
        
        totais_table = Table(totais_data, colWidths=[47.5*mm, 47.5*mm, 47.5*mm, 47.5*mm])
        totais_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#CCCCCC')),
            ('BACKGROUND', (3, 1), (3, 1), colors.HexColor('#00A99D')),
            ('TEXTCOLOR', (3, 1), (3, 1), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (3, 1), (3, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(totais_table)
        elements.append(Spacer(1, 5*mm))
        
        # ========================================
        # RODAPÉ
        # ========================================
        
        elements.append(Paragraph(
            f"<b>Natureza da Operação:</b> {dados['natureza']}",
            self.small_style
        ))
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph(
            "<i>Este documento é uma representação simplificada da NF-e. "
            "Consulte a autenticidade no Portal da Nota Fiscal Eletrônica.</i>",
            self.small_style
        ))
        
        # Gerar PDF
        doc.build(elements)
        
        # Retornar bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
