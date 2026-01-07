-- Criação de tabelas para moedas e taxas de câmbio diárias
-- Execute este script uma vez no banco de dados supply_chain_system

USE supply_chain_system;

CREATE TABLE IF NOT EXISTS currencies (
    code VARCHAR(3) NOT NULL PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    symbol VARCHAR(8) NULL,
    decimal_places TINYINT(1) NOT NULL DEFAULT 2,
    active TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS exchange_rates (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    rate_date DATE NOT NULL,
    base_currency_code VARCHAR(3) NOT NULL,
    target_currency_code VARCHAR(3) NOT NULL,
    rate DECIMAL(18,8) NOT NULL,
    source VARCHAR(64) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_exchange_rates_date_pair (rate_date, base_currency_code, target_currency_code),
    CONSTRAINT fk_exchange_rates_base_currency FOREIGN KEY (base_currency_code) REFERENCES currencies(code),
    CONSTRAINT fk_exchange_rates_target_currency FOREIGN KEY (target_currency_code) REFERENCES currencies(code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT IGNORE INTO currencies (code, name, symbol, decimal_places, active)
VALUES 
    ('BRL', 'Real Brasileiro', 'R$', 2, 1),
    ('PYG', 'Guarani Paraguaio', '₲', 0, 1),
    ('ARS', 'Peso Argentino', '$', 2, 1),
    ('USD', 'Dólar Americano', 'US$', 2, 1),
    ('CNY', 'Yuan Renminbi', '¥', 2, 1);
