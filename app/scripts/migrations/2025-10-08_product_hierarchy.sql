-- Migration: Produto Pai/Filho e Vínculo com Cliente
-- Date: 2025-10-08

START TRANSACTION;

-- 1) Coluna product_type em products
ALTER TABLE products
  ADD COLUMN product_type ENUM('standalone','parent','child') NOT NULL DEFAULT 'standalone' AFTER category;

-- 2) Tabela product_children (BOM do produto pai)
-- OBS: ajuste INT/UNSIGNED conforme o tipo de products.id no seu schema
CREATE TABLE IF NOT EXISTS product_children (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  parent_product_id INT NOT NULL,
  child_product_id INT NOT NULL,
  quantity DECIMAL(10,2) NOT NULL DEFAULT 1,
  interval_days INT NULL,
  notes VARCHAR(255) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_parent_child (parent_product_id, child_product_id),
  KEY idx_pc_parent (parent_product_id),
  KEY idx_pc_child (child_product_id),
  CONSTRAINT fk_pc_parent FOREIGN KEY (parent_product_id) REFERENCES products(id) ON DELETE CASCADE,
  CONSTRAINT fk_pc_child FOREIGN KEY (child_product_id) REFERENCES products(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3) Tabela customer_products (vínculo cliente → produto pai)
-- OBS: ajuste INT/UNSIGNED conforme o tipo de customers.id e products.id
CREATE TABLE IF NOT EXISTS customer_products (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  customer_id INT NOT NULL,
  product_id INT NOT NULL,
  serial_number VARCHAR(100) NULL,
  installed_at DATE NULL,
  active TINYINT(1) NOT NULL DEFAULT 1,
  notes VARCHAR(255) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  KEY idx_cp_customer (customer_id),
  KEY idx_cp_product (product_id),
  CONSTRAINT fk_cp_customer FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
  CONSTRAINT fk_cp_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4) Tabela customer_product_children_status (status de insumos por cliente/produto pai)
-- OBS: ajuste INT/UNSIGNED conforme o tipo de customer_products.id e products.id
CREATE TABLE IF NOT EXISTS customer_product_children_status (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  customer_product_id BIGINT NOT NULL,
  child_product_id INT NOT NULL,
  last_replacement_at DATE NULL,
  interval_days INT NULL,
  next_due_at DATE NULL,
  notes VARCHAR(255) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_cpcs (customer_product_id, child_product_id),
  KEY idx_cpcs_cp (customer_product_id),
  KEY idx_cpcs_child (child_product_id),
  CONSTRAINT fk_cpcs_cp FOREIGN KEY (customer_product_id) REFERENCES customer_products(id) ON DELETE CASCADE,
  CONSTRAINT fk_cpcs_child FOREIGN KEY (child_product_id) REFERENCES products(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

COMMIT;
