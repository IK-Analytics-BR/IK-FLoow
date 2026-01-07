"""
Script para descompactar arquivos Empresas*.zip
"""
import zipfile
import os
from pathlib import Path

# Diretório dos arquivos
DIR = r"C:\Users\arita\CascadeProjects\SupplyChainSystem\app\scripts\downloads_receita"

def descompactar_empresas():
    """Descompacta todos os arquivos Empresas*.zip"""
    
    print("\n" + "="*60)
    print("DESCOMPACTANDO ARQUIVOS EMPRESAS")
    print("="*60)
    
    # Listar arquivos .zip
    arquivos_zip = [f for f in os.listdir(DIR) if f.startswith('Empresas') and f.endswith('.zip')]
    arquivos_zip.sort()
    
    if not arquivos_zip:
        print(f"\n[ERRO] Nenhum arquivo Empresas*.zip encontrado em {DIR}")
        return
    
    print(f"\n[ENCONTRADOS] {len(arquivos_zip)} arquivo(s) ZIP:")
    for arq in arquivos_zip:
        tamanho_mb = os.path.getsize(os.path.join(DIR, arq)) / (1024*1024)
        print(f"  - {arq} ({tamanho_mb:.1f} MB)")
    
    print(f"\n[INICIANDO] Descompactação...")
    
    total_descompactados = 0
    
    for arquivo_zip in arquivos_zip:
        caminho_zip = os.path.join(DIR, arquivo_zip)
        
        # Verificar se CSV já existe
        nome_csv = arquivo_zip.replace('.zip', '.csv')
        caminho_csv = os.path.join(DIR, nome_csv)
        
        if os.path.exists(caminho_csv):
            print(f"\n[PULANDO] {arquivo_zip} - CSV já existe")
            continue
        
        print(f"\n[DESCOMPACTANDO] {arquivo_zip}...")
        
        try:
            with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                # Listar arquivos no ZIP
                arquivos_dentro = zip_ref.namelist()
                
                if len(arquivos_dentro) == 0:
                    print(f"  [AVISO] ZIP vazio!")
                    continue
                
                # Extrair todos os arquivos
                zip_ref.extractall(DIR)
                
                print(f"  [OK] Extraido: {', '.join(arquivos_dentro)}")
                total_descompactados += 1
                
        except Exception as e:
            print(f"  [ERRO] Erro ao descompactar: {e}")
    
    print("\n" + "="*60)
    print(f"[CONCLUÍDO] {total_descompactados} arquivo(s) descompactado(s)")
    print("="*60)
    
    # Listar CSVs resultantes
    arquivos_csv = [f for f in os.listdir(DIR) if f.startswith('Empresas') and f.endswith('.csv')]
    
    if arquivos_csv:
        print(f"\n[RESULTADO] {len(arquivos_csv)} arquivo(s) CSV disponível(is):")
        for arq in sorted(arquivos_csv):
            tamanho_mb = os.path.getsize(os.path.join(DIR, arq)) / (1024*1024)
            print(f"  - {arq} ({tamanho_mb:.1f} MB)")
    else:
        print("\n[AVISO] Nenhum arquivo CSV foi gerado!")

if __name__ == "__main__":
    descompactar_empresas()
    print("\n[OK] Agora voce pode executar: python app\\scripts\\importar_empresas_receita.py")
