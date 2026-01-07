# -*- coding: utf-8 -*-
"""
Gerador de Relatório de Fechamento de Caixa em PDF
Suporta formatos A4 e Cupom Térmico (80mm/58mm)
"""

from io import BytesIO
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class RelatorioCaixaGenerator:
    """
    Gerador de relatório de fechamento de caixa
    """
    
    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab não está instalado. Execute: pip install reportlab")
        
        self.styles = getSampleStyleSheet()
        self._criar_estilos()
    
    def _criar_estilos(self):
        """Cria estilos personalizados"""
        self.title_style = ParagraphStyle(
            'TitleStyle',
            parent=self.styles['Heading1'],
            fontSize=12,
            alignment=TA_CENTER,
            spaceAfter=2*mm
        )
        
        self.header_style = ParagraphStyle(
            'HeaderStyle',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            spaceAfter=1*mm
        )
        
        self.normal_style = ParagraphStyle(
            'NormalStyle',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_LEFT,
            spaceAfter=1*mm
        )
        
        self.small_style = ParagraphStyle(
            'SmallStyle',
            parent=self.styles['Normal'],
            fontSize=7,
            alignment=TA_LEFT
        )
        
        self.right_style = ParagraphStyle(
            'RightStyle',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_RIGHT
        )
    
    def gerar_pdf(self, dados_caixa, formato='80mm'):
        """
        Gera PDF do relatório de fechamento de caixa
        dados_caixa: dicionário com dados do caixa
        formato: 'A4', '80mm' ou '58mm'
        """
        buffer = BytesIO()
        
        if formato == '80mm':
            largura = 80 * mm
            altura = 297 * mm
            doc = SimpleDocTemplate(buffer, pagesize=(largura, altura),
                                    leftMargin=2*mm, rightMargin=2*mm,
                                    topMargin=3*mm, bottomMargin=3*mm)
        elif formato == '58mm':
            largura = 58 * mm
            altura = 297 * mm
            doc = SimpleDocTemplate(buffer, pagesize=(largura, altura),
                                    leftMargin=2*mm, rightMargin=2*mm,
                                    topMargin=3*mm, bottomMargin=3*mm)
        else:
            doc = SimpleDocTemplate(buffer, pagesize=A4,
                                    leftMargin=15*mm, rightMargin=15*mm,
                                    topMargin=15*mm, bottomMargin=15*mm)
        
        elements = []
        separador = "-" * (50 if formato != '58mm' else 35)
        
        # ===== CABEÇALHO =====
        elements.append(Paragraph("<b>RELATÓRIO DE FECHAMENTO</b>", self.title_style))
        elements.append(Paragraph("<b>DE CAIXA</b>", self.title_style))
        elements.append(Spacer(1, 3*mm))
        
        # Dados da empresa
        empresa_nome = dados_caixa.get('empresa_nome', 'EMPRESA')
        elements.append(Paragraph(f"<b>{empresa_nome}</b>", self.header_style))
        if dados_caixa.get('empresa_cnpj'):
            elements.append(Paragraph(f"CNPJ: {dados_caixa.get('empresa_cnpj')}", self.header_style))
        
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(separador, self.header_style))
        
        # ===== DADOS DO CAIXA =====
        elements.append(Paragraph("<b>IDENTIFICAÇÃO DO CAIXA</b>", self.header_style))
        elements.append(Spacer(1, 1*mm))
        
        elements.append(Paragraph(f"Caixa Nº: <b>{dados_caixa.get('caixa_numero', '-')}</b>", self.normal_style))
        elements.append(Paragraph(f"PDV: {dados_caixa.get('pdv_nome', '-')}", self.normal_style))
        elements.append(Paragraph(f"Operador: {dados_caixa.get('operador', '-')}", self.normal_style))
        
        elements.append(Spacer(1, 1*mm))
        
        # Datas
        data_abertura = dados_caixa.get('data_abertura', '')
        data_fechamento = dados_caixa.get('data_fechamento', '')
        elements.append(Paragraph(f"Abertura: {data_abertura}", self.normal_style))
        elements.append(Paragraph(f"Fechamento: {data_fechamento}", self.normal_style))
        
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(separador, self.header_style))
        
        # ===== RESUMO DE VENDAS =====
        elements.append(Paragraph("<b>RESUMO DE VENDAS</b>", self.header_style))
        elements.append(Spacer(1, 2*mm))
        
        total_vendas = dados_caixa.get('total_vendas', 0)
        qtd_vendas = dados_caixa.get('qtd_vendas', 0)
        
        elements.append(Paragraph(f"Quantidade de Vendas: <b>{qtd_vendas}</b>", self.normal_style))
        elements.append(Paragraph(f"Total de Vendas: <b>R$ {total_vendas:.2f}</b>", self.normal_style))
        
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(separador, self.header_style))
        
        # ===== FORMAS DE PAGAMENTO =====
        elements.append(Paragraph("<b>FORMAS DE PAGAMENTO</b>", self.header_style))
        elements.append(Spacer(1, 2*mm))
        
        pagamentos = dados_caixa.get('pagamentos', {})
        for forma, valor in pagamentos.items():
            elements.append(Paragraph(f"{forma}: R$ {valor:.2f}", self.normal_style))
        
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(separador, self.header_style))
        
        # ===== MOVIMENTAÇÕES =====
        elements.append(Paragraph("<b>MOVIMENTAÇÕES</b>", self.header_style))
        elements.append(Spacer(1, 2*mm))
        
        saldo_abertura = dados_caixa.get('saldo_abertura', 0)
        suprimentos = dados_caixa.get('suprimentos', 0)
        sangrias = dados_caixa.get('sangrias', 0)
        
        elements.append(Paragraph(f"Saldo Abertura: R$ {saldo_abertura:.2f}", self.normal_style))
        elements.append(Paragraph(f"(+) Suprimentos: R$ {suprimentos:.2f}", self.normal_style))
        elements.append(Paragraph(f"(-) Sangrias: R$ {sangrias:.2f}", self.normal_style))
        
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(separador, self.header_style))
        
        # ===== CONFERÊNCIA =====
        elements.append(Paragraph("<b>CONFERÊNCIA DE VALORES</b>", self.header_style))
        elements.append(Spacer(1, 2*mm))
        
        esperado_dinheiro = dados_caixa.get('esperado_dinheiro', 0)
        conferido_dinheiro = dados_caixa.get('conferido_dinheiro', 0)
        diferenca_dinheiro = conferido_dinheiro - esperado_dinheiro
        
        esperado_cartao = dados_caixa.get('esperado_cartao', 0)
        conferido_cartao = dados_caixa.get('conferido_cartao', 0)
        diferenca_cartao = conferido_cartao - esperado_cartao
        
        esperado_outros = dados_caixa.get('esperado_outros', 0)
        conferido_outros = dados_caixa.get('conferido_outros', 0)
        diferenca_outros = conferido_outros - esperado_outros
        
        # Dinheiro
        elements.append(Paragraph("<b>DINHEIRO:</b>", self.normal_style))
        elements.append(Paragraph(f"  Esperado: R$ {esperado_dinheiro:.2f}", self.small_style))
        elements.append(Paragraph(f"  Conferido: R$ {conferido_dinheiro:.2f}", self.small_style))
        sinal = '+' if diferenca_dinheiro >= 0 else ''
        elements.append(Paragraph(f"  Diferença: {sinal}R$ {diferenca_dinheiro:.2f}", self.small_style))
        
        elements.append(Spacer(1, 1*mm))
        
        # Cartão
        elements.append(Paragraph("<b>CARTÃO:</b>", self.normal_style))
        elements.append(Paragraph(f"  Esperado: R$ {esperado_cartao:.2f}", self.small_style))
        elements.append(Paragraph(f"  Conferido: R$ {conferido_cartao:.2f}", self.small_style))
        sinal = '+' if diferenca_cartao >= 0 else ''
        elements.append(Paragraph(f"  Diferença: {sinal}R$ {diferenca_cartao:.2f}", self.small_style))
        
        elements.append(Spacer(1, 1*mm))
        
        # Outros
        elements.append(Paragraph("<b>OUTROS:</b>", self.normal_style))
        elements.append(Paragraph(f"  Esperado: R$ {esperado_outros:.2f}", self.small_style))
        elements.append(Paragraph(f"  Conferido: R$ {conferido_outros:.2f}", self.small_style))
        sinal = '+' if diferenca_outros >= 0 else ''
        elements.append(Paragraph(f"  Diferença: {sinal}R$ {diferenca_outros:.2f}", self.small_style))
        
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph(separador, self.header_style))
        
        # ===== DIFERENÇA TOTAL =====
        diferenca_total = diferenca_dinheiro + diferenca_cartao + diferenca_outros
        status = "OK" if diferenca_total == 0 else ("SOBRA" if diferenca_total > 0 else "FALTA")
        
        elements.append(Paragraph(f"<b>DIFERENÇA TOTAL: R$ {diferenca_total:.2f}</b>", self.title_style))
        elements.append(Paragraph(f"<b>STATUS: {status}</b>", self.header_style))
        
        elements.append(Spacer(1, 3*mm))
        elements.append(Paragraph(separador, self.header_style))
        
        # ===== OBSERVAÇÕES =====
        observacoes = dados_caixa.get('observacoes', '')
        if observacoes:
            elements.append(Paragraph("<b>OBSERVAÇÕES:</b>", self.header_style))
            elements.append(Paragraph(observacoes, self.small_style))
            elements.append(Spacer(1, 2*mm))
            elements.append(Paragraph(separador, self.header_style))
        
        # ===== ASSINATURAS =====
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph("_" * 30, self.header_style))
        elements.append(Paragraph("Operador", self.header_style))
        
        elements.append(Spacer(1, 8*mm))
        elements.append(Paragraph("_" * 30, self.header_style))
        elements.append(Paragraph("Supervisor", self.header_style))
        
        # ===== RODAPÉ =====
        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph(f"Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", self.small_style))
        
        # Gerar PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
