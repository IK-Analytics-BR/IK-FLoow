"""
Executa importação de Empresas.csv automaticamente
"""
from importar_empresas_receita import importar_todos_arquivos_empresas

if __name__ == "__main__":
    print("\n🚀 INICIANDO IMPORTAÇÃO AUTOMÁTICA...")
    importar_todos_arquivos_empresas()
    print("\n✅ PROCESSO CONCLUÍDO!")
