"""
Script para popular especificações técnicas baseadas no descritivo dos produtos
Extrai informações como largura, comprimento, tipo de correia, material do nome do produto
"""
import sys
import os
import re

# Adicionar path do app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.database import Database

def extrair_dimensoes(nome):
    """
    Extrai dimensões do nome do produto
    Exemplos:
    - "CORREIA 600 X 3000" -> largura=600, comprimento=3000
    - "- 600 H 200 DZ" -> largura=600, altura=200
    - "CORREIA T10 25MM X 1000MM" -> largura=25, comprimento=1000
    """
    dimensoes = {
        'largura_mm': None,
        'comprimento_mm': None,
        'espessura_mm': None
    }
    
    nome_upper = nome.upper()
    
    # Padrão: XXX X YYYY ou XXX x YYYY (largura x comprimento)
    match = re.search(r'(\d+)\s*[Xx]\s*(\d+)', nome)
    if match:
        dimensoes['largura_mm'] = float(match.group(1))
        dimensoes['comprimento_mm'] = float(match.group(2))
    
    # Padrão: - XXX H YYY (largura H altura)
    match_h = re.search(r'-\s*(\d+)\s*H\s*(\d+)', nome_upper)
    if match_h:
        dimensoes['largura_mm'] = float(match_h.group(1))
        dimensoes['comprimento_mm'] = float(match_h.group(2))
    
    # Padrão: XXXmm ou XXX mm (largura)
    match_mm = re.search(r'(\d+)\s*MM', nome_upper)
    if match_mm and not dimensoes['largura_mm']:
        dimensoes['largura_mm'] = float(match_mm.group(1))
    
    # Padrão: Largura específica (L=XXX ou LARG XXX)
    match_larg = re.search(r'(?:L=|LARG[URA]*\s*)(\d+)', nome_upper)
    if match_larg:
        dimensoes['largura_mm'] = float(match_larg.group(1))
    
    # Padrão: Espessura (ESP XXX ou E=XXX)
    match_esp = re.search(r'(?:ESP[ESSURA]*\s*|E=)(\d+(?:[.,]\d+)?)', nome_upper)
    if match_esp:
        dimensoes['espessura_mm'] = float(match_esp.group(1).replace(',', '.'))
    
    return dimensoes


def identificar_tipo_correia(nome):
    """
    Identifica o tipo de correia baseado no nome
    Retorna o código do tipo
    """
    nome_upper = nome.upper()
    
    # Sincronizadas
    if any(x in nome_upper for x in ['T5', 'T10', 'T20', 'AT5', 'AT10', 'AT20', 'HTD', 'SINCRONI']):
        return 'SIN'
    
    # Poly-V
    if any(x in nome_upper for x in ['PJ', 'PK', 'PL', 'PM', 'POLY-V', 'POLYV', 'PV ']):
        return 'PV'
    
    # Transportadora
    if any(x in nome_upper for x in ['TRANSPORT', 'ELEVADOR', 'ESTEIRA']):
        return 'TRA'
    
    # Plana
    if 'PLANA' in nome_upper:
        return 'PLA'
    
    # Modular
    if 'MODULAR' in nome_upper:
        return 'MOD'
    
    # Dentada
    if any(x in nome_upper for x in ['DENTAD', 'DENTE', 'DT', 'DZ']):
        return 'DEN'
    
    # Default: Transportadora (comum em fábricas de correias)
    return 'TRA'


def identificar_material(nome):
    """
    Identifica o material baseado no nome
    Retorna o código do material
    """
    nome_upper = nome.upper()
    
    if any(x in nome_upper for x in ['PU', 'POLIURETANO', 'URETANO']):
        return 'PU'
    
    if 'PVC' in nome_upper:
        return 'PVC'
    
    if any(x in nome_upper for x in ['BORRACHA', 'RUBBER']):
        return 'BOR'
    
    if any(x in nome_upper for x in ['NBR', 'NITRIL']):
        return 'NBR'
    
    if any(x in nome_upper for x in ['SILICONE', 'SIL ']):
        return 'SIL'
    
    if any(x in nome_upper for x in ['NEOPRENE', 'NEO ']):
        return 'NEO'
    
    if 'EPDM' in nome_upper:
        return 'EPD'
    
    if any(x in nome_upper for x in ['TEFLON', 'PTFE']):
        return 'TFL'
    
    # Default: PU (comum em correias industriais)
    return 'PU'


def identificar_perfil(nome):
    """
    Identifica o perfil da correia baseado no nome
    """
    nome_upper = nome.upper()
    
    # Sincronizadas métricas
    perfis = ['AT20', 'AT10', 'AT5', 'T20', 'T10', 'T5', 'T2.5', 
              'HTD14M', 'HTD8M', 'HTD5M', 'HTD3M']
    for perfil in perfis:
        if perfil in nome_upper:
            return perfil
    
    # Sincronizadas polegadas
    perfis_pol = ['XXH', 'XH', 'XL', 'MXL', ' H ', ' L ']
    for perfil in perfis_pol:
        if perfil in nome_upper or nome_upper.startswith(perfil.strip()):
            return perfil.strip()
    
    # Poly-V
    for perfil in ['PJ', 'PK', 'PL', 'PM']:
        if perfil in nome_upper:
            return perfil
    
    return None


def identificar_numero_lonas(nome):
    """
    Identifica o número de lonas baseado no nome
    """
    nome_upper = nome.upper()
    
    # Padrão: 2L, 3L, 4L (número de lonas)
    match = re.search(r'(\d)\s*L(?:ONA)?', nome_upper)
    if match:
        return int(match.group(1))
    
    # EP400/3 = 3 lonas
    match_ep = re.search(r'EP\d+/(\d)', nome_upper)
    if match_ep:
        return int(match_ep.group(1))
    
    return None


def identificar_cor(nome):
    """Identifica a cor baseado no nome"""
    nome_upper = nome.upper()
    
    cores = {
        'BRANCA': 'Branca', 'BRANCO': 'Branca', 'WHITE': 'Branca',
        'PRETA': 'Preta', 'PRETO': 'Preta', 'BLACK': 'Preta',
        'VERDE': 'Verde', 'GREEN': 'Verde',
        'AZUL': 'Azul', 'BLUE': 'Azul',
        'CINZA': 'Cinza', 'GRAY': 'Cinza', 'GREY': 'Cinza',
        'VERMELHA': 'Vermelha', 'VERMELHO': 'Vermelha', 'RED': 'Vermelha',
        'LARANJA': 'Laranja', 'ORANGE': 'Laranja',
        'AMARELA': 'Amarela', 'AMARELO': 'Amarela', 'YELLOW': 'Amarela',
        'TRANSPARENTE': 'Transparente', 'CLEAR': 'Transparente'
    }
    
    for termo, cor in cores.items():
        if termo in nome_upper:
            return cor
    
    return None


def main():
    db = Database()
    
    print("=" * 60)
    print("POPULAR ESPECIFICAÇÕES TÉCNICAS A PARTIR DO DESCRITIVO")
    print("=" * 60)
    
    # Buscar tipos de correia
    tipos = db.fetch_all("SELECT id, codigo FROM tipos_correia")
    tipos_map = {t['codigo']: t['id'] for t in tipos} if tipos else {}
    
    # Buscar materiais
    materiais = db.fetch_all("SELECT id, codigo FROM materiais_correia")
    materiais_map = {m['codigo']: m['id'] for m in materiais} if materiais else {}
    
    # Buscar perfis
    perfis = db.fetch_all("SELECT id, codigo FROM perfis_correia")
    perfis_map = {p['codigo']: p['id'] for p in perfis} if perfis else {}
    
    print(f"Tipos de correia: {len(tipos_map)}")
    print(f"Materiais: {len(materiais_map)}")
    print(f"Perfis: {len(perfis_map)}")
    
    # Buscar produtos de produção que ainda não têm especificação
    produtos = db.fetch_all("""
        SELECT p.id, p.name, p.internal_code, p.category_id
        FROM products p
        LEFT JOIN produto_especificacoes_tecnicas pet ON pet.produto_id = p.id
        WHERE pet.id IS NULL
          AND (
              p.name LIKE '%CORREIA%'
              OR p.name LIKE '% X %'
              OR p.name LIKE '% H %'
              OR p.name LIKE '%T5%'
              OR p.name LIKE '%T10%'
              OR p.name LIKE '%PU %'
              OR p.name LIKE '%TRANSPORT%'
              OR p.name LIKE '%ESTEIRA%'
              OR p.name LIKE '%SINCRONI%'
              OR p.name LIKE '%DENTAD%'
              OR p.internal_code LIKE 'PROD-%'
              OR p.internal_code LIKE 'COR-%'
          )
        ORDER BY p.id
        LIMIT 100
    """)
    
    if not produtos:
        print("Nenhum produto encontrado para processar.")
        return
    
    print(f"\nEncontrados {len(produtos)} produtos para processar")
    print("-" * 60)
    
    inseridos = 0
    erros = 0
    
    for produto in produtos:
        try:
            nome = produto['name'] or ''
            
            # Extrair informações do nome
            dimensoes = extrair_dimensoes(nome)
            tipo_codigo = identificar_tipo_correia(nome)
            material_codigo = identificar_material(nome)
            perfil_codigo = identificar_perfil(nome)
            num_lonas = identificar_numero_lonas(nome)
            cor = identificar_cor(nome)
            
            # Mapear para IDs
            tipo_id = tipos_map.get(tipo_codigo)
            material_id = materiais_map.get(material_codigo)
            perfil_id = perfis_map.get(perfil_codigo) if perfil_codigo else None
            
            # Gerar código DNA simples
            codigo_dna = f"{tipo_codigo or 'XXX'}-{material_codigo or 'XXX'}"
            if perfil_codigo:
                codigo_dna += f"-{perfil_codigo}"
            if dimensoes['largura_mm']:
                codigo_dna += f"-L{int(dimensoes['largura_mm'])}"
            if dimensoes['comprimento_mm']:
                codigo_dna += f"-C{int(dimensoes['comprimento_mm'])}"
            
            # Inserir especificação
            db.execute("""
                INSERT INTO produto_especificacoes_tecnicas 
                (produto_id, largura_mm, comprimento_mm, espessura_mm,
                 tipo_correia_id, material_base_id, perfil_id,
                 cor, numero_lonas, codigo_dna, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                produto['id'],
                dimensoes['largura_mm'],
                dimensoes['comprimento_mm'],
                dimensoes['espessura_mm'],
                tipo_id,
                material_id,
                perfil_id,
                cor,
                num_lonas,
                codigo_dna
            ))
            
            # Atualizar flag no produto
            db.execute("""
                UPDATE products SET tem_especificacao_tecnica = 1 WHERE id = %s
            """, (produto['id'],))
            
            inseridos += 1
            print(f"[OK] #{produto['id']} - {nome[:50]}")
            print(f"      DNA: {codigo_dna} | L={dimensoes['largura_mm']} C={dimensoes['comprimento_mm']}")
            
        except Exception as e:
            erros += 1
            print(f"[ERRO] #{produto['id']} - {produto['name'][:40]}: {e}")
    
    print("\n" + "=" * 60)
    print(f"RESULTADO: {inseridos} inseridos, {erros} erros")
    print("=" * 60)
    
    # Mostrar estatísticas
    stats = db.fetch_one("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT tipo_correia_id) as tipos,
            COUNT(DISTINCT material_base_id) as materiais,
            COUNT(CASE WHEN largura_mm IS NOT NULL THEN 1 END) as com_largura,
            COUNT(CASE WHEN comprimento_mm IS NOT NULL THEN 1 END) as com_comprimento
        FROM produto_especificacoes_tecnicas
    """)
    
    if stats:
        print(f"\nEstatísticas gerais:")
        print(f"  Total de especificações: {stats['total']}")
        print(f"  Tipos de correia diferentes: {stats['tipos']}")
        print(f"  Materiais diferentes: {stats['materiais']}")
        print(f"  Com largura definida: {stats['com_largura']}")
        print(f"  Com comprimento definido: {stats['com_comprimento']}")


if __name__ == "__main__":
    main()
