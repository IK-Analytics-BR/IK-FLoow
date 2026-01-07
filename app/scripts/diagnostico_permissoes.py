"""
Script para diagnosticar problemas de permissoes
"""
import pymysql

conn = pymysql.connect(
    host='localhost', 
    user='root', 
    password='aritana', 
    database='supply_chain_system',
    cursorclass=pymysql.cursors.DictCursor
)
cur = conn.cursor()

# 1. Buscar usuarios operador
print("=" * 60)
print("1. USUARIOS COM 'operador' NO NOME:")
print("=" * 60)
cur.execute("SELECT id, username, name, role, eh_operador, eh_vendedor, eh_lider_equipe FROM users WHERE username LIKE '%operador%' OR name LIKE '%operador%'")
users = cur.fetchall()
for u in users:
    print(f"  ID: {u['id']}, User: {u['username']}, Role: {u['role']}, Operador: {u['eh_operador']}, Vendedor: {u['eh_vendedor']}, Lider: {u['eh_lider_equipe']}")

# 2. Para cada usuario, verificar permissoes
for user in users:
    print(f"\n{'=' * 60}")
    print(f"2. PERMISSOES DO USUARIO: {user['username']} (ID: {user['id']})")
    print("=" * 60)
    
    cur.execute("""
        SELECT st.codigo, st.modulo, up.pode_visualizar, up.pode_criar, up.pode_editar, up.pode_excluir
        FROM usuario_permissoes up
        JOIN sistema_telas st ON st.id = up.tela_id
        WHERE up.usuario_id = %s
        ORDER BY st.modulo, st.codigo
    """, (user['id'],))
    perms = cur.fetchall()
    
    if not perms:
        print("  NENHUMA PERMISSAO CADASTRADA!")
    else:
        print(f"  Total: {len(perms)} telas permitidas")
        modulo_atual = ""
        for p in perms:
            if p['modulo'] != modulo_atual:
                print(f"\n  [{p['modulo']}]")
                modulo_atual = p['modulo']
            v = 'V' if p['pode_visualizar'] else '-'
            c = 'C' if p['pode_criar'] else '-'
            e = 'E' if p['pode_editar'] else '-'
            x = 'X' if p['pode_excluir'] else '-'
            print(f"    {p['codigo']}: [{v}{c}{e}{x}]")

# 3. Simular carregamento de permissoes
print(f"\n{'=' * 60}")
print("3. SIMULANDO CARREGAMENTO DE PERMISSOES:")
print("=" * 60)

for user in users:
    cur.execute("""
        SELECT 
            st.codigo,
            st.rota_flask,
            st.url_padrao,
            up.pode_visualizar,
            up.pode_criar,
            up.pode_editar,
            up.pode_excluir
        FROM usuario_permissoes up
        JOIN sistema_telas st ON st.id = up.tela_id
        WHERE up.usuario_id = %s AND st.ativo = 1
    """, (user['id'],))
    
    permissoes = cur.fetchall()
    resultado = {}
    for p in permissoes:
        resultado[p['codigo']] = {
            'visualizar': bool(p['pode_visualizar']),
            'criar': bool(p['pode_criar']),
            'editar': bool(p['pode_editar']),
            'excluir': bool(p['pode_excluir']),
        }
    
    print(f"\n  Usuario: {user['username']}")
    print(f"  Permissoes carregadas: {len(resultado)} telas")
    
    # Verificar telas importantes
    telas_menu = ['dashboard', 'vendas.pdv', 'clientes.lista', 'produtos.lista', 'admin.permissoes']
    for tela in telas_menu:
        if tela in resultado:
            print(f"    {tela}: {resultado[tela]}")
        else:
            print(f"    {tela}: NAO PERMITIDO")

conn.close()
print("\n[DIAGNOSTICO CONCLUIDO]")
