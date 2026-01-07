#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Serviço de Envio de Email para NF-e
- Envio automático de NF-e autorizada
- Envio de cancelamento
- Envio de Carta de Correção (CC-e)
- Geração de PDF da CC-e
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, Optional, List
import tempfile

# Ajuste de path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from app.database import get_db
except ImportError:
    from database import get_db


class EmailNFeService:
    """Serviço de envio de emails para NF-e"""
    
    def __init__(self, empresa_id: int):
        self.empresa_id = empresa_id
        self.config = None
        self.db = get_db()
        self._carregar_configuracao()
    
    def _carregar_configuracao(self):
        """Carrega configuração de email da empresa"""
        try:
            self.config = self.db.fetch_one("""
                SELECT * FROM email_config_nfe 
                WHERE empresa_id = %s AND ativo = 1
            """, (self.empresa_id,))
        except Exception as e:
            print(f"[EMAIL-NFe] Erro ao carregar config: {e}")
            self.config = None
    
    def esta_configurado(self) -> bool:
        """Verifica se email está configurado para a empresa"""
        return self.config is not None
    
    def enviar_nfe_autorizada(self, nfe_data: Dict, xml_content: str = None, 
                               danfe_pdf: bytes = None) -> Dict:
        """
        Envia email com NF-e autorizada
        
        Args:
            nfe_data: Dados da NF-e (numero, serie, chave, cliente_email, etc)
            xml_content: Conteúdo do XML da NF-e
            danfe_pdf: PDF do DANFE em bytes
        """
        if not self.config or not self.config.get('enviar_nfe_autorizada'):
            return {'sucesso': False, 'erro': 'Envio de email não configurado'}
        
        email_dest = nfe_data.get('cliente_email')
        if not email_dest:
            return {'sucesso': False, 'erro': 'Cliente não possui email cadastrado'}
        
        # Montar assunto
        assunto = self.config.get('assunto_nfe_autorizada', 'NF-e Autorizada - {numero}/{serie}')
        assunto = assunto.replace('{numero}', str(nfe_data.get('numero', '')))
        assunto = assunto.replace('{serie}', str(nfe_data.get('serie', '')))
        
        # Corpo do email
        corpo = self._gerar_corpo_nfe_autorizada(nfe_data)
        
        # Anexos
        anexos = []
        if xml_content and self.config.get('anexar_xml'):
            anexos.append({
                'nome': f"NFe_{nfe_data.get('numero')}_{nfe_data.get('serie')}.xml",
                'conteudo': xml_content.encode('utf-8'),
                'tipo': 'application/xml'
            })
        
        if danfe_pdf and self.config.get('anexar_danfe'):
            anexos.append({
                'nome': f"DANFE_{nfe_data.get('numero')}_{nfe_data.get('serie')}.pdf",
                'conteudo': danfe_pdf,
                'tipo': 'application/pdf'
            })
        
        return self._enviar_email(
            destinatario=email_dest,
            nome_dest=nfe_data.get('cliente_nome'),
            assunto=assunto,
            corpo_html=corpo,
            anexos=anexos,
            tipo_documento='nfe',
            chave_nfe=nfe_data.get('chave'),
            numero_nfe=nfe_data.get('numero'),
            serie_nfe=nfe_data.get('serie')
        )
    
    def enviar_nfe_cancelada(self, nfe_data: Dict) -> Dict:
        """Envia email informando cancelamento da NF-e"""
        if not self.config or not self.config.get('enviar_nfe_cancelada'):
            return {'sucesso': False, 'erro': 'Envio de email não configurado'}
        
        email_dest = nfe_data.get('cliente_email')
        if not email_dest:
            return {'sucesso': False, 'erro': 'Cliente não possui email cadastrado'}
        
        assunto = self.config.get('assunto_nfe_cancelada', 'NF-e Cancelada - {numero}/{serie}')
        assunto = assunto.replace('{numero}', str(nfe_data.get('numero', '')))
        assunto = assunto.replace('{serie}', str(nfe_data.get('serie', '')))
        
        corpo = self._gerar_corpo_nfe_cancelada(nfe_data)
        
        return self._enviar_email(
            destinatario=email_dest,
            nome_dest=nfe_data.get('cliente_nome'),
            assunto=assunto,
            corpo_html=corpo,
            tipo_documento='cancelamento',
            chave_nfe=nfe_data.get('chave'),
            numero_nfe=nfe_data.get('numero'),
            serie_nfe=nfe_data.get('serie')
        )
    
    def enviar_cce(self, nfe_data: Dict, cce_data: Dict, pdf_cce: bytes = None) -> Dict:
        """
        Envia email com Carta de Correção
        
        Args:
            nfe_data: Dados da NF-e
            cce_data: Dados da CC-e (sequencia, correcao, protocolo)
            pdf_cce: PDF da CC-e em bytes
        """
        if not self.config or not self.config.get('enviar_cce'):
            return {'sucesso': False, 'erro': 'Envio de email não configurado'}
        
        email_dest = nfe_data.get('cliente_email')
        if not email_dest:
            return {'sucesso': False, 'erro': 'Cliente não possui email cadastrado'}
        
        assunto = self.config.get('assunto_cce', 'Carta de Correção - NF-e {numero}/{serie}')
        assunto = assunto.replace('{numero}', str(nfe_data.get('numero', '')))
        assunto = assunto.replace('{serie}', str(nfe_data.get('serie', '')))
        
        corpo = self._gerar_corpo_cce(nfe_data, cce_data)
        
        anexos = []
        if pdf_cce:
            anexos.append({
                'nome': f"CCe_{nfe_data.get('numero')}_{nfe_data.get('serie')}_seq{cce_data.get('sequencia')}.pdf",
                'conteudo': pdf_cce,
                'tipo': 'application/pdf'
            })
        
        return self._enviar_email(
            destinatario=email_dest,
            nome_dest=nfe_data.get('cliente_nome'),
            assunto=assunto,
            corpo_html=corpo,
            anexos=anexos,
            tipo_documento='cce',
            chave_nfe=nfe_data.get('chave'),
            numero_nfe=nfe_data.get('numero'),
            serie_nfe=nfe_data.get('serie')
        )
    
    def _enviar_email(self, destinatario: str, nome_dest: str, assunto: str,
                      corpo_html: str, anexos: List[Dict] = None,
                      tipo_documento: str = 'nfe', chave_nfe: str = None,
                      numero_nfe: int = None, serie_nfe: int = None) -> Dict:
        """Envia o email usando SMTP"""
        try:
            msg = MIMEMultipart()
            msg['From'] = f"{self.config.get('nome_remetente', '')} <{self.config['email_remetente']}>"
            msg['To'] = destinatario
            msg['Subject'] = assunto
            
            # Cópia
            if self.config.get('email_copia'):
                msg['Cc'] = self.config['email_copia']
            
            # Corpo HTML
            msg.attach(MIMEText(corpo_html, 'html', 'utf-8'))
            
            # Anexos
            if anexos:
                for anexo in anexos:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(anexo['conteudo'])
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f"attachment; filename={anexo['nome']}")
                    msg.attach(part)
            
            # Conectar ao SMTP
            if self.config.get('smtp_ssl'):
                server = smtplib.SMTP_SSL(self.config['smtp_server'], self.config['smtp_port'])
            else:
                server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
                server.starttls()
            
            server.login(self.config['email_usuario'], self.config['email_senha'])
            
            # Lista de destinatários
            destinatarios = [destinatario]
            if self.config.get('email_copia'):
                destinatarios.append(self.config['email_copia'])
            if self.config.get('email_copia_oculta'):
                destinatarios.append(self.config['email_copia_oculta'])
            
            server.sendmail(self.config['email_remetente'], destinatarios, msg.as_string())
            server.quit()
            
            # Registrar log
            self._registrar_log(
                tipo_documento=tipo_documento,
                chave_nfe=chave_nfe,
                numero_nfe=numero_nfe,
                serie_nfe=serie_nfe,
                email_dest=destinatario,
                nome_dest=nome_dest,
                status='enviado'
            )
            
            print(f"[EMAIL-NFe] Email enviado com sucesso para {destinatario}")
            return {'sucesso': True, 'mensagem': f'Email enviado para {destinatario}'}
            
        except Exception as e:
            print(f"[EMAIL-NFe] Erro ao enviar email: {e}")
            
            # Registrar log de erro
            self._registrar_log(
                tipo_documento=tipo_documento,
                chave_nfe=chave_nfe,
                numero_nfe=numero_nfe,
                serie_nfe=serie_nfe,
                email_dest=destinatario,
                nome_dest=nome_dest,
                status='erro',
                mensagem_erro=str(e)
            )
            
            return {'sucesso': False, 'erro': str(e)}
    
    def _registrar_log(self, tipo_documento: str, chave_nfe: str, numero_nfe: int,
                       serie_nfe: int, email_dest: str, nome_dest: str,
                       status: str, mensagem_erro: str = None):
        """Registra log de envio de email"""
        try:
            self.db.execute_query("""
                INSERT INTO email_log_nfe (
                    empresa_id, tipo_documento, chave_nfe, numero_nfe, serie_nfe,
                    email_destinatario, nome_destinatario, status, mensagem_erro, data_envio
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                self.empresa_id, tipo_documento, chave_nfe, numero_nfe, serie_nfe,
                email_dest, nome_dest, status, mensagem_erro,
                datetime.now() if status == 'enviado' else None
            ))
        except Exception as e:
            print(f"[EMAIL-NFe] Erro ao registrar log: {e}")
    
    def _gerar_corpo_nfe_autorizada(self, nfe_data: Dict) -> str:
        """Gera corpo HTML do email de NF-e autorizada"""
        empresa_nome = nfe_data.get('empresa_nome', 'Empresa')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #28a745; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .info {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #28a745; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ NF-e Autorizada</h1>
                </div>
                <div class="content">
                    <p>Prezado(a) <strong>{nfe_data.get('cliente_nome', 'Cliente')}</strong>,</p>
                    
                    <p>Informamos que sua Nota Fiscal Eletrônica foi <strong>autorizada</strong> pela SEFAZ.</p>
                    
                    <div class="info">
                        <p><strong>Número:</strong> {nfe_data.get('numero')}</p>
                        <p><strong>Série:</strong> {nfe_data.get('serie')}</p>
                        <p><strong>Chave de Acesso:</strong><br>
                        <code style="word-break: break-all;">{nfe_data.get('chave', '')}</code></p>
                        <p><strong>Data de Emissão:</strong> {nfe_data.get('data_emissao', '')}</p>
                        <p><strong>Valor Total:</strong> R$ {nfe_data.get('valor_total', '0.00')}</p>
                    </div>
                    
                    <p>Em anexo você encontra:</p>
                    <ul>
                        <li>XML da NF-e (arquivo fiscal)</li>
                        <li>DANFE em PDF (documento auxiliar)</li>
                    </ul>
                    
                    <p>Para consultar a autenticidade da NF-e, acesse:<br>
                    <a href="https://www.nfe.fazenda.gov.br/portal/consultaRecaptcha.aspx">Portal Nacional da NF-e</a></p>
                </div>
                <div class="footer">
                    <p>Este é um email automático enviado por {empresa_nome}.<br>
                    Por favor, não responda a este email.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _gerar_corpo_nfe_cancelada(self, nfe_data: Dict) -> str:
        """Gera corpo HTML do email de NF-e cancelada"""
        empresa_nome = nfe_data.get('empresa_nome', 'Empresa')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .info {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #dc3545; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚫 NF-e Cancelada</h1>
                </div>
                <div class="content">
                    <p>Prezado(a) <strong>{nfe_data.get('cliente_nome', 'Cliente')}</strong>,</p>
                    
                    <p>Informamos que a Nota Fiscal Eletrônica abaixo foi <strong>cancelada</strong>.</p>
                    
                    <div class="info">
                        <p><strong>Número:</strong> {nfe_data.get('numero')}</p>
                        <p><strong>Série:</strong> {nfe_data.get('serie')}</p>
                        <p><strong>Chave de Acesso:</strong><br>
                        <code style="word-break: break-all;">{nfe_data.get('chave', '')}</code></p>
                        <p><strong>Protocolo Cancelamento:</strong> {nfe_data.get('protocolo_cancelamento', '')}</p>
                    </div>
                    
                    <p>Caso tenha dúvidas, entre em contato conosco.</p>
                </div>
                <div class="footer">
                    <p>Este é um email automático enviado por {empresa_nome}.<br>
                    Por favor, não responda a este email.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _gerar_corpo_cce(self, nfe_data: Dict, cce_data: Dict) -> str:
        """Gera corpo HTML do email de CC-e"""
        empresa_nome = nfe_data.get('empresa_nome', 'Empresa')
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #ffc107; color: #333; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .info {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #ffc107; }}
                .correcao {{ background: #fff3cd; padding: 15px; margin: 10px 0; border: 1px solid #ffc107; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📝 Carta de Correção Eletrônica</h1>
                </div>
                <div class="content">
                    <p>Prezado(a) <strong>{nfe_data.get('cliente_nome', 'Cliente')}</strong>,</p>
                    
                    <p>Informamos que foi emitida uma <strong>Carta de Correção</strong> para a NF-e abaixo:</p>
                    
                    <div class="info">
                        <p><strong>NF-e Número:</strong> {nfe_data.get('numero')}</p>
                        <p><strong>Série:</strong> {nfe_data.get('serie')}</p>
                        <p><strong>Chave de Acesso:</strong><br>
                        <code style="word-break: break-all;">{nfe_data.get('chave', '')}</code></p>
                    </div>
                    
                    <div class="info">
                        <p><strong>Sequência da CC-e:</strong> {cce_data.get('sequencia')}</p>
                        <p><strong>Protocolo:</strong> {cce_data.get('protocolo', '')}</p>
                        <p><strong>Data/Hora:</strong> {cce_data.get('data_registro', '')}</p>
                    </div>
                    
                    <div class="correcao">
                        <p><strong>Texto da Correção:</strong></p>
                        <p>{cce_data.get('correcao', '')}</p>
                    </div>
                    
                    <p>Em anexo você encontra o PDF da Carta de Correção.</p>
                    
                    <p><small><em>A Carta de Correção é disciplinada pelo § 1º-A do art. 7º do Convênio S/N, 
                    de 15 de dezembro de 1970 e pode ser utilizada para regularização de erro ocorrido na 
                    emissão de documento fiscal, desde que o erro não esteja relacionado com as variáveis 
                    que determinam o valor do imposto.</em></small></p>
                </div>
                <div class="footer">
                    <p>Este é um email automático enviado por {empresa_nome}.<br>
                    Por favor, não responda a este email.</p>
                </div>
            </div>
        </body>
        </html>
        """


class GerarPDFCCe:
    """Gera PDF da Carta de Correção Eletrônica"""
    
    @staticmethod
    def gerar(nfe_data: Dict, cce_data: Dict, empresa_data: Dict = None) -> bytes:
        """
        Gera PDF da CC-e
        
        Args:
            nfe_data: Dados da NF-e
            cce_data: Dados da CC-e
            empresa_data: Dados da empresa (opcional)
        
        Returns:
            bytes do PDF
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
            import io
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                   leftMargin=20*mm, rightMargin=20*mm,
                                   topMargin=20*mm, bottomMargin=20*mm)
            
            styles = getSampleStyleSheet()
            
            # Estilos customizados
            titulo_style = ParagraphStyle(
                'Titulo', parent=styles['Heading1'],
                fontSize=16, alignment=TA_CENTER, spaceAfter=10
            )
            subtitulo_style = ParagraphStyle(
                'Subtitulo', parent=styles['Heading2'],
                fontSize=12, alignment=TA_CENTER, spaceAfter=20
            )
            normal_style = ParagraphStyle(
                'Normal', parent=styles['Normal'],
                fontSize=10, alignment=TA_LEFT
            )
            correcao_style = ParagraphStyle(
                'Correcao', parent=styles['Normal'],
                fontSize=10, alignment=TA_JUSTIFY, 
                borderWidth=1, borderColor=colors.orange,
                borderPadding=10, backColor=colors.lightyellow
            )
            condicao_style = ParagraphStyle(
                'Condicao', parent=styles['Normal'],
                fontSize=8, alignment=TA_JUSTIFY, textColor=colors.grey
            )
            
            elementos = []
            
            # Título
            elementos.append(Paragraph("CARTA DE CORREÇÃO ELETRÔNICA", titulo_style))
            elementos.append(Paragraph("CC-e - Evento 110110", subtitulo_style))
            elementos.append(Spacer(1, 10*mm))
            
            # Dados da empresa (se disponível)
            if empresa_data:
                elementos.append(Paragraph(f"<b>{empresa_data.get('razao_social', '')}</b>", normal_style))
                elementos.append(Paragraph(f"CNPJ: {empresa_data.get('cnpj', '')}", normal_style))
                elementos.append(Spacer(1, 5*mm))
            
            # Dados da NF-e
            elementos.append(Paragraph("<b>DADOS DA NF-e CORRIGIDA</b>", normal_style))
            dados_nfe = [
                ['Número:', str(nfe_data.get('numero', '')), 'Série:', str(nfe_data.get('serie', ''))],
                ['Chave de Acesso:', nfe_data.get('chave', ''), '', ''],
            ]
            t = Table(dados_nfe, colWidths=[30*mm, 50*mm, 20*mm, 30*mm])
            t.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
                ('SPAN', (1, 1), (3, 1)),
            ]))
            elementos.append(t)
            elementos.append(Spacer(1, 5*mm))
            
            # Dados da CC-e
            elementos.append(Paragraph("<b>DADOS DA CARTA DE CORREÇÃO</b>", normal_style))
            dados_cce = [
                ['Sequência:', str(cce_data.get('sequencia', '')), 'Protocolo:', str(cce_data.get('protocolo', ''))],
                ['Data/Hora:', str(cce_data.get('data_registro', '')), '', ''],
            ]
            t = Table(dados_cce, colWidths=[30*mm, 50*mm, 25*mm, 50*mm])
            t.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ]))
            elementos.append(t)
            elementos.append(Spacer(1, 10*mm))
            
            # Texto da correção
            elementos.append(Paragraph("<b>CORREÇÃO:</b>", normal_style))
            elementos.append(Spacer(1, 3*mm))
            elementos.append(Paragraph(cce_data.get('correcao', ''), correcao_style))
            elementos.append(Spacer(1, 10*mm))
            
            # Condição de uso
            condicao_uso = (
                "A Carta de Correção é disciplinada pelo § 1º-A do art. 7º do Convênio S/N, "
                "de 15 de dezembro de 1970 e pode ser utilizada para regularização de erro "
                "ocorrido na emissão de documento fiscal, desde que o erro não esteja "
                "relacionado com: I - as variáveis que determinam o valor do imposto tais "
                "como: base de cálculo, alíquota, diferença de preço, quantidade, valor da "
                "operação ou da prestação; II - a correção de dados cadastrais que implique "
                "mudança do remetente ou do destinatário; III - a data de emissão ou de saída."
            )
            elementos.append(Paragraph("<b>CONDIÇÕES DE USO:</b>", normal_style))
            elementos.append(Paragraph(condicao_uso, condicao_style))
            
            # Gerar PDF
            doc.build(elementos)
            buffer.seek(0)
            return buffer.read()
            
        except Exception as e:
            print(f"[PDF-CCe] Erro ao gerar PDF: {e}")
            import traceback
            traceback.print_exc()
            return None
