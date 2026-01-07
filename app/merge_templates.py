import os

# Definir os arquivos de template a serem combinados
template_files = [
    'produto_form_tabs.html',
    'produto_form_tabs_fiscal.html',
    'produto_form_tabs_compras.html',
    'produto_form_tabs_vendas.html',
    'produto_form_tabs_estoque.html',
    'produto_form_tabs_integracoes.html',
    'produto_form_tabs_footer.html'
]

# Diretório dos templates
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

# Arquivo de saída
output_file = os.path.join(template_dir, 'produto_form.html')

# Ler o conteúdo do primeiro arquivo (cabeçalho)
with open(os.path.join(template_dir, template_files[0]), 'r', encoding='utf-8') as f:
    content = f.read()

# Encontrar onde inserir as outras abas
insert_point = content.find('</div>\n\n')  # Após o fechamento da primeira aba

if insert_point == -1:
    print("Não foi possível encontrar o ponto de inserção!")
    exit(1)

# Inserir as outras abas
for file_name in template_files[1:-1]:  # Excluir o primeiro e o último arquivo
    with open(os.path.join(template_dir, file_name), 'r', encoding='utf-8') as f:
        tab_content = f.read()
        content = content[:insert_point + 7] + tab_content + content[insert_point + 7:]

# Adicionar o rodapé
with open(os.path.join(template_dir, template_files[-1]), 'r', encoding='utf-8') as f:
    footer_content = f.read()
    # Encontrar onde inserir o rodapé
    footer_insert_point = content.rfind('</div>')
    if footer_insert_point != -1:
        content = content[:footer_insert_point + 6] + footer_content

# Salvar o arquivo combinado
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Template combinado salvo em {output_file}")
