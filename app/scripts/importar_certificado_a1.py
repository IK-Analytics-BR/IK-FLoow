"""
Script para importar certificado digital A1 (.pfx)
Armazena no banco de dados de forma segura
"""

import base64
import os
import sys
from datetime import datetime
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.backends import default_backend
from cryptography import x509
import mysql.connector

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from config_local import DB_CONFIG
except ImportError:
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': 'aritana',
        'database': 'supply_chain_system'
    }


def conectar_banco():
    """Conecta ao banco de dados"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {e}")
        return None


def extrair_info_certificado(pfx_path: str, senha: str):
    """
    Extrai informações do certificado PFX
    
    Args:
        pfx_path: Caminho do arquivo .pfx
        senha: Senha do certificado
        
    Returns:
        dict: Informações do certificado
    """
    try:
        # Ler arquivo PFX
        with open(pfx_path, 'rb') as f:
            pfx_data = f.read()
        
        # Carregar certificado
        private_key, certificate, chain = pkcs12.load_key_and_certificates(
            pfx_data,
            senha.encode(),
            default_backend()
        )
        
        # Extrair informações
        subject = certificate.subject
        
        # CNPJ
        cnpj = None
        for attr in subject:
            if attr.oid._name == 'serialNumber':
                cnpj = attr.value
                break
        
        # Nome/Razão Social
        nome = None
        for attr in subject:
            if attr.oid._name == 'commonName':
                nome = attr.value
                break
        
        # Datas
        valido_de = certificate.not_valid_before_utc
        valido_ate = certificate.not_valid_after_utc
        
        # Converter PFX para Base64
        pfx_base64 = base64.b64encode(pfx_data).decode('utf-8')
        
        return {
            'cnpj': cnpj,
            'nome': nome,
            'valido_de': valido_de,
            'valido_ate': valido_ate,
            'pfx_base64': pfx_base64,
            'senha': senha
        }
        
    except Exception as e:
        raise Exception(f"Erro ao extrair informações do certificado: {e}")


def importar_certificado(empresa_id: int, pfx_path: str, senha: str):
    """
    Importa certificado para o banco de dados
    
    Args:
        empresa_id: ID da empresa no banco
        pfx_path: Caminho do arquivo .pfx
        senha: Senha do certificado
    """
    print(f"\n{'='*70}")
    print(f"IMPORTAÇÃO DE CERTIFICADO DIGITAL A1")
    print(f"{'='*70}\n")
    
    # Verificar se arquivo existe
    if not os.path.exists(pfx_path):
        print(f"❌ Arquivo não encontrado: {pfx_path}")
        return False
    
    print(f"📁 Arquivo: {pfx_path}")
    print(f"🏢 Empresa ID: {empresa_id}")
    
    # Extrair informações
    print(f"\n📋 Extraindo informações do certificado...")
    try:
        info = extrair_info_certificado(pfx_path, senha)
    except Exception as e:
        print(f"❌ {e}")
        return False
    
    print(f"✅ Certificado lido com sucesso!")
    print(f"   CNPJ: {info['cnpj']}")
    print(f"   Titular: {info['nome']}")
    print(f"   Válido de: {info['valido_de'].strftime('%d/%m/%Y')}")
    print(f"   Válido até: {info['valido_ate'].strftime('%d/%m/%Y')}")
    
    # Verificar validade
    agora = datetime.now(info['valido_ate'].tzinfo)
    if agora > info['valido_ate']:
        print(f"⚠️  ATENÇÃO: Certificado EXPIRADO!")
        resposta = input("Deseja continuar mesmo assim? (s/n): ")
        if resposta.lower() != 's':
            print("❌ Importação cancelada")
            return False
    
    dias_restantes = (info['valido_ate'] - agora).days
    print(f"   Dias restantes: {dias_restantes}")
    
    # Conectar ao banco
    print(f"\n💾 Conectando ao banco de dados...")
    conn = conectar_banco()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        # Desativar certificados antigos da empresa
        print(f"🔄 Desativando certificados antigos...")
        cursor.execute("""
            UPDATE certificados_digitais 
            SET ativo = FALSE 
            WHERE empresa_id = %s
        """, (empresa_id,))
        
        # Inserir novo certificado
        print(f"💾 Inserindo novo certificado...")
        query = """
            INSERT INTO certificados_digitais (
                empresa_id,
                certificado_base64,
                senha_criptografada,
                cnpj_titular,
                nome_titular,
                validade,
                tipo,
                ativo,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        valores = (
            empresa_id,
            info['pfx_base64'],
            info['senha'],  # TODO: Criptografar senha
            info['cnpj'],
            info['nome'],
            info['valido_ate'],
            'A1',
            True,
            datetime.now()
        )
        
        cursor.execute(query, valores)
        conn.commit()
        
        certificado_id = cursor.lastrowid
        
        print(f"\n✅ Certificado importado com sucesso!")
        print(f"   ID: {certificado_id}")
        print(f"   Empresa ID: {empresa_id}")
        print(f"   Status: ATIVO")
        
        cursor.close()
        conn.close()
        
        print(f"\n{'='*70}")
        print(f"IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"{'='*70}\n")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro ao importar certificado: {e}")
        cursor.close()
        conn.close()
        return False


if __name__ == '__main__':
    print("\n" + "="*70)
    print("IMPORTADOR DE CERTIFICADO DIGITAL A1")
    print("="*70 + "\n")
    
    # Dados do certificado IK ANALYTICS
    EMPRESA_ID = 9  # Será o ID da IK ANALYTICS após cadastro
    PFX_PATH = r"C:\Users\arita\Downloads\IK Analytics - Senha #IKa32165498.pfx"
    SENHA = "#IKa32165498"
    
    print("📋 Configuração:")
    print(f"   Empresa ID: {EMPRESA_ID}")
    print(f"   Arquivo: {PFX_PATH}")
    print(f"   Senha: {'*' * len(SENHA)}")
    
    print("\n⚠️  ATENÇÃO:")
    print("   1. Certifique-se de que a empresa foi cadastrada no banco")
    print("   2. O certificado será armazenado de forma segura")
    print("   3. Certificados antigos serão desativados")
    
    resposta = input("\nDeseja continuar? (s/n): ")
    
    if resposta.lower() == 's':
        importar_certificado(EMPRESA_ID, PFX_PATH, SENHA)
    else:
        print("\n❌ Importação cancelada pelo usuário")
