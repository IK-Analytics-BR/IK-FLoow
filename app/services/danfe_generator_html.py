#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gerador de DANFE (Documento Auxiliar da Nota Fiscal Eletrônica)
Baseado no template HTML profissional
Usa WeasyPrint para converter HTML em PDF
"""

from io import BytesIO
from lxml import etree
from datetime import datetime
import os
import base64

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


class DanfeGeneratorHTML:
    """
    Gerador de DANFE baseado em template HTML
    """
    
    def __init__(self):
        if not WEASYPRINT_AVAILABLE:
            raise ImportError("WeasyPrint não está instalado. Execute: pip install weasyprint")
        
        # Caminho para imagens
        self.template_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'nfe')
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir, exist_ok=True)
    
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
            transp = inf_nfe.find('.//nfe:transp', ns)
            
            # Itens
            dets = inf_nfe.findall('.//nfe:det', ns)
            itens_html = []
            for det in dets:
                prod = det.find('.//nfe:prod', ns)
                imposto = det.find('.//nfe:imposto', ns)
                icms = imposto.find('.//nfe:ICMS', ns)
                ipi = imposto.find('.//nfe:IPI', ns)
                
                # Pegar CST do ICMS (pode estar em vários lugares)
                cst_icms = ''
                if icms is not None:
                    for child in icms:
                        cst_elem = child.find('.//nfe:CST', ns) or child.find('.//nfe:CSOSN', ns)
                        if cst_elem is not None:
                            cst_icms = cst_elem.text
                            break
                
                item_html = f"""
                <tr>
                    <td class="txt-center">{prod.findtext('nfe:cProd', '', ns)}</td>
                    <td>{prod.findtext('nfe:xProd', '', ns)}</td>
                    <td class="txt-center">{prod.findtext('nfe:NCM', '', ns)}</td>
                    <td class="txt-center">{cst_icms}</td>
                    <td class="txt-center">{prod.findtext('nfe:CFOP', '', ns)}</td>
                    <td class="txt-center">{prod.findtext('nfe:uCom', '', ns)}</td>
                    <td class="txt-right">{float(prod.findtext('nfe:qCom', '0', ns)):.2f}</td>
                    <td class="txt-right">{float(prod.findtext('nfe:vUnCom', '0', ns)):.2f}</td>
                    <td class="txt-right">{float(prod.findtext('nfe:vProd', '0', ns)):.2f}</td>
                    <td class="txt-right"></td>
                    <td class="txt-right"></td>
                    <td class="txt-right"></td>
                    <td class="txt-right"></td>
                    <td class="txt-right"></td>
                </tr>
                """
                itens_html.append(item_html)
            
            # Dados do transportador
            transporta = transp.find('.//nfe:transporta', ns) if transp is not None else None
            vol = transp.find('.//nfe:vol', ns) if transp is not None else None
            
            dados = {
                'chave': inf_nfe.get('Id', '').replace('NFe', ''),
                'numero': ide.findtext('nfe:nNF', '', ns),
                'serie': ide.findtext('nfe:serie', '', ns),
                'data_emissao': self.formatar_data(ide.findtext('nfe:dhEmi', '', ns)),
                'natureza': ide.findtext('nfe:natOp', '', ns),
                'tipo_operacao': ide.findtext('nfe:tpNF', '1', ns),  # 0=Entrada, 1=Saída
                
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
                'valor_produtos': self.formatar_valor(total.findtext('nfe:vProd', '0', ns)),
                'valor_frete': self.formatar_valor(total.findtext('nfe:vFrete', '0', ns)),
                'valor_seguro': self.formatar_valor(total.findtext('nfe:vSeg', '0', ns)),
                'valor_desconto': self.formatar_valor(total.findtext('nfe:vDesc', '0', ns)),
                'valor_outras': self.formatar_valor(total.findtext('nfe:vOutro', '0', ns)),
                'valor_ipi': self.formatar_valor(total.findtext('nfe:vIPI', '0', ns)),
                'valor_icms': self.formatar_valor(total.findtext('nfe:vICMS', '0', ns)),
                'valor_icms_st': self.formatar_valor(total.findtext('nfe:vST', '0', ns)),
                'bc_icms': self.formatar_valor(total.findtext('nfe:vBC', '0', ns)),
                'bc_icms_st': self.formatar_valor(total.findtext('nfe:vBCST', '0', ns)),
                'valor_total': self.formatar_valor(total.findtext('nfe:vNF', '0', ns)),
                
                # Transportador
                'transp_nome': transporta.findtext('nfe:xNome', '', ns) if transporta is not None else '',
                'transp_cnpj': self.formatar_cnpj_cpf(transporta.findtext('nfe:CNPJ', '', ns)) if transporta is not None else '',
                'transp_ie': transporta.findtext('nfe:IE', '', ns) if transporta is not None else '',
                'transp_endereco': transporta.findtext('nfe:xEnder', '', ns) if transporta is not None else '',
                'transp_municipio': transporta.findtext('nfe:xMun', '', ns) if transporta is not None else '',
                'transp_uf': transporta.findtext('nfe:UF', '', ns) if transporta is not None else '',
                'transp_placa': transp.findtext('.//nfe:placa', '', ns) if transp is not None else '',
                'transp_placa_uf': transp.findtext('.//nfe:UF', '', ns) if transp is not None else '',
                'vol_qtd': vol.findtext('nfe:qVol', '', ns) if vol is not None else '',
                'vol_especie': vol.findtext('nfe:esp', '', ns) if vol is not None else '',
                'vol_marca': vol.findtext('nfe:marca', '', ns) if vol is not None else '',
                'vol_numero': vol.findtext('nfe:nVol', '', ns) if vol is not None else '',
                'vol_peso_bruto': vol.findtext('nfe:pesoB', '', ns) if vol is not None else '',
                'vol_peso_liquido': vol.findtext('nfe:pesoL', '', ns) if vol is not None else '',
                
                # Itens
                'itens_html': '\n'.join(itens_html)
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
    
    def formatar_valor(self, valor):
        """Formata valor monetário"""
        try:
            return f"{float(valor):.2f}"
        except:
            return "0.00"
    
    def gerar_html(self, dados):
        """
        Gera HTML do DANFE
        """
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>DANFE - NF-e {dados['numero']}</title>
    <style type="text/css">
        @page {{
            size: A4;
            margin: 10mm;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: "Times New Roman", serif;
            font-size: 8pt;
            color: #000;
        }}
        .page {{
            width: 190mm;
            margin: 0 auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 7pt;
        }}
        td, th {{
            border: 1px solid #000;
            padding: 2px;
            vertical-align: top;
        }}
        .nf-label {{
            font-size: 5pt;
            font-weight: bold;
            text-transform: uppercase;
            display: block;
            margin-bottom: 1px;
        }}
        .info {{
            font-size: 8pt;
            font-weight: bold;
            display: block;
        }}
        .txt-center {{ text-align: center; }}
        .txt-right {{ text-align: right; }}
        .txt-upper {{ text-transform: uppercase; }}
        .bold {{ font-weight: bold; }}
        .area-name {{
            font-size: 6pt;
            font-weight: bold;
            text-transform: uppercase;
            margin: 3px 0 1px;
        }}
        .logo {{
            width: 28mm;
            height: 28mm;
            object-fit: contain;
        }}
        .title {{
            font-size: 12pt;
            font-weight: bold;
            margin-bottom: 2mm;
        }}
        .entrada-saida {{
            border: 1px solid #000;
            width: 5mm;
            height: 5mm;
            display: inline-block;
            text-align: center;
            line-height: 5mm;
            font-weight: bold;
        }}
        .chave-acesso {{
            font-size: 9pt;
            font-weight: bold;
            letter-spacing: 1px;
        }}
        .produtos th {{
            background: #f0f0f0;
            font-size: 6pt;
            padding: 3px 2px;
        }}
        .produtos td {{
            font-size: 6pt;
            padding: 1px 2px;
        }}
    </style>
</head>
<body>
    <div class="page">
        <!-- Recebimento -->
        <table style="margin-bottom: 3mm;">
            <tr>
                <td colspan="2" class="txt-upper">
                    Recebemos de {dados['emit_nome']} os produtos e serviços constantes na nota fiscal indicada ao lado
                </td>
                <td rowspan="2" style="width: 32mm; text-align: center; vertical-align: middle;">
                    <div class="title">NF-e</div>
                    <div class="info">Nº {dados['numero']}</div>
                    <div class="info">Série {dados['serie']}</div>
                </td>
            </tr>
            <tr>
                <td style="width: 32mm">
                    <span class="nf-label">Data de recebimento</span>
                </td>
                <td>
                    <span class="nf-label">Identificação de assinatura do Recebedor</span>
                </td>
            </tr>
        </table>

        <!-- Cabeçalho -->
        <table style="margin-bottom: 0;">
            <tr>
                <td rowspan="3" style="width: 30mm; text-align: center;">
                    <!-- Logo da empresa -->
                    <div style="height: 28mm; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 10pt;">LOGO</span>
                    </div>
                </td>
                <td rowspan="3" style="width: 46mm; text-align: center; vertical-align: middle;">
                    <div class="bold" style="margin-bottom: 2mm;">{dados['emit_nome']}</div>
                    <div>{dados['emit_endereco']}</div>
                    <div>{dados['emit_bairro']} - {dados['emit_cep']}</div>
                    <div>{dados['emit_municipio']} - {dados['emit_uf']}</div>
                    <div>Fone: {dados['emit_fone']}</div>
                </td>
                <td rowspan="3" style="width: 34mm; text-align: center; vertical-align: middle;">
                    <div class="title">DANFE</div>
                    <div style="font-size: 7pt; margin-bottom: 2mm;">Documento Auxiliar da NF-e</div>
                    <div style="margin-bottom: 2mm;">
                        <span class="entrada-saida">{dados['tipo_operacao']}</span>
                        <div style="font-size: 5pt; margin-top: 1mm;">
                            <div>0 - Entrada</div>
                            <div>1 - Saída</div>
                        </div>
                    </div>
                    <div class="bold">Nº {dados['numero']}</div>
                    <div class="bold">SÉRIE {dados['serie']}</div>
                </td>
                <td style="width: 80mm; text-align: center;">
                    <span class="nf-label">Controle do Fisco</span>
                    <div style="margin-top: 3mm; font-size: 6pt;">Código de Barras</div>
                </td>
            </tr>
            <tr>
                <td style="text-align: center;">
                    <span class="nf-label">CHAVE DE ACESSO</span>
                    <div class="chave-acesso">{self.formatar_chave(dados['chave'])}</div>
                </td>
            </tr>
            <tr>
                <td style="text-align: center; font-size: 6pt;">
                    Consulta de autenticidade no portal nacional da NF-e<br>
                    www.nfe.fazenda.gov.br/portal ou no site da Sefaz Autorizada
                </td>
            </tr>
        </table>

        <!-- Natureza da Operação -->
        <table style="margin-top: -1px; margin-bottom: 0;">
            <tr>
                <td>
                    <span class="nf-label">NATUREZA DA OPERAÇÃO</span>
                    <span class="info">{dados['natureza']}</span>
                </td>
                <td style="width: 85mm;">
                    <span class="nf-label">PROTOCOLO DE AUTORIZAÇÃO DE USO</span>
                    <span class="info"></span>
                </td>
            </tr>
        </table>

        <!-- Inscrição -->
        <table style="margin-top: -1px; margin-bottom: 0;">
            <tr>
                <td>
                    <span class="nf-label">INSCRIÇÃO ESTADUAL</span>
                    <span class="info">{dados['emit_ie']}</span>
                </td>
                <td style="width: 67mm;">
                    <span class="nf-label">INSCRIÇÃO ESTADUAL DO SUBST. TRIB.</span>
                    <span class="info"></span>
                </td>
                <td style="width: 64mm;">
                    <span class="nf-label">CNPJ</span>
                    <span class="info">{dados['emit_cnpj']}</span>
                </td>
            </tr>
        </table>

        <!-- Destinatário -->
        <p class="area-name">Destinatário/Remetente</p>
        <table style="margin-bottom: 0;">
            <tr>
                <td>
                    <span class="nf-label">NOME/RAZÃO SOCIAL</span>
                    <span class="info">{dados['dest_nome']}</span>
                </td>
                <td style="width: 40mm;">
                    <span class="nf-label">CNPJ/CPF</span>
                    <span class="info">{dados['dest_cnpj_cpf']}</span>
                </td>
                <td style="width: 22mm;">
                    <span class="nf-label">DATA DE EMISSÃO</span>
                    <span class="info">{dados['data_emissao']}</span>
                </td>
            </tr>
            <tr>
                <td>
                    <span class="nf-label">ENDEREÇO</span>
                    <span class="info">{dados['dest_endereco']}</span>
                </td>
                <td>
                    <span class="nf-label">BAIRRO/DISTRITO</span>
                    <span class="info">{dados['dest_bairro']}</span>
                </td>
                <td>
                    <span class="nf-label">CEP</span>
                    <span class="info">{dados['dest_cep']}</span>
                </td>
            </tr>
            <tr>
                <td>
                    <span class="nf-label">MUNICÍPIO</span>
                    <span class="info">{dados['dest_municipio']}</span>
                </td>
                <td>
                    <span class="nf-label">FONE/FAX</span>
                    <span class="info">{dados['dest_fone']}</span>
                </td>
                <td>
                    <span class="nf-label">UF</span>
                    <span class="info">{dados['dest_uf']}</span>
                </td>
            </tr>
        </table>

        <!-- Cálculo do Imposto -->
        <p class="area-name">Cálculo do Imposto</p>
        <table style="margin-bottom: 0;">
            <tr>
                <td><span class="nf-label">BASE DE CÁLC. ICMS</span><span class="info txt-right">{dados['bc_icms']}</span></td>
                <td><span class="nf-label">VALOR DO ICMS</span><span class="info txt-right">{dados['valor_icms']}</span></td>
                <td><span class="nf-label">BASE CÁLC. ICMS ST</span><span class="info txt-right">{dados['bc_icms_st']}</span></td>
                <td><span class="nf-label">VALOR ICMS ST</span><span class="info txt-right">{dados['valor_icms_st']}</span></td>
                <td><span class="nf-label">V. TOTAL PRODUTOS</span><span class="info txt-right">{dados['valor_produtos']}</span></td>
            </tr>
            <tr>
                <td><span class="nf-label">VALOR DO FRETE</span><span class="info txt-right">{dados['valor_frete']}</span></td>
                <td><span class="nf-label">VALOR DO SEGURO</span><span class="info txt-right">{dados['valor_seguro']}</span></td>
                <td><span class="nf-label">DESCONTO</span><span class="info txt-right">{dados['valor_desconto']}</span></td>
                <td><span class="nf-label">OUTRAS DESP.</span><span class="info txt-right">{dados['valor_outras']}</span></td>
                <td><span class="nf-label">VALOR DO IPI</span><span class="info txt-right">{dados['valor_ipi']}</span></td>
            </tr>
            <tr>
                <td colspan="4"></td>
                <td style="background: #00A99D; color: white;"><span class="nf-label" style="color: white;">V. TOTAL DA NOTA</span><span class="info txt-right" style="color: white;">{dados['valor_total']}</span></td>
            </tr>
        </table>

        <!-- Transportador -->
        <p class="area-name">Transportador/Volumes Transportados</p>
        <table style="margin-bottom: 0;">
            <tr>
                <td colspan="2">
                    <span class="nf-label">RAZÃO SOCIAL</span>
                    <span class="info">{dados['transp_nome']}</span>
                </td>
                <td style="width: 30mm;">
                    <span class="nf-label">CNPJ/CPF</span>
                    <span class="info">{dados['transp_cnpj']}</span>
                </td>
            </tr>
        </table>

        <!-- Produtos/Serviços -->
        <p class="area-name">Dados do Produto/Serviço</p>
        <table class="produtos">
            <thead>
                <tr>
                    <th style="width: 15mm;">CÓDIGO</th>
                    <th>DESCRIÇÃO</th>
                    <th style="width: 15mm;">NCM</th>
                    <th style="width: 10mm;">CST</th>
                    <th style="width: 10mm;">CFOP</th>
                    <th style="width: 8mm;">UN</th>
                    <th style="width: 15mm;">QTD</th>
                    <th style="width: 18mm;">VL.UNIT</th>
                    <th style="width: 20mm;">VL.TOTAL</th>
                    <th style="width: 15mm;">BC ICMS</th>
                    <th style="width: 15mm;">VL.ICMS</th>
                    <th style="width: 15mm;">VL.IPI</th>
                    <th style="width: 12mm;">ALIQ.ICMS</th>
                    <th style="width: 12mm;">ALIQ.IPI</th>
                </tr>
            </thead>
            <tbody>
                {dados['itens_html']}
            </tbody>
        </table>

        <!-- Dados Adicionais -->
        <p class="area-name">Dados Adicionais</p>
        <table>
            <tr>
                <td style="height: 20mm;">
                    <span class="nf-label">INFORMAÇÕES COMPLEMENTARES</span>
                </td>
                <td style="width: 85mm;">
                    <span class="nf-label">RESERVADO AO FISCO</span>
                </td>
            </tr>
        </table>
    </div>
</body>
</html>
        """
        return html
    
    def gerar_pdf(self, xml_string):
        """
        Gera DANFE em PDF a partir do XML
        Retorna bytes do PDF
        """
        # Parse do XML
        dados = self.parse_xml(xml_string)
        
        # Gerar HTML
        html_content = self.gerar_html(dados)
        
        # Converter para PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        return pdf_bytes
