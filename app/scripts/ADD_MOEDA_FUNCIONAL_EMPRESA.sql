USE supply_chain_system;

ALTER TABLE empresas
    ADD COLUMN moeda_funcional CHAR(3) NOT NULL DEFAULT 'BRL' COMMENT 'Moeda funcional da empresa (BRL, PYG, USD, etc)';
