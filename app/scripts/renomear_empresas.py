"""
Renomeia arquivos .EMPRECSV para .csv com nome correto
"""
import os
import re

DIR = r"C:\Users\arita\CascadeProjects\SupplyChainSystem\app\scripts\downloads_receita"

def renomear_arquivos():
    print("\n[RENOMEANDO] Arquivos EMPRECSV para CSV...")
    
    # Listar arquivos .EMPRECSV
    for arquivo in os.listdir(DIR):
        if arquivo.endswith('.EMPRECSV'):
            # Extrair número do nome (ex: K3241.K03200Y0.D50913.EMPRECSV -> 0)
            match = re.search(r'Y(\d)', arquivo)
            if match:
                numero = match.group(1)
                novo_nome = f"Empresas{numero}.csv"
                
                caminho_antigo = os.path.join(DIR, arquivo)
                caminho_novo = os.path.join(DIR, novo_nome)
                
                # Renomear
                os.rename(caminho_antigo, caminho_novo)
                print(f"  [OK] {arquivo} -> {novo_nome}")
    
    # Listar arquivos CSV resultantes
    csvs = [f for f in os.listdir(DIR) if f.startswith('Empresas') and f.endswith('.csv')]
    csvs.sort()
    
    print(f"\n[CONCLUIDO] {len(csvs)} arquivo(s) CSV prontos:")
    for csv in csvs:
        tamanho_mb = os.path.getsize(os.path.join(DIR, csv)) / (1024*1024)
        print(f"  - {csv} ({tamanho_mb:.1f} MB)")

if __name__ == "__main__":
    renomear_arquivos()
