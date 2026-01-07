"""
Script para diagnosticar XMLs e ver o que está dentro
"""
import sys
import os
import xml.etree.ElementTree as ET

# Adicionar path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'app'))

from utils.xml_classifier import classificar_xml


def diagnosticar_pasta(pasta_xml, max_arquivos=10):
    """
    Diagnostica os primeiros N XMLs de uma pasta
    """
    print("=" * 100)
    print(f"DIAGNOSTICANDO XMLs em: {pasta_xml}")
    print("=" * 100)
    print()
    
    xml_files = []
    for root, dirs, files in os.walk(pasta_xml):
        for file in files:
            if file.lower().endswith('.xml'):
                xml_files.append(os.path.join(root, file))
                if len(xml_files) >= max_arquivos:
                    break
        if len(xml_files) >= max_arquivos:
            break
    
    print(f"[INFO] Encontrados {len(xml_files)} XMLs para analise")
    print()
    
    stats = {
        'autorizada': 0,
        'cancelada': 0,
        'evento': 0,
        'sem_protocolo': 0,
        'erro': 0
    }
    
    for i, xml_file in enumerate(xml_files, 1):
        print(f"\n{'='*100}")
        print(f"[{i}/{len(xml_files)}] {os.path.basename(xml_file)}")
        print(f"{'='*100}")
        
        try:
            # Classificar
            info = classificar_xml(xml_file)
            tipo = info['tipo']
            status = info.get('status')
            chave = info.get('chave')
            
            print(f"  [TIPO] {tipo}")
            if status:
                print(f"  [STATUS] {status}")
            if chave:
                print(f"  [CHAVE] {chave[:10]}...{chave[-10:]}")
            
            # Analisar estrutura do XML
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Procurar cStat
            print(f"\n  [BUSCA] Codigo de status (cStat)...")
            
            cstats_encontrados = []
            for elem in root.iter():
                if 'cStat' in elem.tag:
                    cstats_encontrados.append({
                        'tag': elem.tag,
                        'valor': elem.text,
                        'pai': elem.getparent().tag if hasattr(elem, 'getparent') else 'N/A'
                    })
            
            if cstats_encontrados:
                print(f"  [OK] Encontrados {len(cstats_encontrados)} codigo(s) de status:")
                for cstat in cstats_encontrados:
                    print(f"     - {cstat['valor']} em <{cstat['tag']}>")
            else:
                print(f"  [AVISO] NENHUM codigo de status encontrado!")
                stats['sem_protocolo'] += 1
            
            # Procurar protNFe
            prot_nfe = None
            for elem in root.iter():
                if 'protNFe' in elem.tag or 'infProt' in elem.tag:
                    prot_nfe = elem
                    break
            
            if prot_nfe is not None:
                print(f"  [OK] Protocolo encontrado!")
            else:
                print(f"  [AVISO] Protocolo NAO encontrado")
            
            # Procurar evento de cancelamento
            evento_canc = None
            for elem in root.iter():
                if 'procEventoNFe' in elem.tag:
                    # Ver se é cancelamento
                    for child in elem.iter():
                        if 'tpEvento' in child.tag and child.text == '110111':
                            evento_canc = True
                            break
                    if evento_canc:
                        break
            
            if evento_canc:
                print(f"  [EVENTO] Cancelamento encontrado no XML!")
            
            # Atualizar estatísticas
            if tipo == 'nfe':
                if status == 'cancelada':
                    stats['cancelada'] += 1
                else:
                    stats['autorizada'] += 1
            else:
                stats['evento'] += 1
                
        except Exception as e:
            print(f"  [ERRO] {str(e)}")
            stats['erro'] += 1
    
    # Resumo
    print("\n\n" + "=" * 100)
    print("RESUMO DO DIAGNOSTICO")
    print("=" * 100)
    print(f"  [OK] NF-e Autorizadas: {stats['autorizada']}")
    print(f"  [CANCELADA] NF-e Canceladas: {stats['cancelada']}")
    print(f"  [EVENTO] Eventos: {stats['evento']}")
    print(f"  [AVISO] Sem protocolo: {stats['sem_protocolo']}")
    print(f"  [ERRO] Erros: {stats['erro']}")
    print()
    
    if stats['sem_protocolo'] > 0:
        print("[ATENCAO] Alguns XMLs nao tem protocolo!")
        print("   Isso pode significar que sao XMLs da NF-e SEM o retorno da SEFAZ")
        print("   Esses XMLs nao tem como determinar se foram cancelados ou nao")
    
    if stats['cancelada'] == 0 and stats['autorizada'] > 0:
        print("\n[INFO] NENHUMA NF-e cancelada encontrada!")
        print("   Possibilidades:")
        print("   1. Seus XMLs nao tem NF-e canceladas")
        print("   2. Os XMLs nao contem o protocolo de cancelamento")
        print("   3. O cancelamento esta em arquivo separado (evento)")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python diagnosticar_xmls.py <pasta_xml> [quantidade]")
        print()
        print("Exemplo:")
        print("  python app\\scripts\\diagnosticar_xmls.py C:\\XMLs 20")
        sys.exit(1)
    
    pasta = sys.argv[1]
    max_arq = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    diagnosticar_pasta(pasta, max_arq)
