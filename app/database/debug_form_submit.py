import requests
import json

def simulate_product_form_submission():
    """
    Simula o envio do formulário de cadastro de produtos para identificar o erro.
    """
    # URL do formulário de cadastro
    url = "http://localhost:8080/produtos/cadastrar"
    
    # Dados do formulário (simulando os campos do formulário HTML)
    form_data = {
        # Dados Básicos
        "name": "Produto Teste Simulado",
        "description": "Descrição do produto teste simulado",
        "internal_code": "TEST002",
        "barcode": "7891234567891",
        "unit_measure": "UN",
        "category_id": "",  # Vazio para testar se é obrigatório
        "brand_id": "",
        "group_id": "",
        "subgroup_id": "",
        
        # Dados Fiscais
        "ncm": "12345678",
        "cest": "1234567",
        "cfop_in": "1102",
        "cfop_out": "5102",
        "cst_csosn": "000",
        "origin": "0",
        "icms_rate": "18",
        "pis_rate": "1.65",
        "cofins_rate": "7.6",
        "ipi_rate": "5",
        "tax_benefits": "",
        
        # Dados de Compras
        "main_supplier_id": "",
        "supplier_code": "FORN001",
        "last_purchase_price": "50",
        "avg_delivery_time": "5",
        
        # Dados de Preço (movidos para Identificação Básica)
        "cost_price": "50",
        "margin": "100",
        "price": "100",
        "max_discount": "10",
        
        # Estoque e Logística
        "stock_quantity": "10",
        "min_stock": "5",
        "max_stock": "20",
        "location": "Prateleira A1",
        "lot_number": "LOT001",
        "expiry_date": "2025-12-31",
        "net_weight": "1.5",
        "gross_weight": "1.8",
        "length_cm": "10",
        "width_cm": "5",
        "height_cm": "2",
        "volume_m3": "0.0001",
        
        # Integrações e Outras Informações
        "active": "on",  # Checkbox marcado
        "lot_control": "on",
        "serial_control": "",  # Checkbox desmarcado
        "imported": "",
        "notes": "Observações de teste"
    }
    
    # Enviar o formulário
    try:
        # Primeiro, obter um cookie de sessão
        session = requests.Session()
        login_url = "http://localhost:8080/login"
        login_data = {
            "username": "admin",
            "password": "admin"
        }
        login_response = session.post(login_url, data=login_data)
        
        if login_response.status_code == 200:
            print("Login falhou. Verifique as credenciais.")
            return
        
        # Agora enviar o formulário de cadastro de produtos
        response = session.post(url, data=form_data)
        
        # Verificar a resposta
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            # Se retornou 200, provavelmente houve um erro no formulário
            print("Formulário retornou com erro (status 200). Verificando o conteúdo...")
            
            # Procurar por mensagens de erro no HTML
            if "Erro ao cadastrar produto" in response.text:
                print("Encontrada mensagem de erro no formulário.")
                
                # Tentar extrair a mensagem de erro específica
                import re
                error_match = re.search(r'Erro ao cadastrar produto: (.*?)</div>', response.text)
                if error_match:
                    error_message = error_match.group(1)
                    print(f"Mensagem de erro: {error_message}")
        elif response.status_code == 302:
            # Redirecionamento indica sucesso
            print("Produto cadastrado com sucesso!")
        else:
            print(f"Resposta inesperada: {response.status_code}")
    
    except Exception as e:
        print(f"Erro ao enviar o formulário: {str(e)}")

if __name__ == "__main__":
    simulate_product_form_submission()
