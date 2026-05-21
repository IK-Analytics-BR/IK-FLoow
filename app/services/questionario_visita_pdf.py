# -*- coding: utf-8 -*-
"""Geração de PDF para Questionário de Visita ao Cliente (genérico por segmento)."""

from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import mm


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="TituloDoc",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=10,
        textColor=colors.HexColor("#003b73"),
    ))

    styles.add(ParagraphStyle(
        name="Secao",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        alignment=TA_LEFT,
        spaceBefore=10,
        spaceAfter=4,
        textColor=colors.HexColor("#00a6b4"),
    ))

    styles.add(ParagraphStyle(
        name="Pergunta",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        spaceBefore=4,
        spaceAfter=1,
        textColor=colors.HexColor("#1f2933"),
    ))

    styles.add(ParagraphStyle(
        name="Resposta",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        leftIndent=8,
        spaceAfter=4,
        textColor=colors.HexColor("#111827"),
    ))

    styles.add(ParagraphStyle(
        name="Meta",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#4b5563"),
    ))

    return styles


# Mapeamento de campos -> (seção, rótulo amigável)
SECOES_CAMPOS = {
    "1. Visão Geral do Negócio": [
        ("visao_empresas_juridicas", "Quais empresas existem juridicamente?"),
        ("visao_contabilidade", "Contabilidade separada ou centralizada?"),
        ("visao_gargalos", "Onde estão os principais gargalos hoje?"),
        ("visao_retrabalho", "O que mais gera retrabalho manual?"),
        ("visao_indicadores", "Quais indicadores são críticos para a gestão?"),
        ("visao_expansao", "Planos de expansão (novas cidades, franquias, exportação etc.)"),
    ],
    "2. Produção / Operações": [
        ("producao_fluxo", "Como funciona o fluxo de produção/operações (etapas principais, responsáveis e controles)?"),
        ("producao_tipo_planejamento", "Produção por OP, previsão de vendas ou sob demanda?"),
        ("producao_fichas_tecnicas", "Existem fichas técnicas/receitas por produto?"),
        ("producao_variacoes_cliente", "Há variação de receita por cliente?"),
        ("producao_perdas_subprodutos", "Perdas, quebras técnicas e reaproveitamento/subprodutos são controlados?"),
        ("producao_lotes_rastreabilidade", "Controle de lote, validade e rastreabilidade (recall)?"),
    ],
    "3. Estoque – Matéria-prima e Produto Acabado": [
        ("estoque_insumos_criticos", "Quais são os insumos críticos?"),
        ("estoque_controle_mp", "Como é o controle de lote/validade da matéria-prima?"),
        ("estoque_inventario", "Há inventários frequentes?"),
        ("estoque_produto_acabado", "Como é organizado o estoque de produto acabado (câmaras, CNPJ, tipo de produto, trânsito)?"),
        ("estoque_perdas_validade", "Há perdas por validade vencida?"),
        ("estoque_sistema_atual", "O sistema atual consegue controlar lote + validade + localização?"),
    ],
    "4. Loja de Fábrica (Varejo)": [
        ("loja_sistema", "A loja usa PDV separado ou o mesmo sistema da indústria?"),
        ("loja_estoque_integrado", "O estoque da loja é integrado com a fábrica?"),
        ("loja_tipo_venda", "Vende produto congelado, pronto para consumo ou ambos?"),
        ("loja_pagamentos", "Formas de pagamento aceitas (dinheiro, cartão, PIX, vale etc.)?"),
        ("loja_caixa", "Como é o controle de caixa (por operador/turno)?"),
        ("loja_fiscal", "Emite NFC-e, SAT ou outro?"),
        ("loja_promocoes", "Existem promoções, combos e políticas específicas?"),
    ],
    "5. Distribuidora / Atacado B2B": [
        ("dist_clientes_tipo", "Quais tipos de clientes atendem (supermercados, lanchonetes, redes etc.)?"),
        ("dist_politica_comercial", "Política comercial (tabelas de preço, descontos por volume, bonificações)?"),
        ("dist_pedidos_captacao", "Como os pedidos chegam (manual, WhatsApp, vendedor externo)?"),
        ("dist_separacao", "Separação (picking) por rota ou por cliente?"),
        ("dist_faturamento", "Faturamento (NF-e por pedido, consolidação, particularidades)?"),
        ("dist_cobranca", "Controle de inadimplência e condições de pagamento?"),
    ],
    "6. Transportadora / Logística Própria": [
        ("transp_frota", "Existe frota própria? Quantos veículos e tipos?"),
        ("transp_roteirizacao", "Roteirização manual ou por sistema?"),
        ("transp_tipo_entregas", "Entregas por rota fixa ou por pedido?"),
        ("transp_custos", "Como controlam custos (por km, por entrega)?"),
        ("transp_fiscal", "Emissão de CT-e, MDF-e e outros documentos?"),
        ("transp_temperatura_ocorrencias", "Controle de temperatura e registro de ocorrências (atraso, avaria)?"),
    ],
    "7. Fiscal & Obrigações": [
        ("fiscal_regime", "Qual o regime tributário e principais CFOPs?"),
        ("fiscal_icms_st", "Uso de ICMS ST e particularidades fiscais do segmento?"),
        ("fiscal_sped", "SPED Fiscal/Contribuições: como é feito hoje?"),
        ("fiscal_credito_icms", "Controle de crédito de ICMS?"),
        ("fiscal_diferenciacao_operacoes", "Diferença de tratamento entre varejo, atacado e transferências entre CNPJs?"),
    ],
    "8. Financeiro": [
        ("fin_contas", "Contas a pagar/receber estão no sistema?"),
        ("fin_conciliacao", "Conciliação bancária é feita automaticamente?"),
        ("fin_centros_custo", "Centros de custo por fábrica, loja, distribuidora, transportadora?"),
        ("fin_dre", "Existe DRE gerencial e visão de margem por produto/linha?"),
        ("fin_custo_real", "O custo real de produção é conhecido?"),
    ],
    "9. Tecnologia & Integrações": [
        ("tec_sistema_atual", "Qual sistema usam hoje e o que funciona bem/mal?"),
        ("tec_planilhas_whatsapp", "O que roda fora do sistema (Excel, WhatsApp etc.)?"),
        ("tec_integracoes", "Integrações necessárias (balanças, etiquetas, PDV, roteirizador, contabilidade etc.)?"),
        ("tec_relatorios_faltantes", "Quais relatórios hoje não conseguem tirar?"),
    ],
    "10. Visão de Futuro": [
        ("futuro_sistema_perfeito", "Se o sistema fosse perfeito, o que ele faria?"),
        ("futuro_dores", "O que mais dói hoje e trava o crescimento?"),
        ("futuro_perdas_ocultas", "Onde acreditam estar perdendo dinheiro sem perceber?"),
    ],
}


def gerar_pdf_questionario(contexto, respostas):
    """Gera o PDF do questionário de visita.

    Args:
        contexto (dict): dados principais do cliente/contato.
        respostas (dict): respostas do formulário, chaveadas pelos nomes dos campos.

    Returns:
        BytesIO: buffer com o PDF gerado.
    """
    styles = _build_styles()
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
    )

    elementos = []

    # Cabeçalho
    titulo = "Questionário de Visita ao Cliente"
    elementos.append(Paragraph(titulo, styles["TituloDoc"]))
    elementos.append(Spacer(1, 6))

    cliente_nome = contexto.get("cliente_nome") or "(não informado)"
    cliente_email = contexto.get("cliente_email") or "(não informado)"
    cliente_cnpj = contexto.get("cliente_cnpj") or ""
    contato_nome = contexto.get("contato_nome") or ""

    meta_lines = [
        f"Cliente: <b>{cliente_nome}</b>",
        f"Contato: {contato_nome}" if contato_nome else "",
        f"E-mail: {cliente_email}",
        f"CNPJ: {cliente_cnpj}" if cliente_cnpj else "",
        f"Data da visita: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
    ]
    meta_html = "<br/>".join([l for l in meta_lines if l])
    elementos.append(Paragraph(meta_html, styles["Meta"]))
    elementos.append(Spacer(1, 10))

    # Seções e respostas
    for nome_secao, campos in SECOES_CAMPOS.items():
        elementos.append(Paragraph(nome_secao, styles["Secao"]))

        for campo, rotulo in campos:
            valor = respostas.get(campo)
            if not valor:
                continue
            if isinstance(valor, (list, tuple)):
                texto_resposta = ", ".join(str(v) for v in valor if v)
            else:
                texto_resposta = str(valor)

            elementos.append(Paragraph(rotulo, styles["Pergunta"]))
            elementos.append(Paragraph(texto_resposta.replace("\n", "<br/>"), styles["Resposta"]))

        elementos.append(Spacer(1, 6))

    doc.build(elementos)
    buffer.seek(0)
    return buffer
