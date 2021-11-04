-- Script for creating the database for the project -- 
PRAGMA foreign_keys=OFF;
DROP TABLE IF EXISTS pallets;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS suborders;
DROP TABLE IF EXISTS recipes;
DROP TABLE IF EXISTS recipe_items;
DROP TABLE IF EXISTS inventory;


PRAGMA foreign_keys=ON;

CREATE TABLE pallets (
      pallet_id         TEXT DEFAULT (lower(hex(randomblob(16)))), 
      order_id          TEXT, 
      cookie_type       TEXT, 
      production_time   DATE NOT NULL, 
      blocked           INT DEFAULT 0, 
      delivered_date    DATE, 
      PRIMARY KEY (pallet_id), 
      FOREIGN KEY (cookie_type) REFERENCES recipies(cookie_type),
      FOREIGN KEY (delivered_date) REFERENCES orders(delivered_date)
);

CREATE TABLE orders ( 
      order_id          TEXT DEFAULT (lower(hex(randomblob(16)))), 
      order_date        DATE, 
      delivered_date    DATE, 
      customer_id       TEXT, 
      PRIMARY KEY (order_id), 
      FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE customers ( 
      customer_id       TEXT DEFAULT (lower(hex(randomblob(16)))), 
      customer_name     TEXT, 
      customer_address  TEXT, 
      PRIMARY KEY (customer_id)
);      

CREATE TABLE suborders ( 
      order_id      TEXT, 
      cookie_type   TEXT, 
      quantity      INTEGER, 
      PRIMARY KEY (order_id, cookie_type),
      FOREIGN KEY (order_id) REFERENCES orders(order_id), 
      FOREIGN KEY (cookie_type) REFERENCES recipies(cookie_type)
);

CREATE TABLE recipes (
      cookie_type TEXT NOT NULL,
      PRIMARY KEY (cookie_type)
);

CREATE TABLE recipe_items (
      cookie_type   TEXT, 
      ingredient    TEXT, 
      amount        REAL,
      PRIMARY KEY (cookie_type, ingredient),
      FOREIGN KEY (cookie_type) REFERENCES recipies(cookie_type),
      FOREIGN KEY (ingredient) REFERENCES inventory(ingredient)
);


CREATE TABLE inventory (
      inventory_update_key TEXT DEFAULT (lower(hex(randomblob(16)))), 
      ingredient    TEXT NOT NULL, 
      amount        REAL DEFAULT 0,
      unit          TEXT,
      date          DATETIME,
      PRIMARY KEY (inventory_update_key)
);

DROP TRIGGER IF EXISTS ckeck_inventory;
CREATE TRIGGER check_inventory
AFTER INSERT ON inventory
WHEN 
      (SELECT sum(amount) AS stock
      FROM inventory 
      WHERE ingredient = NEW.ingredient)
      < 0
BEGIN 
      SELECT RAISE (ROllBACK, "Not enough ingredients in inventory");
END;

-- Trying to fix triggers
-- DROP TRIGGER IF EXISTS check_inventory;
-- CREATE TRIGGER check_inventory
-- AFTER INSERT ON inventory
-- WHEN
--       SELECT sum(amount) AS stock
--       FROM inventory
--       WHERE ingredient = NEW.ingredient
-- BEGIN
--       SELECT RAISE (ROLLBACK, "Not enough ingredients in inventory");
-- END;

-- DROP TRIGGER IF EXISTS update_inventory;
-- CREATE TRIGGER update_inventory
-- AFTER INSERT ON pallets
-- INSERT INTO inventory(ingredient,amount)
-- FOR EACH ROW
-- VALUES 
--       (SELECT ingredient
--       FROM recipe_items
--       WHERE cookie_type = NEW.cookie_type, 
--       SELECT -15*10*36*amount
--       FROM recipe_items
--       WHERE cookie_type = NEW.cookie_type);
-- END;
