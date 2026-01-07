import mysql.connector
import sys
import os

# Adicionar o diretório pai ao caminho de importação
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_db

def test_direct_insert():
    """
    Testa a inserção direta de um produto no banco de dados.
    """
    try:
        db = get_db()
        
        # Dados do produto para teste
        name = "Produto Teste Direto"
        description = "Descrição do produto teste direto"
        internal_code = "TEST003"
        barcode = "7891234567892"
        unit_measure = "UN"
        category_id = None
        brand_id = None
        group_id = None
        subgroup_id = None
        ncm = "12345678"
        cest = "1234567"
        cfop_in = "1102"
        cfop_out = "5102"
        cst_csosn = "000"
        origin = 0
        icms_rate = 18.0
        pis_rate = 1.65
        cofins_rate = 7.6
        ipi_rate = 5.0
        tax_benefits = ""
        main_supplier_id = None
        supplier_code = "FORN001"
        last_purchase_price = 50.0
        avg_delivery_time = 5
        cost_price = 50.0
        margin = 100.0
        price = 100.0
        max_discount = 10.0
        stock_quantity = 10.0
        min_stock = 5.0
        max_stock = 20.0
        location = "Prateleira A1"
        lot_number = "LOT001"
        expiry_date = None
        net_weight = 1.5
        gross_weight = 1.8
        length_cm = 10.0
        width_cm = 5.0
        height_cm = 2.0
        volume_m3 = 0.0001
        active = True
        lot_control = True
        serial_control = False
        imported = False
        notes = "Observações de teste"
        photo_url = ""
        category = "outro"
        
        # Construir a query de inserção
        query = """
            INSERT INTO products (
                name, description, internal_code, barcode, unit_measure, 
                category_id, brand_id, group_id, subgroup_id,
                ncm, cest, cfop_in, cfop_out, cst_csosn, origin, 
                icms_rate, pis_rate, cofins_rate, ipi_rate, tax_benefits,
                main_supplier_id, supplier_code, last_purchase_price, avg_delivery_time,
                cost_price, margin, price, max_discount,
                stock_quantity, min_stock, max_stock, location, lot_number, expiry_date,
                net_weight, gross_weight, length_cm, width_cm, height_cm, volume_m3,
                active, lot_control, serial_control, imported, notes, photo_url, category
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        params = (
            name, description, internal_code, barcode, unit_measure, 
            category_id, brand_id, group_id, subgroup_id,
            ncm, cest, cfop_in, cfop_out, cst_csosn, origin, 
            icms_rate, pis_rate, cofins_rate, ipi_rate, tax_benefits,
            main_supplier_id, supplier_code, last_purchase_price, avg_delivery_time,
            cost_price, margin, price, max_discount,
            stock_quantity, min_stock, max_stock, location, lot_number, expiry_date,
            net_weight, gross_weight, length_cm, width_cm, height_cm, volume_m3,
            active, lot_control, serial_control, imported, notes, photo_url, category
        )
        
        # Tentar inserir o produto
        produto_id = db.insert(query, params)
        
        if produto_id:
            print(f"Produto inserido com sucesso! ID: {produto_id}")
            
            # Verificar se o produto foi inserido
            produto = db.fetch_one("SELECT * FROM products WHERE id = %s", (produto_id,))
            if produto:
                print("Produto encontrado no banco de dados!")
                print(f"Nome: {produto['name']}")
                print(f"Preço: {produto['price']}")
            else:
                print("Produto não encontrado no banco de dados!")
        else:
            print("Falha ao inserir o produto!")
            
    except Exception as e:
        print(f"Erro ao testar inserção direta: {str(e)}")

if __name__ == "__main__":
    test_direct_insert()
