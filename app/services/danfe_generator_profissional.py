#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gerador de DANFE Profissional usando ReportLab
Layout baseado no template oficial da NFe
"""

from io import BytesIO
from lxml import etree
from datetime import datetime
import os

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class DanfeGeneratorProfissional:
    """
    Gerador de DANFE profissional com ReportLab
    """
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab não está instalado. Execute: pip install reportlab")
        
        self.width, self.height = A4
        self.margin = 2*mm  # Margem mínima conforme modelo oficial
        
    def parse_xml(self, xml_string):
        """Parse do XML da NFe"""
        try:
            root = etree.fromstring(xml_string.encode('utf-8') if isinstance(xml_string, str) else xml_string)
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            inf_nfe = root.find('.//nfe:infNFe', ns)
            ide = inf_nfe.find('.//nfe:ide', ns)
            emit = inf_nfe.find('.//nfe:emit', ns)
            dest = inf_nfe.find('.//nfe:dest', ns)
            total = inf_nfe.find('.//nfe:total/nfe:ICMSTot', ns)
            transp = inf_nfe.find('.//nfe:transp', ns)
            
            # Itens
            dets = inf_nfe.findall('.//nfe:det', ns)
            itens = []
            for det in dets:
                prod = det.find('.//nfe:prod', ns)
                imposto = det.find('.//nfe:imposto', ns)
                icms = imposto.find('.//nfe:ICMS', ns) if imposto is not None else None
                
                # Extrair dados fiscais completos
                icms = imposto.find('.//nfe:ICMS', ns)
                ipi = imposto.find('.//nfe:IPI', ns)
                
                # Dados ICMS
                cst_icms = ''
                bc_icms = 0.0
                valor_icms = 0.0
                aliq_icms = 0.0
                
                if icms is not None:
                    for child in icms:
                        # CST/CSOSN
                        cst_elem = child.find('.//nfe:CST', ns) or child.find('.//nfe:CSOSN', ns)
                        if cst_elem is not None:
                            cst_icms = cst_elem.text
                        
                        # Base de Cálculo ICMS
                        bc_elem = child.find('.//nfe:vBC', ns)
                        if bc_elem is not None:
                            bc_icms = float(bc_elem.text or '0')
                        
                        # Valor ICMS
                        v_icms_elem = child.find('.//nfe:vICMS', ns)
                        if v_icms_elem is not None:
                            valor_icms = float(v_icms_elem.text or '0')
                        
                        # Alíquota ICMS
                        p_icms_elem = child.find('.//nfe:pICMS', ns)
                        if p_icms_elem is not None:
                            aliq_icms = float(p_icms_elem.text or '0')
                        
                        break
                
                # Dados IPI
                valor_ipi = 0.0
                aliq_ipi = 0.0
                
                if ipi is not None:
                    ipi_trib = ipi.find('.//nfe:IPITrib', ns)
                    if ipi_trib is not None:
                        # Valor IPI
                        v_ipi_elem = ipi_trib.find('.//nfe:vIPI', ns)
                        if v_ipi_elem is not None:
                            valor_ipi = float(v_ipi_elem.text or '0')
                        
                        # Alíquota IPI
                        p_ipi_elem = ipi_trib.find('.//nfe:pIPI', ns)
                        if p_ipi_elem is not None:
                            aliq_ipi = float(p_ipi_elem.text or '0')
                
                item = {
                    'codigo': prod.findtext('nfe:cProd', '', ns)[:10],
                    'descricao': prod.findtext('nfe:xProd', '', ns)[:45],
                    'ncm': prod.findtext('nfe:NCM', '', ns),
                    'cst': cst_icms,
                    'cfop': prod.findtext('nfe:CFOP', '', ns),
                    'unidade': prod.findtext('nfe:uCom', '', ns),
                    'quantidade': float(prod.findtext('nfe:qCom', '0', ns)),
                    'valor_unitario': float(prod.findtext('nfe:vUnCom', '0', ns)),
                    'valor_total': float(prod.findtext('nfe:vProd', '0', ns)),
                    # Dados fiscais
                    'bc_icms': bc_icms,
                    'valor_icms': valor_icms,
                    'aliq_icms': aliq_icms,
                    'valor_ipi': valor_ipi,
                    'aliq_ipi': aliq_ipi
                }
                itens.append(item)
            
            # Transportador
            transporta = transp.find('.//nfe:transporta', ns) if transp is not None else None
            vol = transp.find('.//nfe:vol', ns) if transp is not None else None
            
            dados = {
                'chave': inf_nfe.get('Id', '').replace('NFe', ''),
                'numero': ide.findtext('nfe:nNF', '', ns),
                'serie': ide.findtext('nfe:serie', '', ns),
                'data_emissao': self.formatar_data(ide.findtext('nfe:dhEmi', '', ns)),
                'natureza': ide.findtext('nfe:natOp', '', ns),
                'tipo_operacao': ide.findtext('nfe:tpNF', '1', ns),
                
                # Emitente
                'emit_nome': emit.findtext('nfe:xNome', '', ns),
                'emit_cnpj': self.formatar_cnpj_cpf(emit.findtext('nfe:CNPJ', '', ns)),
                'emit_ie': emit.findtext('nfe:IE', '', ns),
                'emit_endereco': f"{emit.findtext('.//nfe:xLgr', '', ns)}, {emit.findtext('.//nfe:nro', '', ns)}",
                'emit_bairro': emit.findtext('.//nfe:xBairro', '', ns),
                'emit_municipio': emit.findtext('.//nfe:xMun', '', ns),
                'emit_uf': emit.findtext('.//nfe:UF', '', ns),
                'emit_cep': self.formatar_cep(emit.findtext('.//nfe:CEP', '', ns)),
                'emit_fone': self.formatar_telefone(emit.findtext('.//nfe:fone', '', ns)),
                
                # Destinatário
                'dest_nome': dest.findtext('nfe:xNome', '', ns) if dest is not None else '',
                'dest_cnpj_cpf': self.formatar_cnpj_cpf(dest.findtext('nfe:CNPJ', '', ns) or dest.findtext('nfe:CPF', '', ns)) if dest is not None else '',
                'dest_endereco': f"{dest.findtext('.//nfe:xLgr', '', ns)}, {dest.findtext('.//nfe:nro', '', ns)}" if dest is not None else '',
                'dest_bairro': dest.findtext('.//nfe:xBairro', '', ns) if dest is not None else '',
                'dest_municipio': dest.findtext('.//nfe:xMun', '', ns) if dest is not None else '',
                'dest_uf': dest.findtext('.//nfe:UF', '', ns) if dest is not None else '',
                'dest_cep': self.formatar_cep(dest.findtext('.//nfe:CEP', '', ns)) if dest is not None else '',
                'dest_fone': self.formatar_telefone(dest.findtext('.//nfe:fone', '', ns)) if dest is not None else '',
                'dest_ie': dest.findtext('nfe:IE', '', ns) if dest is not None else '',
                
                # Totais
                'valor_produtos': float(total.findtext('nfe:vProd', '0', ns)),
                'valor_frete': float(total.findtext('nfe:vFrete', '0', ns)),
                'valor_seguro': float(total.findtext('nfe:vSeg', '0', ns)),
                'valor_desconto': float(total.findtext('nfe:vDesc', '0', ns)),
                'valor_outras': float(total.findtext('nfe:vOutro', '0', ns)),
                'valor_ipi': float(total.findtext('nfe:vIPI', '0', ns)),
                'valor_icms': float(total.findtext('nfe:vICMS', '0', ns)),
                'valor_icms_st': float(total.findtext('nfe:vST', '0', ns)),
                'bc_icms': float(total.findtext('nfe:vBC', '0', ns)),
                'bc_icms_st': float(total.findtext('nfe:vBCST', '0', ns)),
                'valor_total': float(total.findtext('nfe:vNF', '0', ns)),
                
                # Transportador
                'transp_nome': transporta.findtext('nfe:xNome', '', ns) if transporta is not None else '',
                'transp_cnpj': self.formatar_cnpj_cpf(transporta.findtext('nfe:CNPJ', '', ns)) if transporta is not None else '',
                
                # Itens
                'itens': itens
            }
            
            return dados
            
        except Exception as e:
            print(f"[DANFE] Erro ao parsear XML: {e}")
            raise
    
    def formatar_cnpj_cpf(self, doc):
        """Formata CNPJ ou CPF"""
        if not doc:
            return ''
        doc = ''.join(c for c in doc if c.isdigit())
        if len(doc) == 14:  # CNPJ
            return f"{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}"
        elif len(doc) == 11:  # CPF
            return f"{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}"
        return doc
    
    def formatar_cep(self, cep):
        """Formata CEP"""
        if not cep:
            return ''
        cep = ''.join(c for c in cep if c.isdigit())
        if len(cep) == 8:
            return f"{cep[:5]}-{cep[5:]}"
        return cep
    
    def formatar_telefone(self, fone):
        """Formata telefone"""
        if not fone:
            return ''
        fone = ''.join(c for c in fone if c.isdigit())
        if len(fone) == 10:
            return f"({fone[:2]}) {fone[2:6]}-{fone[6:]}"
        elif len(fone) == 11:
            return f"({fone[:2]}) {fone[2:7]}-{fone[7:]}"
        return fone
    
    def formatar_chave(self, chave):
        """Formata chave de acesso (grupos de 4 dígitos)"""
        if not chave:
            return ''
        chave = ''.join(c for c in chave if c.isdigit())
        return ' '.join([chave[i:i+4] for i in range(0, len(chave), 4)])
    
    def formatar_data(self, data_iso):
        """Formata data ISO para DD/MM/YYYY"""
        if not data_iso:
            return ''
        try:
            dt = datetime.fromisoformat(data_iso.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y')
        except:
            return data_iso[:10]
    
    def buscar_logo_empresa(self, cnpj_emitente):
        """
        Busca a logo da empresa no banco de dados
        Retorna o caminho completo da logo ou None
        """
        try:
            from app.database import Database
            db = Database()
            
            # Buscar logo_path da empresa pelo CNPJ
            query = "SELECT logo_path FROM empresas WHERE cnpj = %s LIMIT 1"
            resultado = db.execute_query(query, (cnpj_emitente,))
            
            if hasattr(resultado, "fetchone"):
                empresa = resultado.fetchone()
            else:
                empresa = resultado[0] if resultado else None
            
            if empresa and empresa.get('logo_path'):
                # Construir caminho completo
                logo_path = empresa['logo_path']
                # Caminho relativo a partir da raiz do projeto
                full_path = os.path.join('app', 'static', logo_path)
                
                if os.path.exists(full_path):
                    print(f"[DANFE] Logo encontrada: {full_path}")
                    return full_path
                else:
                    print(f"[DANFE] Logo não encontrada no caminho: {full_path}")
            else:
                print(f"[DANFE] Empresa não possui logo cadastrada")
            
            return None
            
        except Exception as e:
            print(f"[DANFE] Erro ao buscar logo: {e}")
            return None
    
    def gerar_pdf_simplificado(self, xml_string):
        """
        Gera DANFE profissional em PDF
        """
        # Parse do XML
        dados = self.parse_xml(xml_string)
        
        # Criar PDF em memória
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=self.margin, bottomMargin=self.margin,
                                leftMargin=self.margin, rightMargin=self.margin)
        elements = []
        
        # Estilos conforme modelo oficial SEFAZ
        styles = getSampleStyleSheet()
        style_title = ParagraphStyle('title', parent=styles['Heading1'], fontSize=12, alignment=TA_CENTER, fontName='Helvetica-Bold', leading=14)
        style_label = ParagraphStyle('label', parent=styles['Normal'], fontSize=6, textColor=colors.black, leading=7)
        style_info = ParagraphStyle('info', parent=styles['Normal'], fontSize=8, textColor=colors.black, fontName='Helvetica-Bold', leading=9)
        style_small = ParagraphStyle('small', parent=styles['Normal'], fontSize=5, textColor=colors.black, leading=6)
        
        # Estilo padrão conforme modelo oficial
        default_table_style = [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1.5*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
        ]
        
        # ========================================
        # RECEBIMENTO
        # ========================================
        recebimento_data = [
            [Paragraph(f"<b>RECEBEMOS DE {dados['emit_nome'].upper()} OS PRODUTOS E/OU SERVIÇOS CONSTANTES DA NOTA FISCAL ELETRÔNICA INDICADA ABAIXO. EMISSÃO: {dados['data_emissao']} VALOR TOTAL: R$ {dados['valor_total']:.2f}</b>", style_label),
             Paragraph(f"<b><font size=16>NF-e</font></b><br/><b><font size=18>Nº {dados['numero']}</font></b><br/><b><font size=12>Série {dados['serie']}</font></b>", style_title)],
            [Paragraph("<b>DATA DE RECEBIMENTO</b>", style_label), Paragraph("<b>IDENTIFICAÇÃO E ASSINATURA DO RECEBEDOR</b>", style_label)]
        ]
        
        recebimento_table = Table(recebimento_data, colWidths=[150*mm, 56*mm])
        recebimento_table.setStyle(TableStyle(default_table_style + [
            ('SPAN', (1, 0), (1, 0)),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
        ]))
        elements.append(recebimento_table)
        elements.append(Spacer(1, 2*mm))
        
        # ========================================
        # CABEÇALHO
        # ========================================
        
        # Buscar logo da empresa
        cnpj_emitente = ''.join(c for c in dados['emit_cnpj'] if c.isdigit())
        logo_path = self.buscar_logo_empresa(cnpj_emitente)
        
        # Criar logo da empresa - Tamanho ajustado para não estourar
        if logo_path:
            try:
                logo_img = Image(logo_path, width=18*mm, height=18*mm, kind='proportional')
                logo_element = logo_img
            except Exception as e:
                print(f"[DANFE] Erro ao carregar imagem: {e}")
                logo_element = Paragraph("", style_label)
        else:
            logo_element = Paragraph("", style_label)
        
        # Cabeçalho conforme modelo oficial - Logo e dados centralizados
        # Criar tabela interna para logo + dados do emitente (centralizado)
        emitente_data = [[
            logo_element,
            Paragraph(f"<b>{dados['emit_nome'].upper()}</b><br/>{dados['emit_endereco']}, {dados['emit_bairro']}<br/>{dados['emit_municipio']}-{dados['emit_uf']} CEP: {dados['emit_cep']}<br/>Fone: {dados['emit_fone']}", style_label)
        ]]
        emitente_table = Table(emitente_data, colWidths=[20*mm, 33*mm])
        emitente_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 1*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
        ]))
        
        # Criar célula com título e conteúdo do emitente
        emitente_completo = [[
            Paragraph("<b>IDENTIFICAÇÃO DO EMITENTE</b>", style_label)
        ], [
            emitente_table
        ]]
        emitente_final = Table(emitente_completo, colWidths=[55*mm])
        emitente_final.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 1), (0, 1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        
        # Gerar código de barras da chave de acesso
        try:
            from reportlab.graphics.barcode import code128
            from reportlab.graphics.shapes import Drawing
            from reportlab.platypus import Flowable
            
            class BarcodeFlowable(Flowable):
                def __init__(self, value, width, height):
                    Flowable.__init__(self)
                    self.value = value
                    self.width = width
                    self.height = height
                
                def draw(self):
                    # Criar código de barras mais compacto para caber no espaço
                    barcode = code128.Code128(self.value, barHeight=10*mm, barWidth=0.19*mm)
                    # Obter largura real do código de barras
                    barcode_real_width = barcode.width
                    # Centralizar horizontalmente
                    x_offset = (self.width - barcode_real_width) / 2
                    # Posicionar verticalmente
                    y_offset = 2*mm
                    barcode.drawOn(self.canv, x_offset, y_offset)
            
            chave_numeros = ''.join(c for c in dados['chave'] if c.isdigit())
            barcode_element = BarcodeFlowable(chave_numeros, 76*mm, 15*mm)
        except Exception as e:
            print(f"[DANFE] Erro ao gerar código de barras: {e}")
            import traceback
            traceback.print_exc()
            barcode_element = Paragraph("<b>[CÓDIGO DE BARRAS]</b>", style_label)
        
        # Criar tabela para código de barras + chave
        barcode_data = [[barcode_element], [
            Paragraph(f"<b>CHAVE DE ACESSO</b><br/><font size=6>{self.formatar_chave(dados['chave'])}</font><br/><font size=5>Consulta de autenticidade no portal nacional da NF-e<br/>www.nfe.fazenda.gov.br/portal ou no site da Sefaz Autorizadora</font>", style_label)
        ]]
        barcode_table = Table(barcode_data, colWidths=[76*mm])
        barcode_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 1*mm),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1*mm),
            ('TOPPADDING', (0, 0), (-1, -1), 1*mm),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1*mm),
        ]))
        
        header_data = [
            [
                emitente_final,
                Paragraph(f"<b><font size=14>DANFE</font></b><br/><font size=6>Documento Auxiliar da Nota Fiscal Eletrônica</font><br/><b>{dados['tipo_operacao']}</b> - ENTRADA / <b>1</b> - SAÍDA<br/><b>Nº {dados['numero']}</b><br/><b>Série {dados['serie']}</b><br/><font size=5>Folha 1/1</font>", style_title),
                barcode_table
            ]
        ]
        
        header_table = Table(header_data, colWidths=[55*mm, 75*mm, 76*mm])
        header_table.setStyle(TableStyle(default_table_style + [
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'CENTER'),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 1*mm))
        
        # ========================================
        # NATUREZA DA OPERAÇÃO
        # ========================================
        natureza_data = [[
            Paragraph(f"<b>NATUREZA DA OPERAÇÃO</b><br/>{dados['natureza']}", style_label),
            Paragraph("<b>PROTOCOLO DE AUTORIZAÇÃO</b><br/>", style_label)
        ]]
        
        natureza_table = Table(natureza_data, colWidths=[103*mm, 103*mm])
        natureza_table.setStyle(TableStyle(default_table_style))
        elements.append(natureza_table)
        elements.append(Spacer(1, 1*mm))
        
        # ========================================
        # INSCRIÇÃO
        # ========================================
        inscricao_data = [[
            Paragraph(f"<b>INSCRIÇÃO ESTADUAL</b><br/>{dados['emit_ie']}", style_label),
            Paragraph("<b>INSCRIÇÃO ESTADUAL DO SUBST. TRIB.</b><br/>", style_label),
            Paragraph(f"<b>CNPJ</b><br/>{dados['emit_cnpj']}", style_label)
        ]]
        
        inscricao_table = Table(inscricao_data, colWidths=[68*mm, 69*mm, 69*mm])
        inscricao_table.setStyle(TableStyle(default_table_style))
        elements.append(inscricao_table)
        elements.append(Spacer(1, 2*mm))
        
        # ========================================
        # DESTINATÁRIO
        # ========================================
        elements.append(Paragraph("<b>DESTINATÁRIO/REMETENTE</b>", style_label))
        
        dest_data = [
            [
                Paragraph(f"<b>NOME/RAZÃO SOCIAL</b><br/>{dados['dest_nome']}", style_label),
                Paragraph(f"<b>CNPJ/CPF</b><br/>{dados['dest_cnpj_cpf']}", style_label),
                Paragraph(f"<b>DATA DE EMISSÃO</b><br/>{dados['data_emissao']}", style_label)
            ],
            [
                Paragraph(f"<b>ENDEREÇO</b><br/>{dados['dest_endereco']}", style_label),
                Paragraph(f"<b>BAIRRO/DISTRITO</b><br/>{dados['dest_bairro']}", style_label),
                Paragraph(f"<b>CEP</b><br/>{dados['dest_cep']}", style_label)
            ],
            [
                Paragraph(f"<b>MUNICÍPIO</b><br/>{dados['dest_municipio']}", style_label),
                Paragraph(f"<b>FONE/FAX</b><br/>{dados['dest_fone']}", style_label),
                Paragraph(f"<b>UF</b><br/>{dados['dest_uf']}", style_label)
            ]
        ]
        
        dest_table = Table(dest_data, colWidths=[110*mm, 56*mm, 40*mm])
        dest_table.setStyle(TableStyle(default_table_style))
        elements.append(dest_table)
        elements.append(Spacer(1, 2*mm))
        
        # ========================================
        # CÁLCULO DO IMPOSTO
        # ========================================
        elements.append(Paragraph("<b>CÁLCULO DO IMPOSTO</b>", style_label))
        
        imposto_data = [
            [
                Paragraph(f"<b>BASE CÁLC. ICMS</b><br/>{dados['bc_icms']:.2f}", style_label),
                Paragraph(f"<b>VALOR ICMS</b><br/>{dados['valor_icms']:.2f}", style_label),
                Paragraph(f"<b>BASE CÁLC. ICMS ST</b><br/>{dados['bc_icms_st']:.2f}", style_label),
                Paragraph(f"<b>VALOR ICMS ST</b><br/>{dados['valor_icms_st']:.2f}", style_label),
                Paragraph(f"<b>V. TOTAL PRODUTOS</b><br/>{dados['valor_produtos']:.2f}", style_label)
            ],
            [
                Paragraph(f"<b>VALOR FRETE</b><br/>{dados['valor_frete']:.2f}", style_label),
                Paragraph(f"<b>VALOR SEGURO</b><br/>{dados['valor_seguro']:.2f}", style_label),
                Paragraph(f"<b>DESCONTO</b><br/>{dados['valor_desconto']:.2f}", style_label),
                Paragraph(f"<b>OUTRAS DESP.</b><br/>{dados['valor_outras']:.2f}", style_label),
                Paragraph(f"<b>VALOR IPI</b><br/>{dados['valor_ipi']:.2f}", style_label)
            ],
            [
                {'text': '', 'colspan': 4},
                Paragraph(f"<b>V. TOTAL DA NOTA</b><br/><font size=10 color='#00A99D'><b>R$ {dados['valor_total']:.2f}</b></font>", style_label)
            ]
        ]
        
        # Processar imposto_data
        processed_imposto = []
        for row in imposto_data:
            new_row = []
            for cell in row:
                if isinstance(cell, dict):
                    continue
                new_row.append(cell)
            if new_row:
                processed_imposto.append(new_row)
        
        imposto_table = Table(processed_imposto, colWidths=[41*mm, 41*mm, 41*mm, 41*mm, 42*mm])
        imposto_table.setStyle(TableStyle(default_table_style + [
            ('BACKGROUND', (4, 2), (4, 2), colors.HexColor('#E0F7FA')),
            ('ALIGN', (0, 1), (-1, -1), 'RIGHT'),
        ]))
        elements.append(imposto_table)
        elements.append(Spacer(1, 2*mm))
        
        # ========================================
        # TRANSPORTADOR
        # ========================================
        elements.append(Paragraph("<b>TRANSPORTADOR/VOLUMES TRANSPORTADOS</b>", style_label))
        
        transp_data = [[
            Paragraph(f"<b>RAZÃO SOCIAL</b><br/>{dados['transp_nome']}", style_label),
            Paragraph(f"<b>CNPJ/CPF</b><br/>{dados['transp_cnpj']}", style_label)
        ]]
        
        transp_table = Table(transp_data, colWidths=[140*mm, 66*mm])
        transp_table.setStyle(TableStyle(default_table_style))
        elements.append(transp_table)
        elements.append(Spacer(1, 2*mm))
        
        # ========================================
        # PRODUTOS/SERVIÇOS
        # ========================================
        elements.append(Paragraph("<b>DADOS DO PRODUTO/SERVIÇO</b>", style_label))
        
        produtos_header = [[
            Paragraph("<b>CÓD<br/>PROD</b>", style_small),
            Paragraph("<b>DESCRIÇÃO DO PRODUTO/SERVIÇO</b>", style_small),
            Paragraph("<b>NCM<br/>SH</b>", style_small),
            Paragraph("<b>O<br/>CST</b>", style_small),
            Paragraph("<b>CFOP</b>", style_small),
            Paragraph("<b>UN</b>", style_small),
            Paragraph("<b>QUANT</b>", style_small),
            Paragraph("<b>VALOR<br/>UNIT</b>", style_small),
            Paragraph("<b>VALOR<br/>TOTAL</b>", style_small),
            Paragraph("<b>BC<br/>ICMS</b>", style_small),
            Paragraph("<b>VALOR<br/>ICMS</b>", style_small),
            Paragraph("<b>VALOR<br/>IPI</b>", style_small),
            Paragraph("<b>ALÍQ<br/>ICMS</b>", style_small),
            Paragraph("<b>ALÍQ<br/>IPI</b>", style_small)
        ]]
        
        for item in dados['itens']:
            produtos_header.append([
                Paragraph(item['codigo'], style_small),
                Paragraph(item['descricao'], style_small),
                Paragraph(item['ncm'], style_small),
                Paragraph(item['cst'], style_small),
                Paragraph(item['cfop'], style_small),
                Paragraph(item['unidade'], style_small),
                Paragraph(f"{item['quantidade']:.2f}", style_small),
                Paragraph(f"{item['valor_unitario']:.2f}", style_small),
                Paragraph(f"{item['valor_total']:.2f}", style_small),
                Paragraph(f"{item['bc_icms']:.2f}", style_small),
                Paragraph(f"{item['valor_icms']:.2f}", style_small),
                Paragraph(f"{item['valor_ipi']:.2f}", style_small),
                Paragraph(f"{item['aliq_icms']:.2f}%" if item['aliq_icms'] > 0 else "-", style_small),
                Paragraph(f"{item['aliq_ipi']:.2f}%" if item['aliq_ipi'] > 0 else "-", style_small)
            ])
        
        produtos_table = Table(produtos_header, colWidths=[12*mm, 45*mm, 12*mm, 8*mm, 10*mm, 8*mm, 12*mm, 14*mm, 16*mm, 12*mm, 12*mm, 12*mm, 10*mm, 10*mm])
        produtos_table.setStyle(TableStyle(default_table_style + [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E0E0E0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (6, 1), (8, -1), 'RIGHT'),
        ]))
        elements.append(produtos_table)
        elements.append(Spacer(1, 2*mm))
        
        # ========================================
        # DADOS ADICIONAIS
        # ========================================
        elements.append(Paragraph("<b>DADOS ADICIONAIS</b>", style_label))
        
        adicionais_data = [[
            Paragraph("<b>INFORMAÇÕES COMPLEMENTARES</b><br/>", style_label),
            Paragraph("<b>RESERVADO AO FISCO</b><br/>", style_label)
        ]]
        
        adicionais_table = Table(adicionais_data, colWidths=[103*mm, 103*mm], rowHeights=[25*mm])
        adicionais_table.setStyle(TableStyle(default_table_style))
        elements.append(adicionais_table)
        
        # Gerar PDF
        doc.build(elements)
        
        # Retornar bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
