# -*- coding: utf-8 -*-
"""
Serviço de Geração de PDF para Orçamentos
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime
from decimal import Decimal
import os


def formatar_moeda(valor):
    """Formata valor para moeda brasileira"""
    if valor is None:
        valor = 0
    try:
        valor = float(valor)
    except:
        valor = 0
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_data(data):
    """Formata data para o padrão brasileiro"""
    if data is None:
        return ""
    if isinstance(data, str):
        try:
            data = datetime.strptime(data, "%Y-%m-%d")
        except:
            return data
    return data.strftime("%d/%m/%Y")


class OrcamentoPDF:
    """Classe para gerar PDF de orçamento"""
    
    def __init__(self, orcamento, itens, empresa=None):
        self.orcamento = orcamento
        self.itens = itens or []
        self.empresa = empresa or {}
        self.styles = getSampleStyleSheet()
        self._criar_estilos()
    
    def _criar_estilos(self):
        """Cria estilos personalizados"""
        self.styles.add(ParagraphStyle(
            name='TituloDoc',
            parent=self.styles['Heading1'],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=10,
            textColor=colors.HexColor('#071231')
        ))
        
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Heading2'],
            fontSize=12,
            alignment=TA_LEFT,
            spaceBefore=15,
            spaceAfter=5,
            textColor=colors.HexColor('#0d7377')
        ))
        
        self.styles.add(ParagraphStyle(
            name='Normal2',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='Rodape',
            parent=self.styles['Normal'],
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.gray
        ))
        
        self.styles.add(ParagraphStyle(
            name='Direita',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_RIGHT
        ))
    
    def gerar(self):
        """Gera o PDF e retorna o buffer"""
        buffer = BytesIO()
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=15*mm,
            bottomMargin=20*mm
        )
        
        elementos = []
        
        # Cabeçalho
        elementos.extend(self._criar_cabecalho())
        
        # Dados do Cliente
        elementos.extend(self._criar_dados_cliente())
        
        # Tabela de Itens
        elementos.extend(self._criar_tabela_itens())
        
        # Totais
        elementos.extend(self._criar_totais())
        
        # Condições
        elementos.extend(self._criar_condicoes())
        
        # Observações
        elementos.extend(self._criar_observacoes())
        
        # Rodapé
        elementos.extend(self._criar_rodape())
        
        doc.build(elementos)
        buffer.seek(0)
        return buffer
    
    def _criar_cabecalho(self):
        """Cria o cabeçalho do documento com logo e dados da empresa"""
        elementos = []
        
        # Dados da empresa
        nome_empresa = self.empresa.get('nome_fantasia') or self.empresa.get('razao_social', 'EMPRESA')
        razao_social = self.empresa.get('razao_social', '')
        cnpj = self.empresa.get('cnpj', '')
        ie = self.empresa.get('inscricao_estadual', '')
        logradouro = self.empresa.get('logradouro', '')
        numero = self.empresa.get('numero', '')
        bairro = self.empresa.get('bairro', '')
        cidade = self.empresa.get('cidade', '')
        estado = self.empresa.get('estado', '')
        cep = self.empresa.get('cep', '')
        telefone = self.empresa.get('telefone', '')
        email = self.empresa.get('email', '')
        logo_path = self.empresa.get('logo_path', '')
        
        # Tentar adicionar logo
        logo_element = None
        if logo_path:
            try:
                # Caminho relativo ao projeto
                full_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app', 'static', logo_path.lstrip('/'))
                if os.path.exists(full_path):
                    logo_element = Image(full_path, width=50*mm, height=20*mm)
                    logo_element.hAlign = 'LEFT'
            except:
                pass
        
        # Criar tabela com logo e dados da empresa
        dados_empresa = []
        dados_empresa.append(Paragraph(f"<b>{nome_empresa}</b>", self.styles['Normal2']))
        if razao_social and razao_social != nome_empresa:
            dados_empresa.append(Paragraph(f"{razao_social}", self.styles['Normal2']))
        if cnpj:
            dados_empresa.append(Paragraph(f"CNPJ: {cnpj}" + (f" | IE: {ie}" if ie else ""), self.styles['Normal2']))
        if logradouro:
            endereco = f"{logradouro}, {numero}" if numero else logradouro
            if bairro:
                endereco += f" - {bairro}"
            dados_empresa.append(Paragraph(endereco, self.styles['Normal2']))
        if cidade:
            dados_empresa.append(Paragraph(f"{cidade}/{estado}" + (f" - CEP: {cep}" if cep else ""), self.styles['Normal2']))
        if telefone or email:
            contato = []
            if telefone:
                contato.append(f"Tel: {telefone}")
            if email:
                contato.append(email)
            dados_empresa.append(Paragraph(" | ".join(contato), self.styles['Normal2']))
        
        # Montar tabela do cabeçalho
        if logo_element:
            header_data = [[logo_element, dados_empresa]]
            header_table = Table(header_data, colWidths=[60*mm, 120*mm])
        else:
            header_data = [[dados_empresa]]
            header_table = Table(header_data, colWidths=[180*mm])
        
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ]))
        elementos.append(header_table)
        
        elementos.append(Spacer(1, 8*mm))
        
        # Título do orçamento
        numero_orc = self.orcamento.get('numero', 'N/A')
        elementos.append(Paragraph(f"ORÇAMENTO Nº {numero_orc}", self.styles['TituloDoc']))
        
        # Data de emissão, validade e vendedor
        data_emissao = formatar_data(self.orcamento.get('data_emissao'))
        data_validade = formatar_data(self.orcamento.get('data_validade'))
        vendedor = self.orcamento.get('vendedor_nome', '')
        
        dados_tabela = [
            ['Data de Emissão:', data_emissao, 'Validade:', data_validade],
            ['Vendedor:', vendedor, '', ''],
        ]
        
        t = Table(dados_tabela, colWidths=[80, 100, 80, 100])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        elementos.append(t)
        elementos.append(Spacer(1, 5*mm))
        
        return elementos
    
    def _criar_dados_cliente(self):
        """Cria a seção de dados do cliente"""
        elementos = []
        
        elementos.append(Paragraph("DADOS DO CLIENTE", self.styles['Subtitulo']))
        
        cliente_nome = self.orcamento.get('cliente_nome', 'Cliente não informado')
        cliente_doc = self.orcamento.get('cliente_documento', '')
        cliente_ie = self.orcamento.get('cliente_ie', '')
        cliente_endereco = self.orcamento.get('cliente_endereco', '')
        cliente_numero = self.orcamento.get('cliente_numero', '')
        cliente_bairro = self.orcamento.get('cliente_bairro', '')
        cliente_cidade = self.orcamento.get('cliente_cidade', '')
        cliente_estado = self.orcamento.get('cliente_estado', '')
        cliente_cep = self.orcamento.get('cliente_cep', '')
        cliente_telefone = self.orcamento.get('cliente_telefone', '')
        cliente_email = self.orcamento.get('cliente_email', '')
        contato = self.orcamento.get('contato', '')
        
        # Montar endereço completo
        endereco_partes = []
        if cliente_endereco:
            endereco_partes.append(cliente_endereco)
        if cliente_numero:
            endereco_partes.append(cliente_numero)
        if cliente_bairro:
            endereco_partes.append(f"- {cliente_bairro}")
        endereco = ", ".join(endereco_partes) if endereco_partes else ''
        
        cidade_estado = f"{cliente_cidade}/{cliente_estado}" if cliente_cidade else ''
        if cliente_cep:
            cidade_estado += f" - CEP: {cliente_cep}"
        
        dados = [
            ['Cliente:', cliente_nome],
        ]
        
        if cliente_doc:
            doc_label = 'CNPJ:' if len(str(cliente_doc).replace('.','').replace('-','').replace('/','')) > 11 else 'CPF:'
            dados.append([doc_label, cliente_doc + (f" | IE: {cliente_ie}" if cliente_ie else "")])
        
        if endereco:
            dados.append(['Endereço:', endereco])
        
        if cidade_estado:
            dados.append(['Cidade:', cidade_estado])
        
        if cliente_telefone:
            dados.append(['Telefone:', cliente_telefone])
        
        if cliente_email:
            dados.append(['Email:', cliente_email])
        
        if contato:
            dados.append(['Contato:', contato])
        
        t = Table(dados, colWidths=[70, 400])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.gray),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))
        elementos.append(t)
        elementos.append(Spacer(1, 5*mm))
        
        return elementos
    
    def _criar_tabela_itens(self):
        """Cria a tabela de itens do orçamento"""
        elementos = []
        
        elementos.append(Paragraph("ITENS DO ORCAMENTO", self.styles['Subtitulo']))
        
        # Cabeçalho da tabela
        cabecalho = ['#', 'Codigo', 'Descricao', 'Qtd', 'Un', 'Preco Unit.', 'Desconto', 'Total']
        dados = [cabecalho]
        
        # Itens
        for i, item in enumerate(self.itens, 1):
            codigo = item.get('produto_codigo', item.get('produto_id', ''))
            descricao = item.get('produto_nome', item.get('descricao', ''))
            quantidade = item.get('quantidade', 0)
            unidade = item.get('unidade', 'UN')
            preco = item.get('preco_unitario', 0)
            desconto = item.get('valor_desconto', 0)
            total = item.get('valor_total', 0)
            
            # Truncar descrição se muito longa
            if len(str(descricao)) > 40:
                descricao = str(descricao)[:37] + '...'
            
            dados.append([
                str(i),
                str(codigo)[:15],
                descricao,
                f"{float(quantidade):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                unidade,
                formatar_moeda(preco),
                formatar_moeda(desconto) if float(desconto or 0) > 0 else '-',
                formatar_moeda(total)
            ])
        
        # Criar tabela
        col_widths = [20, 50, 180, 40, 25, 70, 50, 70]
        t = Table(dados, colWidths=col_widths, repeatRows=1)
        
        t.setStyle(TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d7377')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Corpo
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # #
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),   # Qtd
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Un
            ('ALIGN', (5, 1), (-1, -1), 'RIGHT'),  # Valores
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.gray),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#0d7377')),
            
            # Alternância de cores
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f9fa')]),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        elementos.append(t)
        elementos.append(Spacer(1, 5*mm))
        
        return elementos
    
    def _criar_totais(self):
        """Cria a seção de totais"""
        elementos = []
        
        valor_produtos = float(self.orcamento.get('valor_produtos', 0) or 0)
        valor_desconto = float(self.orcamento.get('valor_desconto', 0) or 0)
        valor_frete = float(self.orcamento.get('valor_frete', 0) or 0)
        valor_total = float(self.orcamento.get('valor_total', 0) or 0)
        
        dados = []
        dados.append(['', '', 'Subtotal:', formatar_moeda(valor_produtos)])
        
        if valor_desconto > 0:
            dados.append(['', '', 'Desconto:', f"- {formatar_moeda(valor_desconto)}"])
        
        if valor_frete > 0:
            dados.append(['', '', 'Frete:', formatar_moeda(valor_frete)])
        
        dados.append(['', '', 'TOTAL:', formatar_moeda(valor_total)])
        
        t = Table(dados, colWidths=[200, 100, 100, 100])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
            ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (2, -1), (-1, -1), 12),
            ('TEXTCOLOR', (2, -1), (-1, -1), colors.HexColor('#0d7377')),
            ('LINEABOVE', (2, -1), (-1, -1), 1, colors.HexColor('#0d7377')),
            ('TOPPADDING', (0, -1), (-1, -1), 8),
        ]))
        
        elementos.append(t)
        elementos.append(Spacer(1, 5*mm))
        
        return elementos
    
    def _criar_condicoes(self):
        """Cria a seção de condições comerciais"""
        elementos = []
        
        elementos.append(Paragraph("CONDIÇÕES COMERCIAIS", self.styles['Subtitulo']))
        
        condicao_pagamento = self.orcamento.get('condicao_pagamento', 'A combinar')
        prazo_entrega = self.orcamento.get('prazo_entrega', 0)
        frete = self.orcamento.get('frete_por_conta', 'destinatario')
        obs_validade = self.orcamento.get('obs_validade', '')
        obs_entrega = self.orcamento.get('obs_entrega', '')
        obs_embalagem = self.orcamento.get('obs_embalagem', '')
        obs_garantia = self.orcamento.get('obs_garantia', '')
        obs_certificado = self.orcamento.get('obs_certificado', '')
        referencia_cliente = self.orcamento.get('referencia_cliente', '')
        
        frete_texto = {
            'emitente': 'Por conta do emitente (CIF)',
            'destinatario': 'Por conta do destinatário (FOB)',
            'terceiros': 'Por conta de terceiros',
            'sem_frete': 'Sem frete'
        }.get(frete, frete)
        
        dados = [
            ['Condição de Pagamento:', condicao_pagamento or 'A combinar'],
            ['Prazo de Entrega:', f"{prazo_entrega} dias" if prazo_entrega else (obs_entrega or 'A combinar')],
            ['Frete:', frete_texto],
        ]
        
        # Transportadora
        transportadora = self.orcamento.get('transportadora_nome')
        if transportadora:
            dados.append(['Transportadora:', transportadora])
        
        # Informações adicionais
        if obs_validade:
            dados.append(['Validade:', f"{obs_validade} dias"])
        
        if obs_embalagem:
            dados.append(['Embalagem:', obs_embalagem])
        
        if obs_garantia:
            dados.append(['Garantia:', obs_garantia])
        
        if obs_certificado:
            dados.append(['Certificado:', obs_certificado])
        
        if referencia_cliente:
            dados.append(['Ref. Cliente:', referencia_cliente])
        
        t = Table(dados, colWidths=[120, 350])
        t.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9fa')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.gray),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elementos.append(t)
        elementos.append(Spacer(1, 5*mm))
        
        return elementos
    
    def _criar_observacoes(self):
        """Cria a seção de observações"""
        elementos = []
        
        observacoes = self.orcamento.get('observacoes', '')
        
        if observacoes:
            elementos.append(Paragraph("OBSERVACOES", self.styles['Subtitulo']))
            elementos.append(Paragraph(observacoes, self.styles['Normal2']))
            elementos.append(Spacer(1, 5*mm))
        
        return elementos
    
    def _criar_rodape(self):
        """Cria o rodapé do documento"""
        elementos = []
        
        elementos.append(Spacer(1, 10*mm))
        
        # Linha de assinatura
        elementos.append(Paragraph("_" * 60, self.styles['Rodape']))
        elementos.append(Paragraph("Assinatura do Cliente / Aceite", self.styles['Rodape']))
        
        elementos.append(Spacer(1, 5*mm))
        
        # Data de geração
        agora = datetime.now().strftime("%d/%m/%Y as %H:%M")
        elementos.append(Paragraph(f"Documento gerado em {agora}", self.styles['Rodape']))
        elementos.append(Paragraph("Este orcamento tem validade conforme data indicada acima.", self.styles['Rodape']))
        
        return elementos


def gerar_pdf_orcamento(orcamento, itens, empresa=None):
    """
    Função auxiliar para gerar PDF de orçamento
    
    Args:
        orcamento: dict com dados do orçamento
        itens: list de dicts com itens do orçamento
        empresa: dict com dados da empresa (opcional)
    
    Returns:
        BytesIO: buffer com o PDF gerado
    """
    pdf = OrcamentoPDF(orcamento, itens, empresa)
    return pdf.gerar()
