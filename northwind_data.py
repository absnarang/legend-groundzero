"""
Northwind cheat sheet constants — model, seed SQL, and all TDS examples.
Kept in a separate module so tests can import without triggering Streamlit.
"""

ENGINE_URL = "http://localhost:8080"

# ══════════════════════════════════════════════════════════════════════════════
# NORTHWIND CHEAT SHEET — model, seed data, and all TDS examples
# Based on the FINOS Legend Northwind showcase model (illustrative data only)
# ══════════════════════════════════════════════════════════════════════════════

NORTHWIND_MODEL = """\
// ── NLQ Profile ────────────────────────────────────────────────────────────

Profile nlq::NlqProfile
{
    stereotypes: [core, junction, timeseries, calculated, sensitive];
    tags: [description, synonyms, businessDomain, importance, exampleQuestions, sampleValues, unit, whenToUse];
}

// ── Domain classes ─────────────────────────────────────────────────────────

Class {nlq::NlqProfile.description = 'A product category or grouping',
       nlq::NlqProfile.synonyms = 'category, group, type, product category',
       nlq::NlqProfile.businessDomain = 'Product Catalog',
       nlq::NlqProfile.importance = 'medium'} northwind::model::Category
{
    categoryId:   Integer[1];
    categoryName: String[1];
    description:  String[0..1];
}

Class {nlq::NlqProfile.description = 'A product supplier or vendor',
       nlq::NlqProfile.synonyms = 'supplier, vendor, manufacturer',
       nlq::NlqProfile.businessDomain = 'Product Catalog',
       nlq::NlqProfile.importance = 'low'} northwind::model::Supplier
{
    supplierId:  Integer[1];
    companyName: String[1];
    country:     String[0..1];
    city:        String[0..1];
}

Class <<nlq::NlqProfile.core>>
      {nlq::NlqProfile.description = 'A product in the catalog with unit price and stock info',
       nlq::NlqProfile.synonyms = 'product, item, goods, merchandise',
       nlq::NlqProfile.businessDomain = 'Product Catalog',
       nlq::NlqProfile.importance = 'high',
       nlq::NlqProfile.exampleQuestions = 'What is the average unit price per category?|List products sorted by price|Which products are discontinued?'} northwind::model::Product
{
    productId:    Integer[1];
    productName:  String[1];
    unitPrice:    Float[1];
    unitsInStock: Integer[1];
    discontinued: Integer[1];
}

Class <<nlq::NlqProfile.core>>
      {nlq::NlqProfile.description = 'A customer who places orders',
       nlq::NlqProfile.synonyms = 'customer, client, buyer, account',
       nlq::NlqProfile.businessDomain = 'Sales',
       nlq::NlqProfile.importance = 'high',
       nlq::NlqProfile.exampleQuestions = 'How many orders does each customer have?|List customers from Germany'} northwind::model::Customer
{
    customerId:  String[1];
    companyName: String[1];
    contactName: String[0..1];
    city:        String[0..1];
    country:     String[0..1];
}

Class {nlq::NlqProfile.description = 'An employee who processes orders',
       nlq::NlqProfile.synonyms = 'employee, staff, rep, sales rep',
       nlq::NlqProfile.businessDomain = 'Sales',
       nlq::NlqProfile.importance = 'medium'} northwind::model::Employee
{
    employeeId: Integer[1];
    firstName:  String[1];
    lastName:   String[1];
    title:      String[0..1];
    city:       String[0..1];
    country:    String[0..1];
    hireDate:   String[0..1];
}

Class <<nlq::NlqProfile.core>>
      {nlq::NlqProfile.description = 'A customer order header with date and shipping info',
       nlq::NlqProfile.synonyms = 'order, purchase, sale, transaction',
       nlq::NlqProfile.businessDomain = 'Sales',
       nlq::NlqProfile.importance = 'high',
       nlq::NlqProfile.exampleQuestions = 'Show orders from Germany|List orders by freight|How many orders per country?'} northwind::model::Order
{
    orderId:     Integer[1];
    orderDate:   String[0..1];
    freight:     Float[0..1];
    shipCountry: String[0..1];
    shipCity:    String[0..1];
}

Class <<nlq::NlqProfile.core>>
      {nlq::NlqProfile.description = 'A line item within an order — one row per product per order',
       nlq::NlqProfile.synonyms = 'order detail, line item, order line, order item',
       nlq::NlqProfile.businessDomain = 'Sales',
       nlq::NlqProfile.importance = 'high',
       nlq::NlqProfile.whenToUse = 'Use OrderDetail as root class when the question asks about products within orders, order lines, or needs to show per-product detail for orders. Start from OrderDetail and navigate to Order and Product.',
       nlq::NlqProfile.exampleQuestions = 'Show each order with product names from its order details|What are the quantities per order?|List order lines with product info'} northwind::model::OrderDetail
{
    unitPrice: Float[1];
    quantity:  Integer[1];
    discount:  Float[1];
}

// ── Associations ────────────────────────────────────────────────────────────

Association northwind::assoc::Product_Category
{
    category: northwind::model::Category[1];
    products: northwind::model::Product[*];
}

Association northwind::assoc::Product_Supplier
{
    supplier: northwind::model::Supplier[0..1];
    products: northwind::model::Product[*];
}

Association northwind::assoc::Order_Customer
{
    customer: northwind::model::Customer[1];
    orders:   northwind::model::Order[*];
}

Association northwind::assoc::Order_Employee
{
    employee: northwind::model::Employee[0..1];
    orders:   northwind::model::Order[*];
}

Association northwind::assoc::Order_OrderDetail
{
    orderDetails: northwind::model::OrderDetail[*];
    order:        northwind::model::Order[1];
}

Association northwind::assoc::OrderDetail_Product
{
    product:      northwind::model::Product[1];
    orderDetails: northwind::model::OrderDetail[*];
}

// ── Database ────────────────────────────────────────────────────────────────

Database northwind::store::NorthwindDB
(
    Table T_CATEGORIES
    (
        CATEGORY_ID   INTEGER PRIMARY KEY,
        CATEGORY_NAME VARCHAR(100),
        DESCRIPTION   VARCHAR(500)
    )
    Table T_SUPPLIERS
    (
        SUPPLIER_ID  INTEGER PRIMARY KEY,
        COMPANY_NAME VARCHAR(200),
        COUNTRY      VARCHAR(100),
        CITY         VARCHAR(100)
    )
    Table T_PRODUCTS
    (
        PRODUCT_ID     INTEGER PRIMARY KEY,
        PRODUCT_NAME   VARCHAR(200),
        CATEGORY_ID    INTEGER,
        SUPPLIER_ID    INTEGER,
        UNIT_PRICE     DOUBLE,
        UNITS_IN_STOCK INTEGER,
        DISCONTINUED   INTEGER
    )
    Table T_CUSTOMERS
    (
        CUSTOMER_ID  VARCHAR(10) PRIMARY KEY,
        COMPANY_NAME VARCHAR(200),
        CONTACT_NAME VARCHAR(100),
        CITY         VARCHAR(100),
        COUNTRY      VARCHAR(100)
    )
    Table T_EMPLOYEES
    (
        EMPLOYEE_ID INTEGER PRIMARY KEY,
        FIRST_NAME  VARCHAR(100),
        LAST_NAME   VARCHAR(100),
        TITLE       VARCHAR(100),
        CITY        VARCHAR(100),
        COUNTRY     VARCHAR(100),
        HIRE_DATE   VARCHAR(20)
    )
    Table T_ORDERS
    (
        ORDER_ID    INTEGER PRIMARY KEY,
        CUSTOMER_ID VARCHAR(10),
        EMPLOYEE_ID INTEGER,
        ORDER_DATE  VARCHAR(20),
        FREIGHT     DOUBLE,
        SHIP_COUNTRY VARCHAR(100),
        SHIP_CITY   VARCHAR(100)
    )
    Table T_ORDER_DETAILS
    (
        ORDER_ID   INTEGER,
        PRODUCT_ID INTEGER,
        UNIT_PRICE DOUBLE,
        QUANTITY   INTEGER,
        DISCOUNT   DOUBLE
    )
    Join Product_Category(T_PRODUCTS.CATEGORY_ID = T_CATEGORIES.CATEGORY_ID)
    Join Product_Supplier(T_PRODUCTS.SUPPLIER_ID = T_SUPPLIERS.SUPPLIER_ID)
    Join Order_Customer(T_ORDERS.CUSTOMER_ID = T_CUSTOMERS.CUSTOMER_ID)
    Join Order_Employee(T_ORDERS.EMPLOYEE_ID = T_EMPLOYEES.EMPLOYEE_ID)
    Join Order_OrderDetail(T_ORDER_DETAILS.ORDER_ID = T_ORDERS.ORDER_ID)
    Join OrderDetail_Product(T_ORDER_DETAILS.PRODUCT_ID = T_PRODUCTS.PRODUCT_ID)
)

// ── Mapping ─────────────────────────────────────────────────────────────────

Mapping northwind::mapping::NorthwindMapping
(
    northwind::model::Category: Relational
    {
        ~mainTable [NorthwindDB] T_CATEGORIES
        categoryId:   [NorthwindDB] T_CATEGORIES.CATEGORY_ID,
        categoryName: [NorthwindDB] T_CATEGORIES.CATEGORY_NAME,
        description:  [NorthwindDB] T_CATEGORIES.DESCRIPTION
    }
    northwind::model::Supplier: Relational
    {
        ~mainTable [NorthwindDB] T_SUPPLIERS
        supplierId:  [NorthwindDB] T_SUPPLIERS.SUPPLIER_ID,
        companyName: [NorthwindDB] T_SUPPLIERS.COMPANY_NAME,
        country:     [NorthwindDB] T_SUPPLIERS.COUNTRY,
        city:        [NorthwindDB] T_SUPPLIERS.CITY
    }
    northwind::model::Product: Relational
    {
        ~mainTable [NorthwindDB] T_PRODUCTS
        productId:    [NorthwindDB] T_PRODUCTS.PRODUCT_ID,
        productName:  [NorthwindDB] T_PRODUCTS.PRODUCT_NAME,
        unitPrice:    [NorthwindDB] T_PRODUCTS.UNIT_PRICE,
        unitsInStock: [NorthwindDB] T_PRODUCTS.UNITS_IN_STOCK,
        discontinued: [NorthwindDB] T_PRODUCTS.DISCONTINUED
    }
    northwind::model::Customer: Relational
    {
        ~mainTable [NorthwindDB] T_CUSTOMERS
        customerId:  [NorthwindDB] T_CUSTOMERS.CUSTOMER_ID,
        companyName: [NorthwindDB] T_CUSTOMERS.COMPANY_NAME,
        contactName: [NorthwindDB] T_CUSTOMERS.CONTACT_NAME,
        city:        [NorthwindDB] T_CUSTOMERS.CITY,
        country:     [NorthwindDB] T_CUSTOMERS.COUNTRY
    }
    northwind::model::Employee: Relational
    {
        ~mainTable [NorthwindDB] T_EMPLOYEES
        employeeId: [NorthwindDB] T_EMPLOYEES.EMPLOYEE_ID,
        firstName:  [NorthwindDB] T_EMPLOYEES.FIRST_NAME,
        lastName:   [NorthwindDB] T_EMPLOYEES.LAST_NAME,
        title:      [NorthwindDB] T_EMPLOYEES.TITLE,
        city:       [NorthwindDB] T_EMPLOYEES.CITY,
        country:    [NorthwindDB] T_EMPLOYEES.COUNTRY,
        hireDate:   [NorthwindDB] T_EMPLOYEES.HIRE_DATE
    }
    northwind::model::Order: Relational
    {
        ~mainTable [NorthwindDB] T_ORDERS
        orderId:     [NorthwindDB] T_ORDERS.ORDER_ID,
        orderDate:   [NorthwindDB] T_ORDERS.ORDER_DATE,
        freight:     [NorthwindDB] T_ORDERS.FREIGHT,
        shipCountry: [NorthwindDB] T_ORDERS.SHIP_COUNTRY,
        shipCity:    [NorthwindDB] T_ORDERS.SHIP_CITY
    }
    northwind::model::OrderDetail: Relational
    {
        ~mainTable [NorthwindDB] T_ORDER_DETAILS
        unitPrice: [NorthwindDB] T_ORDER_DETAILS.UNIT_PRICE,
        quantity:  [NorthwindDB] T_ORDER_DETAILS.QUANTITY,
        discount:  [NorthwindDB] T_ORDER_DETAILS.DISCOUNT
    }
)

RelationalDatabaseConnection northwind::store::NorthwindConn
{
    type: DuckDB;
    specification: InMemory { };
    auth: NoAuth { };
}

Runtime northwind::runtime::NorthwindRuntime
{
    mappings:
    [
        northwind::mapping::NorthwindMapping
    ];
    connections:
    [
        northwind::store::NorthwindDB:
        [
            environment: northwind::store::NorthwindConn
        ]
    ];
}"""

NORTHWIND_SEED_SQL = """\
CREATE TABLE IF NOT EXISTS T_CATEGORIES (
    CATEGORY_ID   INTEGER PRIMARY KEY,
    CATEGORY_NAME VARCHAR(100),
    DESCRIPTION   VARCHAR(500)
);
CREATE TABLE IF NOT EXISTS T_SUPPLIERS (
    SUPPLIER_ID  INTEGER PRIMARY KEY,
    COMPANY_NAME VARCHAR(200),
    COUNTRY      VARCHAR(100),
    CITY         VARCHAR(100)
);
CREATE TABLE IF NOT EXISTS T_PRODUCTS (
    PRODUCT_ID     INTEGER PRIMARY KEY,
    PRODUCT_NAME   VARCHAR(200),
    CATEGORY_ID    INTEGER,
    SUPPLIER_ID    INTEGER,
    UNIT_PRICE     DOUBLE,
    UNITS_IN_STOCK INTEGER,
    DISCONTINUED   INTEGER
);
CREATE TABLE IF NOT EXISTS T_CUSTOMERS (
    CUSTOMER_ID  VARCHAR(10) PRIMARY KEY,
    COMPANY_NAME VARCHAR(200),
    CONTACT_NAME VARCHAR(100),
    CITY         VARCHAR(100),
    COUNTRY      VARCHAR(100)
);
CREATE TABLE IF NOT EXISTS T_EMPLOYEES (
    EMPLOYEE_ID INTEGER PRIMARY KEY,
    FIRST_NAME  VARCHAR(100),
    LAST_NAME   VARCHAR(100),
    TITLE       VARCHAR(100),
    CITY        VARCHAR(100),
    COUNTRY     VARCHAR(100),
    HIRE_DATE   VARCHAR(20)
);
CREATE TABLE IF NOT EXISTS T_ORDERS (
    ORDER_ID     INTEGER PRIMARY KEY,
    CUSTOMER_ID  VARCHAR(10),
    EMPLOYEE_ID  INTEGER,
    ORDER_DATE   VARCHAR(20),
    FREIGHT      DOUBLE,
    SHIP_COUNTRY VARCHAR(100),
    SHIP_CITY    VARCHAR(100)
);
CREATE TABLE IF NOT EXISTS T_ORDER_DETAILS (
    ORDER_ID   INTEGER,
    PRODUCT_ID INTEGER,
    UNIT_PRICE DOUBLE,
    QUANTITY   INTEGER,
    DISCOUNT   DOUBLE
);

DELETE FROM T_ORDER_DETAILS;
DELETE FROM T_ORDERS;
DELETE FROM T_CUSTOMERS;
DELETE FROM T_EMPLOYEES;
DELETE FROM T_PRODUCTS;
DELETE FROM T_SUPPLIERS;
DELETE FROM T_CATEGORIES;

INSERT INTO T_CATEGORIES VALUES
    (1, 'Beverages',    'Soft drinks, coffees, teas, beers, and ales'),
    (2, 'Condiments',   'Sweet and savory sauces, relishes, spreads, and seasonings'),
    (3, 'Seafood',      'Seaweed and fish'),
    (4, 'Dairy',        'Cheeses'),
    (5, 'Grains',       'Breads, crackers, pasta, and cereal'),
    (6, 'Meat',         'Prepared meats and poultry'),
    (7, 'Produce',      'Dried fruit and bean curd'),
    (8, 'Confections',  'Desserts, candies, and sweet breads');

INSERT INTO T_SUPPLIERS VALUES
    (1, 'Exotic Liquids',          'UK',   'London'),
    (2, 'New Orleans Cajun Delights', 'USA', 'New Orleans'),
    (3, 'Grandma Kelly''s Homestead', 'USA', 'Ann Arbor'),
    (4, 'Tokyo Traders',           'Japan', 'Tokyo'),
    (5, 'Cooperativa de Quesos',   'Spain', 'Oviedo');

INSERT INTO T_PRODUCTS VALUES
    (1,  'Chai',                  1, 1, 18.0,  39, 0),
    (2,  'Chang',                 1, 1, 19.0,  17, 0),
    (3,  'Aniseed Syrup',         2, 1, 10.0,  13, 0),
    (4,  'Chef Anton''s Cajun',   2, 2, 22.0,  53, 0),
    (5,  'Grandma''s Boysenberry',2, 3, 25.0,  0,  1),
    (6,  'Uncle Bob''s Organic',  7, 3, 30.0,  15, 0),
    (7,  'Northwoods Cranberry',  2, 3, 40.0,  6,  0),
    (8,  'Mishi Kobe Niku',       6, 4, 97.0,  29, 1),
    (9,  'Ikura',                 8, 4, 31.0,  31, 0),
    (10, 'Queso Cabrales',        4, 5, 21.0,  22, 0),
    (11, 'Queso Manchego',        4, 5, 38.0,  86, 0),
    (12, 'Konbu',                 8, 4,  6.0,  24, 0),
    (13, 'Tofu',                  7, 4, 23.25, 35, 0),
    (14, 'Genen Shouyu',          2, 4, 15.5,  39, 0),
    (15, 'Pavlova',               3, 2, 17.45, 29, 0);

INSERT INTO T_CUSTOMERS VALUES
    ('ALFKI', 'Alfreds Futterkiste',     'Maria Anders',    'Berlin',     'Germany'),
    ('ANATR', 'Ana Trujillo Emparedados','Ana Trujillo',    'Mexico City','Mexico'),
    ('ANTON', 'Antonio Moreno Taqueria', 'Antonio Moreno',  'Mexico City','Mexico'),
    ('AROUT', 'Around the Horn',         'Thomas Hardy',    'London',     'UK'),
    ('BERGS', 'Berglunds snabbkop',      'Christina Berglund','Lulea',    'Sweden'),
    ('BOLID', 'Bolido Comidas',          'Martin Sommer',   'Madrid',     'Spain'),
    ('BONAP', 'Bon app',                 'Laurence Lebihan','Marseille',  'France'),
    ('BOTTM', 'Bottom-Dollar Markets',   'Elizabeth Lincoln','Tsawwassen','Canada'),
    ('BSBEV', 'B''s Beverages',          'Victoria Ashworth','London',    'UK'),
    ('CACTU', 'Cactus Comidas',          'Patricio Simpson','Buenos Aires','Argentina');

INSERT INTO T_EMPLOYEES VALUES
    (1, 'Nancy',   'Davolio',  'Sales Representative', 'Seattle',  'USA', '1992-05-01'),
    (2, 'Andrew',  'Fuller',   'Vice President Sales',  'Tacoma',   'USA', '1992-08-14'),
    (3, 'Janet',   'Leverling','Sales Representative', 'Kirkland', 'USA', '1992-04-01'),
    (4, 'Margaret','Peacock',  'Sales Representative', 'Redmond',  'USA', '1993-05-03'),
    (5, 'Steven',  'Buchanan', 'Sales Manager',        'London',   'UK',  '1993-10-17'),
    (6, 'Michael', 'Suyama',   'Sales Representative', 'London',   'UK',  '1993-10-17'),
    (7, 'Robert',  'King',     'Sales Representative', 'London',   'UK',  '1994-01-02'),
    (8, 'Laura',   'Callahan', 'Inside Sales Coord.',  'Seattle',  'USA', '1994-03-05'),
    (9, 'Anne',    'Dodsworth','Sales Representative', 'London',   'UK',  '1994-11-15');

INSERT INTO T_ORDERS VALUES
    (10248, 'ALFKI', 1, '1996-07-04', 32.38,  'Germany',   'Berlin'),
    (10249, 'ANATR', 2, '1996-07-05', 11.61,  'Mexico',    'Mexico City'),
    (10250, 'ANTON', 3, '1996-07-08', 65.83,  'Mexico',    'Mexico City'),
    (10251, 'AROUT', 4, '1996-07-08', 41.34,  'UK',        'London'),
    (10252, 'BERGS', 5, '1996-07-09', 51.30,  'Sweden',    'Lulea'),
    (10253, 'BOLID', 6, '1996-07-10', 58.17,  'Spain',     'Madrid'),
    (10254, 'BONAP', 7, '1996-07-11', 22.98,  'France',    'Marseille'),
    (10255, 'BOTTM', 8, '1996-07-12', 148.33, 'Canada',    'Tsawwassen'),
    (10256, 'BSBEV', 9, '1996-07-15', 13.97,  'UK',        'London'),
    (10257, 'CACTU', 1, '1996-07-16', 81.91,  'Argentina', 'Buenos Aires'),
    (10258, 'ALFKI', 2, '1996-07-17', 140.51, 'Germany',   'Berlin'),
    (10259, 'ANATR', 3, '1996-07-18', 3.25,   'Mexico',    'Mexico City'),
    (10260, 'ANTON', 4, '1996-07-19', 55.09,  'Mexico',    'Mexico City'),
    (10261, 'AROUT', 5, '1996-07-19', 3.05,   'UK',        'London'),
    (10262, 'BERGS', 6, '1996-07-22', 48.29,  'Sweden',    'Lulea');

INSERT INTO T_ORDER_DETAILS VALUES
    (10248,  1, 18.0, 12, 0.0),
    (10248,  2, 19.0, 10, 0.0),
    (10248,  3, 10.0,  5, 0.0),
    (10249,  4, 22.0,  9, 0.0),
    (10249,  5, 25.0, 40, 0.0),
    (10250,  6, 30.0, 10, 0.0),
    (10250,  7, 40.0, 35, 0.15),
    (10250,  8, 97.0, 15, 0.15),
    (10251,  9, 31.0,  6, 0.05),
    (10251, 10, 21.0, 15, 0.05),
    (10252, 11, 38.0, 40, 0.05),
    (10252, 12,  6.0, 25, 0.05),
    (10253, 13, 23.0, 20, 0.0),
    (10253, 14, 15.5, 42, 0.0),
    (10254, 15, 17.45,15, 0.15),
    (10255,  1, 18.0, 20, 0.0),
    (10255,  2, 19.0, 35, 0.0),
    (10256,  3, 10.0, 15, 0.0),
    (10257,  4, 22.0, 25, 0.0),
    (10258,  5, 25.0, 50, 0.2),
    (10259,  6, 30.0, 10, 0.0),
    (10260,  7, 40.0, 16, 0.25),
    (10261,  8, 97.0, 20, 0.0),
    (10262,  9, 31.0, 12, 0.2);"""

# ── Cheat-sheet examples — every TDS operation ──────────────────────────────
# Each entry: (group, description, pure_query, explanation, uses_db)
# uses_db=True  → requires Northwind seed data (tables must be populated)
# uses_db=False → TDS literal (inline data); no seed needed
# ALL examples use NORTHWIND_MODEL as the runtime container.

CHEAT_SHEET = {
    # ── 1. BASICS ─────────────────────────────────────────────────────────────

    "01 · project — select columns": (
        "Basics",
        "Pick specific properties and give them column aliases.",
        """\
northwind::model::Product.all()
->project(
    [p|$p.productName, p|$p.unitPrice, p|$p.unitsInStock],
    ['product', 'unitPrice', 'stock']
)""",
        "**Signature:** ->project(columnLambdas: List<Lambda>, aliases: List<String>)\n\n"
        "**Arg 1 — columnLambdas:** A list of lambdas, one per output column. Each lambda "
        "receives the root class instance (here `p`) and returns the property to project: "
        "`[p|$p.productName, p|$p.unitPrice]`. You can also navigate associations inline: "
        "`p|$p.category.categoryName`.\n\n"
        "**Arg 2 — aliases:** A parallel list of String column names for the resulting TDS. "
        "Order must match columnLambdas exactly. These aliases become the column names used "
        "in every downstream operation (filter, sort, groupBy).\n\n"
        "**Result:** A TDS (Tabular Data Set) — the fundamental Legend relation type. "
        "All subsequent operations (->filter, ->sort, ->groupBy, ->extend) operate on TDS.",
        True,
    ),

    "02 · filter — WHERE condition": (
        "Basics",
        "Keep only rows matching a boolean predicate.",
        """\
northwind::model::Product.all()
->filter(p | $p.discontinued == 0)
->project(
    [p|$p.productName, p|$p.unitPrice, p|$p.unitsInStock],
    ['product', 'unitPrice', 'stock']
)""",
        "**Signature:** ->filter(predicate: Lambda<Boolean>)\n\n"
        "**Arg 1 — predicate:** A single lambda that returns a Boolean. The variable "
        "(`p` before project, `row` or `r` after project) is bound to each row in turn.\n\n"
        "**Before project:** the lambda parameter is the class instance — use class "
        "properties directly: `p | $p.discontinued == 0`. Association paths also work: "
        "`o | $o.customer.country == 'Germany'`.\n\n"
        "**After project:** the lambda parameter is a TDS row — reference columns by alias: "
        "`{row | $row.unitPrice > 20.0 && $row.stock > 10}`. Use `&&` (AND) and `||` (OR).\n\n"
        "**Operator reference:** `==` `!=` `>` `<` `>=` `<=` for primitives; "
        "`->startsWith()` `->contains()` for strings.",
        True,
    ),

    "03 · sort — ORDER BY": (
        "Basics",
        "Sort results ascending (default) or descending.",
        """\
northwind::model::Product.all()
->project(
    [p|$p.productName, p|$p.unitPrice],
    ['product', 'unitPrice']
)
->sort(~unitPrice->descending())""",
        "**Signature (ascending):** ->sort('columnAlias')\n"
        "**Signature (descending):** ->sort(~columnAlias->descending())\n\n"
        "**Arg — column reference:**\n"
        "• Ascending: pass a String alias: `sort('product')` → SQL ORDER BY ASC.\n"
        "• Descending: use a column selector with `~`: `sort(~unitPrice->descending())` "
        "→ SQL ORDER BY DESC.\n\n"
        "**Chaining:** multiple sort() calls compose left-to-right (last call is the "
        "primary sort key): `->sort(~a->descending())->sort('b')` → ORDER BY b ASC, a DESC.\n\n"
        "**Important:** sort() operates on TDS column aliases, not on class property names. "
        "Always project first, then sort on the alias.",
        True,
    ),

    "04 · take — LIMIT N": (
        "Basics",
        "Return only the first N rows (after sort).",
        """\
northwind::model::Product.all()
->project(
    [p|$p.productName, p|$p.unitPrice],
    ['product', 'unitPrice']
)
->sort(~unitPrice->descending())
->take(5)""",
        "**Signature:** ->take(n: Integer)\n\n"
        "**Arg 1 — n:** The maximum number of rows to return. Maps directly to SQL LIMIT.\n\n"
        "**Legend convention:** Always pair take() with sort() to produce a deterministic "
        "result. Without a sort, the engine may return any N rows depending on storage order.\n\n"
        "**Typical pattern for top-N:** `->sort(~col->descending())->take(N)` — "
        "this is the Legend equivalent of SQL `ORDER BY col DESC LIMIT N`.\n\n"
        "**Distinct from slice():** take(N) is equivalent to slice(0, N). Use take() "
        "when you only need the first N rows from the beginning.",
        True,
    ),

    "05 · filter after project — filter on alias": (
        "Basics",
        "Filter on a computed/aliased column using $row.",
        """\
northwind::model::Product.all()
->project(
    [p|$p.productName, p|$p.unitPrice, p|$p.unitsInStock],
    ['product', 'unitPrice', 'stock']
)
->filter({row | $row.unitPrice > 20.0 && $row.stock > 10})""",
        "**Signature:** ->filter(predicate: Lambda<Boolean>)\n\n"
        "**Post-project lambda form:** After ->project(), the filter lambda receives a "
        "TDS row rather than a class instance. Columns are accessed via dot notation on "
        "the row variable: `$row.unitPrice`, `$row.stock`.\n\n"
        "**Boolean operators:**\n"
        "• `&&` → SQL AND\n"
        "• `||` → SQL OR\n"
        "• `!expr` → SQL NOT\n\n"
        "**Key rule:** Once you have crossed the project() boundary, you can only "
        "reference columns by their TDS alias — not by the original class property name. "
        "Use curly braces `{row | ...}` for the lambda when writing post-project filters.",
        True,
    ),

    "06 · distinct — DISTINCT rows": (
        "Basics",
        "Remove duplicate rows from the result.",
        """\
northwind::model::Order.all()
->project(
    [o|$o.shipCountry],
    ['country']
)
->distinct()
->sort('country')""",
        "**Signature:** ->distinct()\n\n"
        "**Args:** None — distinct() takes no arguments. It deduplicates all columns "
        "of the current TDS together (equivalent to SQL SELECT DISTINCT on all projected columns).\n\n"
        "**Placement:** Apply distinct() after project() and before sort()/take(). "
        "Calling it before project() on a class will deduplicate on all mapped columns, "
        "which is rarely what you want.\n\n"
        "**Legend idiom for unique values:** `->project([x|$x.prop], ['alias'])->distinct()` "
        "is the standard pattern for 'find all distinct values of a property' — "
        "equivalent to SQL `SELECT DISTINCT col FROM table`.",
        True,
    ),

    # ── 2. GROUPBY & AGGREGATION ──────────────────────────────────────────────

    "07 · groupBy — count per group": (
        "GroupBy",
        "Count rows within each group.",
        """\
northwind::model::Order.all()
->project(
    [o|$o.shipCountry, o|$o.orderId],
    ['country', 'orderId']
)
->groupBy(
    [{r|$r.country}],
    [{r|$r.orderId->count()}],
    ['country', 'orderCount']
)
->sort(~orderCount->descending())""",
        "**Signature:** ->groupBy(groupKeys: List<Lambda>, aggregations: List<Lambda>, aliases: List<String>)\n\n"
        "**Arg 1 — groupKeys:** List of lambdas selecting the GROUP BY columns from the TDS row. "
        "Each lambda: `{r|$r.columnAlias}`. Multiple keys: `[{r|$r.country},{r|$r.category}]`.\n\n"
        "**Arg 2 — aggregations:** List of lambdas applying an aggregation function. "
        "Each lambda: `{r|$r.columnAlias->aggFn()}`. "
        "Available aggregators: `->count()` `->sum()` `->avg()` `->min()` `->max()`.\n\n"
        "**Arg 3 — aliases:** Output column names for the result TDS, one per group key "
        "followed by one per aggregation — in the same order.\n\n"
        "**Note:** groupBy() must be called on a TDS (after ->project()), not directly "
        "on a class. The TDS column aliases from project() are what the groupBy lambdas reference.",
        True,
    ),

    "08 · groupBy — sum aggregation": (
        "GroupBy",
        "Sum a numeric column within each group.",
        """\
northwind::model::Order.all()
->project(
    [o|$o.shipCountry, o|$o.freight],
    ['country', 'freight']
)
->groupBy(
    [{r|$r.country}],
    [{r|$r.freight->sum()}],
    ['country', 'totalFreight']
)
->sort(~totalFreight->descending())""",
        "**Signature:** ->groupBy(groupKeys: List<Lambda>, aggregations: List<Lambda>, aliases: List<String>)\n\n"
        "**->sum() aggregator:** Applies to Float or Integer TDS columns. "
        "The lambda form is `{r|$r.colAlias->sum()}` where `colAlias` must resolve to a "
        "numeric column in the projected TDS.\n\n"
        "**Alias alignment:** The third list must have exactly (number of group keys) + "
        "(number of aggregations) entries. Here: 1 key ('country') + 1 agg ('totalFreight') = 2 aliases.\n\n"
        "**SQL equivalent:** `SELECT ship_country, SUM(freight) FROM orders GROUP BY ship_country ORDER BY 2 DESC`.",
        True,
    ),

    "09 · groupBy — avg + count together": (
        "GroupBy",
        "Multiple aggregations in a single groupBy.",
        """\
northwind::model::Product.all()
->project(
    [p|$p.category.categoryName, p|$p.unitPrice, p|$p.productId],
    ['category', 'unitPrice', 'productId']
)
->groupBy(
    [{r|$r.category}],
    [{r|$r.unitPrice->avg()}, {r|$r.productId->count()}],
    ['category', 'avgPrice', 'numProducts']
)
->sort('category')""",
        "**Signature:** ->groupBy(groupKeys: List<Lambda>, aggregations: List<Lambda>, aliases: List<String>)\n\n"
        "**Multiple aggregations:** Add one lambda to the aggregations list per aggregation. "
        "Here: `[{r|$r.unitPrice->avg()}, {r|$r.productId->count()}]` produces two output columns.\n\n"
        "**Alias list length rule:** aliases list length = len(groupKeys) + len(aggregations). "
        "Here: 1 + 2 = 3 aliases: `['category', 'avgPrice', 'numProducts']`.\n\n"
        "**Association navigation in project:** `p|$p.category.categoryName` crosses the "
        "Product→Category association before groupBy, making categoryName available as the "
        "'category' alias for grouping. Always project association paths before groupBy.",
        True,
    ),

    "10 · groupBy — filter on aggregate (HAVING)": (
        "GroupBy",
        "Keep only groups where the aggregate passes a threshold (SQL HAVING).",
        """\
northwind::model::Order.all()
->project(
    [o|$o.shipCountry, o|$o.orderId],
    ['country', 'orderId']
)
->groupBy(
    [{r|$r.country}],
    [{r|$r.orderId->count()}],
    ['country', 'orderCount']
)
->filter({row | $row.orderCount >= 2})
->sort(~orderCount->descending())""",
        "**Signature:** ->groupBy(...) followed by ->filter(predicate: Lambda<Boolean>)\n\n"
        "**HAVING pattern:** Pure has no dedicated HAVING keyword. Instead, chain a "
        "->filter() after ->groupBy(). The filter lambda receives a TDS row and can "
        "reference any output alias from the groupBy — including aggregated columns.\n\n"
        "**Lambda form:** `{row | $row.orderCount >= 2}` — use curly-brace lambda syntax "
        "when filtering on aggregated TDS columns post-groupBy.\n\n"
        "**Engine translation:** The engine detects that the filter references an aggregated "
        "column and emits SQL HAVING or a subquery WHERE as appropriate. "
        "This is semantically equivalent to `HAVING COUNT(order_id) >= 2`.",
        True,
    ),

    # ── 3. ASSOCIATION JOINS ──────────────────────────────────────────────────

    "11 · join — 1-hop association": (
        "Joins",
        "Navigate a 1-hop association — generates a SQL JOIN.",
        """\
northwind::model::Product.all()
->project(
    [p|$p.productName, p|$p.unitPrice, p|$p.category.categoryName],
    ['product', 'unitPrice', 'category']
)
->sort('category')""",
        "**Signature:** No explicit join syntax — navigate via dot notation inside a project lambda.\n\n"
        "**How it works:** `p|$p.category.categoryName` traverses the Association declared "
        "in the model (`Product_Category`). The engine resolves the foreign key from the "
        "Mapping definition and emits a LEFT OUTER JOIN automatically.\n\n"
        "**Association declaration in the model:**\n"
        "```\nAssociation northwind::model::Product_Category {\n"
        "  category: northwind::model::Category[1];\n"
        "  products: northwind::model::Product[*];\n}\n```\n"
        "**Key rule:** Association navigation is always written as `$var.associationName.property` "
        "inside a project or filter lambda. No JOIN keyword, no ON clause — Legend handles it.",
        True,
    ),

    "12 · join — OrderDetail → Product": (
        "Joins",
        "Navigate from OrderDetail to its Product — largest order lines by qty.",
        """\
northwind::model::OrderDetail.all()
->project(
    [d|$d.quantity, d|$d.unitPrice, d|$d.discount,
     d|$d.product.productName],
    ['qty', 'unitPrice', 'discount', 'product']
)
->sort(~qty->descending())
->take(10)""",
        "**Signature:** Navigate via `$d.product.productName` inside the project lambda.\n\n"
        "**Association used:** `OrderDetail_Product` — maps the PRODUCT_ID foreign key "
        "in T_ORDER_DETAILS to T_PRODUCTS. The engine emits a LEFT OUTER JOIN.\n\n"
        "**Mix local and associated columns freely:** In the same project lambda list you "
        "can reference OrderDetail's own mapped columns (`$d.quantity`, `$d.unitPrice`) "
        "alongside the joined Product column (`$d.product.productName`).\n\n"
        "**Multiplicity note:** OrderDetail→Product is many-to-one (`[1]`), so each "
        "detail line maps to exactly one product — the join never fans out the row count.\n\n"
        "**sort + take pattern:** `->sort(~qty->descending())->take(10)` gives the top-10 "
        "order lines by quantity — the Legend equivalent of `ORDER BY qty DESC LIMIT 10`.",
        True,
    ),

    "13 · join — filter through association": (
        "Joins",
        "Filter rows based on a property in a related class.",
        """\
northwind::model::Order.all()
->filter(o | $o.customer.country == 'Germany')
->project(
    [o|$o.orderId, o|$o.orderDate,
     o|$o.customer.companyName, o|$o.shipCity],
    ['orderId', 'orderDate', 'customer', 'shipCity']
)""",
        "**Signature:** ->filter(predicate: Lambda<Boolean>) using association navigation.\n\n"
        "**Pre-project association filter:** `o | $o.customer.country == 'Germany'` "
        "navigates Order→Customer inside the filter predicate. The engine emits a JOIN "
        "or EXISTS subquery to evaluate the condition.\n\n"
        "**Then navigate again in project:** `o|$o.customer.companyName` in the project "
        "lambda reuses the same association — the engine is smart enough to emit one JOIN, "
        "not two.\n\n"
        "**Pattern — filter on FK property, project FK property:** This is the standard "
        "Legend pattern for 'show me orders WHERE customer.country = X, and also show "
        "me the customer name'. Both filter and project can reference the same association "
        "in one clean pipeline.",
        True,
    ),

    "14 · join — Order + Employee": (
        "Joins",
        "Project Order columns alongside the assigned Employee name.",
        """\
northwind::model::Order.all()
->project(
    [o|$o.orderId, o|$o.orderDate, o|$o.freight,
     o|$o.employee.firstName, o|$o.employee.lastName],
    ['orderId', 'orderDate', 'freight', 'empFirst', 'empLast']
)
->sort(~freight->descending())""",
        "**Signature:** Navigate via `$o.employee.firstName` and `$o.employee.lastName` "
        "inside the project lambda list.\n\n"
        "**Association used:** `Order_Employee` — maps the EMP_ID foreign key in T_ORDERS "
        "to T_EMPLOYEES. The engine emits a single LEFT OUTER JOIN.\n\n"
        "**Multiple properties from the same association:** Both `$o.employee.firstName` "
        "and `$o.employee.lastName` cross the same Order→Employee association. The engine "
        "recognises that both paths share the same JOIN and does not duplicate it.\n\n"
        "**Multiplicity:** Order→Employee is many-to-one (`[1]`), so projecting employee "
        "fields never multiplies order rows. If multiplicity were `[*]`, each order row "
        "would fan out to one row per matching employee.",
        True,
    ),

    # ── 4. EXTEND (derived columns) ───────────────────────────────────────────

    "15 · extend — price rank within category (TDS)": (
        "Extend",
        "Add a window-computed rank column to inline TDS data.",
        """\
#TDS
    product, category, unitPrice
    Chai,              Beverages,  18.0
    Chang,             Beverages,  19.0
    Aniseed Syrup,     Condiments, 10.0
    Chef Antons Cajun, Condiments, 22.0
    Northwoods,        Condiments, 40.0
    Pavlova,           Confections,17.45
    Ikura,             Confections,31.0
#->extend(
    over(~category, ~unitPrice->ascending()),
    ~priceRank:{p,w,r|$p->rank($w,$r)}
)""",
        "**Signature:** ->extend(windowSpec: over(...), columnSpec: ~alias:{p,w,r|expr})\n\n"
        "**Arg 1 — over(partitionCol, orderCol):**\n"
        "• `~partitionCol` — the column to PARTITION BY (tilde prefix = column selector).\n"
        "• `~orderCol->ascending()` or `~orderCol->descending()` — the ORDER BY within the window.\n\n"
        "**Arg 2 — ~alias:{p,w,r|expr}:**\n"
        "• `~alias` — the name of the new column added to the TDS.\n"
        "• `{p,w,r|...}` — three-parameter window lambda: `p` = the current partition frame, "
        "`w` = the window spec, `r` = the current row. Pass them to the window function: "
        "`$p->rank($w,$r)`.\n\n"
        "**Window function options:** `rank($w,$r)`, `denseRank($w,$r)`, "
        "`lag($r).colName`, `lead($r).colName`.\n\n"
        "**TDS literal syntax:** `#TDS\\n col1, col2\\n val1, val2\\n#` — "
        "provides inline data without a database. Requires a Runtime in the code block.",
        False,
    ),

    "16 · extend — running revenue by category (TDS)": (
        "Extend",
        "Compute a running cumulative sum within each category partition.",
        """\
#TDS
    product, category, unitPrice
    Aniseed Syrup,     Condiments, 10.0
    Chef Antons Cajun, Condiments, 22.0
    Northwoods,        Condiments, 40.0
    Chai,              Beverages,  18.0
    Chang,             Beverages,  19.0
    Pavlova,           Confections,17.45
    Ikura,             Confections,31.0
#->extend(
    over(~category, ~unitPrice->ascending()),
    ~runningTotal:{p,w,r|$r.unitPrice}:y|$y->plus()
)""",
        "**Signature:** ->extend(windowSpec: over(...), ~alias:{p,w,r|valueExpr}:accumVar|accumExpr)\n\n"
        "**Running aggregation form:** Append `:accumVar|$accumVar->aggFn()` after the "
        "window lambda to produce a running (cumulative) value.\n\n"
        "**Breakdown of `~runningTotal:{p,w,r|$r.unitPrice}:y|$y->plus()`:**\n"
        "• `~runningTotal` — name of the new column.\n"
        "• `{p,w,r|$r.unitPrice}` — per-row value selector: extract unitPrice from each row.\n"
        "• `:y|$y->plus()` — accumulation step: `y` holds the collected values so far; "
        "`->plus()` sums them (running SUM). Use `->times()` for running PRODUCT.\n\n"
        "**over() args:** `~category` partitions; `~unitPrice->ascending()` sets the "
        "cumulative order within each category partition.\n\n"
        "**vs window RANK:** Both use extend(over(...), ...). RANK uses `$p->rank($w,$r)`. "
        "Running SUM uses the accumulator `:y|$y->plus()` form — no `$p`/`$w` needed.",
        False,
    ),

    # ── 5. WINDOW FUNCTIONS ───────────────────────────────────────────────────

    "17 · window RANK — within partition": (
        "Window",
        "Rank each row within a partition, ordered by a key. Gaps for ties.",
        """\
#TDS
    product, category, unitPrice
    Chai,              Beverages, 18.0
    Chang,             Beverages, 19.0
    Aniseed Syrup,     Condiments, 10.0
    Chef Antons Cajun, Condiments, 22.0
    Northwoods Cranberry, Condiments, 40.0
    Queso Cabrales,    Dairy, 21.0
    Queso Manchego,    Dairy, 38.0
    Konbu,             Confections, 6.0
    Ikura,             Confections, 31.0
#->extend(
    over(~category, ~unitPrice->descending()),
    ~priceRank:{p,w,r|$p->rank($w,$r)}
)""",
        "**Signature:** ->extend(over(~partition, ~orderCol->dir()), ~alias:{p,w,r|$p->rank($w,$r)})\n\n"
        "**over() args:**\n"
        "• Arg 1: `~partitionCol` — column selector for PARTITION BY.\n"
        "• Arg 2: `~orderCol->descending()` or `->ascending()` — ORDER BY within the window.\n\n"
        "**Window lambda `{p,w,r|...}`:**\n"
        "• `p` — the partition frame (the set of rows in this partition).\n"
        "• `w` — the window spec (the ordering within the partition).\n"
        "• `r` — the current row.\n"
        "• Call: `$p->rank($w,$r)` — pass all three to rank().\n\n"
        "**RANK behaviour:** Assigns integers 1,2,3,… with gaps on ties. "
        "If two rows tie at rank 2, the next row gets rank 4 (SQL RANK). "
        "Use denseRank() for no-gap consecutive ranks.",
        False,
    ),

    "18 · window DENSE_RANK — no gaps on ties": (
        "Window",
        "Like RANK but consecutive ranks — no gaps when there are ties.",
        """\
#TDS
    product, category, unitPrice
    Chai,              Beverages, 18.0
    Chang,             Beverages, 19.0
    Aniseed Syrup,     Condiments, 10.0
    Chef Antons Cajun, Condiments, 22.0
    Northwoods Cranberry, Condiments, 40.0
    Queso Cabrales,    Dairy, 21.0
    Queso Manchego,    Dairy, 38.0
#->extend(
    over(~category, ~unitPrice->descending()),
    ~denseRank:{p,w,r|$p->denseRank($w,$r)}
)""",
        "**Signature:** ->extend(over(~partition, ~orderCol->dir()), ~alias:{p,w,r|$p->denseRank($w,$r)})\n\n"
        "**denseRank() vs rank():**\n"
        "• `rank($w,$r)` — SQL RANK: gaps on ties (1,2,2,4).\n"
        "• `denseRank($w,$r)` — SQL DENSE_RANK: no gaps (1,2,2,3).\n\n"
        "**Lambda parameter recap — same for all window functions:**\n"
        "• `p` = partition frame → passed to the window function as first arg.\n"
        "• `w` = window ordering spec → passed as second arg.\n"
        "• `r` = current row → passed as third arg.\n\n"
        "**When to use denseRank:** Whenever you need a contiguous ranking (e.g. "
        "'top 3 by price in each category') and don't want gaps caused by tied values.",
        False,
    ),

    "19 · window LAG — look back one row": (
        "Window",
        "Access the previous row's value within the same partition.",
        """\
#TDS
    product, category, unitPrice
    Chai,              Beverages, 18.0
    Chang,             Beverages, 19.0
    Aniseed Syrup,     Condiments, 10.0
    Chef Antons Cajun, Condiments, 22.0
    Northwoods Cranberry, Condiments, 40.0
    Queso Cabrales,    Dairy, 21.0
    Queso Manchego,    Dairy, 38.0
#->extend(
    over(~category, ~unitPrice->ascending()),
    ~prevPrice:{p,w,r|$p->lag($r).unitPrice}
)""",
        "**Signature:** ->extend(over(~partition, ~orderCol->dir()), ~alias:{p,w,r|$p->lag($r).colName})\n\n"
        "**lag($r).colName:**\n"
        "• `$p->lag($r)` — returns the *previous* row in the window ordering as a row object.\n"
        "• `.unitPrice` — property access on the lagged row to extract the value.\n"
        "• The first row in each partition has no previous row → returns null.\n\n"
        "**over() ordering matters:** The ordering in over() determines what 'previous' means. "
        "Here `~unitPrice->ascending()` means lag() looks at the row with the next-lower unitPrice.\n\n"
        "**SQL equivalent:** `LAG(unit_price) OVER (PARTITION BY category ORDER BY unit_price ASC)`.\n\n"
        "**Use cases:** Period-over-period change, finding the prior price, "
        "computing deltas between consecutive rows within a group.",
        False,
    ),

    "20 · window LEAD — look ahead one row": (
        "Window",
        "Access the next row's value within the same partition.",
        """\
#TDS
    product, category, unitPrice
    Chai,              Beverages, 18.0
    Chang,             Beverages, 19.0
    Aniseed Syrup,     Condiments, 10.0
    Chef Antons Cajun, Condiments, 22.0
    Northwoods Cranberry, Condiments, 40.0
    Queso Cabrales,    Dairy, 21.0
    Queso Manchego,    Dairy, 38.0
#->extend(
    over(~category, ~unitPrice->ascending()),
    ~nextPrice:{p,w,r|$p->lead($r).unitPrice}
)""",
        "**Signature:** ->extend(over(~partition, ~orderCol->dir()), ~alias:{p,w,r|$p->lead($r).colName})\n\n"
        "**lead($r).colName:**\n"
        "• `$p->lead($r)` — returns the *next* row in the window ordering as a row object.\n"
        "• `.unitPrice` — property access on the lead row to extract the value.\n"
        "• The last row in each partition has no next row → returns null.\n\n"
        "**lag() vs lead():**\n"
        "• `lag($r)` — look back one row (previous in ordering).\n"
        "• `lead($r)` — look ahead one row (next in ordering).\n"
        "Both use the same lambda signature `{p,w,r|$p->fn($r).col}` and the same over() spec.\n\n"
        "**SQL equivalent:** `LEAD(unit_price) OVER (PARTITION BY category ORDER BY unit_price ASC)`.",
        False,
    ),

    "21 · window running SUM — cumulative total": (
        "Window",
        "Compute a running (cumulative) total within a partition.",
        """\
#TDS
    product, category, unitPrice
    Aniseed Syrup,     Condiments, 10.0
    Chef Antons Cajun, Condiments, 22.0
    Northwoods Cranberry, Condiments, 40.0
    Konbu,             Confections, 6.0
    Ikura,             Confections, 31.0
    Chai,              Beverages, 18.0
    Chang,             Beverages, 19.0
#->extend(
    over(~category, ~unitPrice->ascending()),
    ~runningTotal:{p,w,r|$r.unitPrice}:y|$y->plus()
)""",
        "**Signature:** ->extend(over(~partition, ~orderCol->dir()), ~alias:{p,w,r|$r.colName}:y|$y->aggFn())\n\n"
        "**Running aggregation breakdown:**\n"
        "• `{p,w,r|$r.unitPrice}` — value selector lambda: extract unitPrice from each row `r`.\n"
        "• `:y|$y->plus()` — accumulator step: `y` is the running collection of values; "
        "`->plus()` sums them cumulatively (SQL SUM OVER with ROWS UNBOUNDED PRECEDING).\n\n"
        "**Accumulator functions:**\n"
        "• `->plus()` → running SUM.\n"
        "• `->times()` → running PRODUCT.\n\n"
        "**Key distinction from RANK/LAG:** RANK and LAG use `{p,w,r|$p->fn($w,$r)}` — "
        "the partition frame `p` drives the function. Running SUM uses `{p,w,r|$r.col}:y|$y->plus()` "
        "— `r` (the current row) provides the value, and `:y|...` accumulates it.",
        False,
    ),

    # ── 6. ASOF JOIN ─────────────────────────────────────────────────────────

    "22 · asOfJoin — latest quote per trade (time)": (
        "AsOf Join",
        "For each trade, find the most recent quote that came BEFORE it.",
        """\
#TDS
    tradeId, symbol, tradeTime
    1, CHAI,  %2024-01-15T10:30:00
    2, CHANG, %2024-01-15T10:30:00
    3, CHAI,  %2024-01-15T11:30:00
    4, CHANG, %2024-01-15T11:45:00
#->asOfJoin(
    #TDS
        quoteSymbol, quoteTime, price
        CHAI,  %2024-01-15T10:00:00, 18.0
        CHANG, %2024-01-15T10:00:00, 19.0
        CHAI,  %2024-01-15T11:00:00, 18.5
        CHANG, %2024-01-15T11:15:00, 19.5
    #,
    {t, q | $t.tradeTime > $q.quoteTime},
    {t, q | $t.symbol == $q.quoteSymbol}
)""",
        "**Signature:** ->asOfJoin(rightTDS, timeCondition: Lambda<Boolean>, equalityCondition: Lambda<Boolean>)\n\n"
        "**Arg 1 — rightTDS:** The right-hand TDS to join against. Can be a `#TDS...#` literal "
        "or the result of any TDS-producing expression.\n\n"
        "**Arg 2 — timeCondition `{t,q|$t.timeCol > $q.timeCol}`:**\n"
        "• `t` = left row (trade), `q` = right row (quote).\n"
        "• Must be a strict inequality on the time columns (`>`).\n"
        "• Selects: for each trade, all quotes where quoteTime is before tradeTime.\n"
        "• From those candidates, the engine picks the *most recent* (latest quoteTime).\n\n"
        "**Arg 3 — equalityCondition `{t,q|$t.symbol == $q.quoteSymbol}`:**\n"
        "• An optional additional equality predicate — filters candidates further before "
        "selecting the most recent match.\n"
        "• Use this for symbol matching, instrument ID, or any partition key.\n\n"
        "**DateTime literal syntax:** `%2024-01-15T10:30:00` — the `%` prefix marks a "
        "Pure DateTime literal. All datetime columns in TDS literals must use this form.",
        False,
    ),

    "23 · asOfJoin — simple (time only, no equality)": (
        "AsOf Join",
        "AsOf join on time only — no additional equality filter.",
        """\
#TDS
    tradeId, tradeTime
    1, %2024-01-15T10:30:00
    2, %2024-01-15T10:50:00
    3, %2024-01-15T11:30:00
#->asOfJoin(
    #TDS
        quoteId, quoteTime, marketPrice
        A, %2024-01-15T10:15:00, 100.0
        B, %2024-01-15T10:45:00, 102.5
        C, %2024-01-15T11:15:00, 105.0
        D, %2024-01-15T12:00:00, 108.0
    #,
    {t, q | $t.tradeTime > $q.quoteTime}
)""",
        "**Signature:** ->asOfJoin(rightTDS, timeCondition: Lambda<Boolean>)\n\n"
        "**Two-arg form (no equality condition):** When there is only one condition, "
        "every left row is matched to the *single most recent* right row whose time "
        "is strictly less than the left row's time — no symbol/key partitioning.\n\n"
        "**How the engine picks the match:**\n"
        "1. Filter right rows where `$q.quoteTime < $t.tradeTime` (strict `>` in the lambda).\n"
        "2. Among those candidates, pick the one with the maximum quoteTime.\n"
        "3. If no right row qualifies, the left row is still included with null right-side columns.\n\n"
        "**Worked example from the data above:**\n"
        "• tradeId=1 (10:30) → quoteB (10:45) is *after* — not eligible. Matches quoteA (10:15).\n"
        "• tradeId=2 (10:50) → quoteB (10:45) is before. Matches quoteB (highest before 10:50).\n"
        "• tradeId=3 (11:30) → quoteC (11:15) is before; quoteD (12:00) is after. Matches quoteC.\n\n"
        "**DateTime literal:** prefix with `%` — e.g. `%2024-01-15T10:30:00`.",
        False,
    ),

    # ── Column manipulation ────────────────────────────────────────────────────

    "24 · rename — rename a TDS column": (
        "Column Manipulation",
        "Rename one column in a TDS without touching any other columns.",
        """\
northwind::model::Product.all()
->project([p|$p.productName, p|$p.unitPrice], ['product','price'])
->sort(~price->descending())
->take(5)
->rename(~price, ~unitPrice)""",
        "**Signature:** ->rename(oldCol: ColSpec, newCol: ColSpec)\n\n"
        "**Arg 1 — oldCol:** The existing column to rename, referenced with the tilde prefix: `~price`. "
        "The tilde (`~`) is the ColSpec constructor in Pure — it selects a column by its alias name.\n\n"
        "**Arg 2 — newCol:** The new name for that column, also written as a ColSpec: `~unitPrice`. "
        "No lambda is involved — rename is purely a schema-level operation.\n\n"
        "**Effect:** Only the column header changes. All other columns and all row values are preserved "
        "exactly as-is. The renamed column keeps its position in the TDS.\n\n"
        "**SQL equivalent:** `SELECT product, price AS unitPrice FROM ...`\n\n"
        "**Typical use:** After `project()` produces a computed alias (e.g. `'price'`) you want to "
        "standardise before passing downstream, or when `concatenate()` requires matching column names.",
        True,
    ),

    "25 · select — narrow columns from a TDS": (
        "Column Manipulation",
        "Drop unwanted columns by selecting only the ones you need.",
        """\
northwind::model::Product.all()
->project([p|$p.productName, p|$p.unitPrice, p|$p.unitsInStock],
          ['product','price','stock'])
->filter({r | $r.price > 20.0})
->select(~[product, price])""",
        "**Signature:** ->select(cols: ColSpecArray)\n\n"
        "**Arg 1 — cols:** A ColSpecArray listing every column to keep, written as `~[col1, col2, ...]`. "
        "Use `~colName` (no brackets) when selecting a single column.\n\n"
        "**Effect:** Returns a new TDS containing only the listed columns, in the order given. "
        "Columns not listed are dropped. Row count is unchanged.\n\n"
        "**SQL equivalent:** `SELECT product, price FROM (...)`  — a projection at the TDS level.\n\n"
        "**Contrast with project():** `project()` maps class properties → TDS columns (with lambdas). "
        "`select()` works on an already-projected TDS and simply removes columns — no lambdas needed.\n\n"
        "**Typical use:** After a wide `project()` that computed many columns, narrow the result "
        "before passing it to `groupBy()`, `concatenate()`, or an API boundary.",
        True,
    ),

    # ── Set operations ─────────────────────────────────────────────────────────

    "26 · concatenate — union two TDS vertically": (
        "Set Operations",
        "Stack two TDS with identical schemas on top of each other (UNION ALL).",
        """\
northwind::model::Product.all()
->project([p|$p.productName, p|$p.unitPrice], ['product','price'])
->filter({r | $r.price > 30.0})
->concatenate(
    northwind::model::Product.all()
    ->project([p|$p.productName, p|$p.unitPrice], ['product','price'])
    ->filter({r | $r.price < 10.0})
)""",
        "**Signature:** ->concatenate(otherTDS: Relation<T>)\n\n"
        "**Arg 1 — otherTDS:** The second TDS to append. It must have exactly the same column names "
        "and compatible types as the first TDS. The schemas must match — use `rename()` or `select()` "
        "to align them if necessary.\n\n"
        "**Result:** A new TDS whose row count equals `|left| + |right|`. "
        "Duplicates are *not* removed — this is UNION ALL, not UNION DISTINCT.\n\n"
        "**SQL equivalent:** `SELECT ... FROM ... WHERE price > 30 UNION ALL SELECT ... WHERE price < 10`\n\n"
        "**Ordering:** The result retains the original row order of each part (left rows first, "
        "then right rows). Apply `->sort()` after if you need a global order.\n\n"
        "**Typical use:** Combine two filtered subsets, merge historical + current data, "
        "or assemble a multi-region result set before a single final sort/groupBy.",
        True,
    ),

    # ── Explicit join ──────────────────────────────────────────────────────────

    "27 · join — INNER join on predicate": (
        "Joins",
        "Explicit INNER join on an arbitrary boolean predicate — only matching rows on both sides survive.",
        """\
#TDS
    emp, deptId
    Alice, 1
    Bob,   2
    Carol, 1
    Dave,  3
#->join(
    #TDS
        deptId, deptName, budget
        1, Engineering, 500000
        2, Sales,       200000
    #,
    JoinType.INNER,
    {a,b | $a.deptId == $b.deptId}
)""",
        "**Signature:** ->join(rightTDS, joinKind: JoinKind, condition: Lambda<Boolean>)\n\n"
        "**Arg 1 — rightTDS:** The right-hand relation. Can be a TDS literal, a class query, "
        "or any other relation expression.\n\n"
        "**Arg 2 — joinKind:** One of `JoinType.INNER`, `JoinType.LEFT`, `JoinType.RIGHT`, "
        "or `JoinType.FULL`. Controls which unmatched rows are kept.\n\n"
        "**Arg 3 — condition:** A two-parameter lambda `{a,b | ...}` where `a` is a row from "
        "the left TDS and `b` is a row from the right. Return a Boolean — typically an equality "
        "like `$a.deptId == $b.deptId`, or a compound like `$a.k1 == $b.k1 && $a.k2 == $b.k2`.\n\n"
        "**Result:** Left columns followed by all right columns. If column names clash (e.g. `deptId` "
        "appears in both), both are kept — disambiguate downstream with `select()` or `rename()`.\n\n"
        "**INNER semantics:** Only rows where the condition is `true` appear in the result. "
        "Dave (deptId=3) is dropped because no right row has deptId=3.\n\n"
        "**SQL equivalent:** `SELECT * FROM left INNER JOIN right ON left.deptId = right.deptId`\n\n"
        "**vs association navigation:** Association navigation (`$p.category.categoryName`) compiles "
        "to a LEFT JOIN implicitly. Use explicit `join()` when you need INNER, RIGHT, or FULL semantics, "
        "or when joining two independent TDS expressions without a modelled association.",
        False,
    ),

    "28 · join — LEFT join (keep all left rows)": (
        "Joins",
        "LEFT join preserves every left row; unmatched rows get null right-side columns.",
        """\
#TDS
    emp, deptId
    Alice, 1
    Bob,   2
    Carol, 9
#->join(
    #TDS
        deptId, deptName
        1, Engineering
        2, Sales
    #,
    JoinType.LEFT,
    {a,b | $a.deptId == $b.deptId}
)""",
        "**Signature:** ->join(rightTDS, JoinType.LEFT, condition: Lambda<Boolean>)\n\n"
        "**JoinType.LEFT semantics:** Every row from the left TDS appears in the result exactly once. "
        "If the condition matches one or more right rows, those right columns are filled in. "
        "If no right row matches (Carol, deptId=9), the right-side columns are null.\n\n"
        "**Result row count:** Always `>= |left|`. If a left row matches *multiple* right rows, "
        "it appears once per match (fan-out). If it matches zero, it appears once with nulls.\n\n"
        "**JoinType options recap:**\n"
        "• `JoinType.INNER` — only matched rows (both sides must match)\n"
        "• `JoinType.LEFT`  — all left rows; right nulls on no match\n"
        "• `JoinType.RIGHT` — all right rows; left nulls on no match\n"
        "• `JoinType.FULL`  — all rows from both sides; nulls where no match\n\n"
        "**SQL equivalent:** `SELECT * FROM left LEFT JOIN right ON left.deptId = right.deptId`",
        False,
    ),

    # ── Slicing ────────────────────────────────────────────────────────────────

    "29 · drop — skip the first N rows": (
        "Slicing",
        "Remove the first N rows from a sorted TDS — the complement of take().",
        """\
northwind::model::Product.all()
->project([p|$p.productName, p|$p.unitPrice], ['product','price'])
->sort(~price->descending())
->drop(5)""",
        "**Signature:** ->drop(n: Integer)\n\n"
        "**Arg 1 — n:** Number of rows to skip from the *top* of the relation. Must be ≥ 0.\n\n"
        "**Result:** A TDS containing all rows *after* the first n. Row count = `max(0, |input| - n)`.\n\n"
        "**SQL equivalent:** `OFFSET 5` (with an ORDER BY to make it deterministic).\n\n"
        "**Relationship to take() / slice():**\n"
        "• `->take(5)` — keep rows 1–5 (TOP 5 / LIMIT 5)\n"
        "• `->drop(5)` — skip rows 1–5, keep the rest\n"
        "• `->slice(2, 7)` — keep rows at 0-based indices 2, 3, 4, 5, 6 (five rows)\n\n"
        "**Determinism:** `drop()` is only meaningful after an explicit `->sort()`. Without a sort "
        "the engine may return any N rows and the result is undefined.",
        True,
    ),

    "30 · slice — rows in a half-open range [start, stop)": (
        "Slicing",
        "Extract a window of rows by 0-based index range — useful for pagination.",
        """\
northwind::model::Product.all()
->project([p|$p.productName, p|$p.unitPrice], ['product','price'])
->sort(~price->descending())
->slice(2, 7)""",
        "**Signature:** ->slice(start: Integer, stop: Integer)\n\n"
        "**Arg 1 — start:** 0-based index of the first row to include (inclusive).\n\n"
        "**Arg 2 — stop:** 0-based index of the first row to *exclude* (exclusive). "
        "The result contains rows at indices `start, start+1, …, stop-1`.\n\n"
        "**Row count returned:** `stop - start` (provided the relation is large enough).\n\n"
        "**Example:** `->slice(2, 7)` on 15 products → rows at indices 2, 3, 4, 5, 6 → 5 rows.\n\n"
        "**SQL equivalent:** `LIMIT 5 OFFSET 2`\n\n"
        "**Pagination pattern:**\n"
        "  Page 1 → `->slice(0, 10)`\n"
        "  Page 2 → `->slice(10, 20)`\n"
        "  Page 3 → `->slice(20, 30)`\n\n"
        "**vs take() / drop():** `->take(n)` ≡ `->slice(0, n)`. "
        "`->drop(k)->take(n)` ≡ `->slice(k, k+n)` — slice is the more general form.",
        True,
    ),

    "31 · first — single top row after sort": (
        "Slicing",
        "Return exactly one row — the first row of the relation after sorting.",
        """\
northwind::model::Product.all()
->project([p|$p.productName, p|$p.unitPrice], ['product','price'])
->sort(~price->descending())
->first()""",
        "**Signature:** ->first()\n\n"
        "**Args:** None. `first()` takes no parameters — it simply returns the first row.\n\n"
        "**Result:** A Relation with exactly 1 row. If the input is empty, the result is empty "
        "(0 rows, not an error).\n\n"
        "**SQL equivalent:** `LIMIT 1`\n\n"
        "**Determinism:** Like `take()` and `drop()`, `first()` is only meaningful after an explicit "
        "`->sort()`. Without a sort the engine picks an arbitrary row.\n\n"
        "**vs take(1):** Functionally identical — `->first()` is idiomatic when the intent is "
        "'give me the single best/latest/cheapest row', while `->take(1)` is used when you plan "
        "to generalise to `take(n)` later.\n\n"
        "**Typical use:** Find the most expensive product, the latest order, the largest holding.",
        True,
    ),

    # ── Window functions (additional) ──────────────────────────────────────────

    "32 · window rowNumber — sequential position in partition": (
        "Window Functions",
        "Assign a 1-based sequential row number within each partition, ordered by the window spec.",
        """\
#TDS
    product,           category,   unitPrice
    Chai,              Beverages,  18.0
    Chang,             Beverages,  19.0
    Aniseed Syrup,     Condiments, 10.0
    Chef Anton Cajun,  Condiments, 22.0
    Ikura,             Seafood,    31.0
#->extend(over(~category, ~unitPrice->descending()), ~rowNum:{p,w,r|$p->rowNumber($w,$r)})""",
        "**Signature:** ->extend(over(partition, orderSpec), ~alias:{p,w,r|$p->rowNumber($w,$r)})\n\n"
        "**rowNumber()** is a window function called inside the `extend()` lambda:\n\n"
        "**Lambda parameters — p, w, r:**\n"
        "• `p` — the Relation (partition view) passed to the window function\n"
        "• `w` — the `_Window` spec produced by `over()` (partition + order)\n"
        "• `r` — the current row being evaluated\n\n"
        "**over() args:**\n"
        "• Arg 1 — partition col(s): `~category` groups rows into per-category windows. "
        "Use `[]` for no partitioning (global row number).\n"
        "• Arg 2 — order col(s): `~unitPrice->descending()` defines the sort within each partition.\n\n"
        "**Result:** Integer 1, 2, 3, … within each partition. No gaps, no ties — every row gets "
        "a unique number even when values are identical (contrast with `rank()` which produces gaps "
        "on ties, and `denseRank()` which produces no gaps).\n\n"
        "**SQL equivalent:** `ROW_NUMBER() OVER (PARTITION BY category ORDER BY unitPrice DESC)`",
        False,
    ),

    "33 · window ntile — divide rows into N equal buckets": (
        "Window Functions",
        "Assign each row to one of N equal-sized buckets (tiles) ordered by the window spec.",
        """\
#TDS
    product,           unitPrice
    Konbu,             6.0
    Aniseed Syrup,     10.0
    Genen Shouyu,      15.5
    Chai,              18.0
    Chang,             19.0
    Tofu,              23.25
    Chef Anton Cajun,  22.0
    Ikura,             31.0
#->extend(over([], ~unitPrice->ascending()), ~quartile:{p,w,r|$p->ntile($w,$r,4)})""",
        "**Signature:** ->extend(over(partition, orderSpec), ~alias:{p,w,r|$p->ntile($w,$r,N)})\n\n"
        "**Arg inside ntile — N:** Integer tile count. 4 = quartiles, 10 = deciles, 100 = percentiles.\n\n"
        "**Lambda parameters — p, w, r:** Same convention as all window functions:\n"
        "• `p` — the Relation (window view)\n"
        "• `w` — the `_Window` spec from `over()`\n"
        "• `r` — the current row\n\n"
        "**How tiles are assigned:** Rows are sorted by the order spec within each partition, "
        "then divided as evenly as possible into N buckets (numbered 1..N). "
        "If the row count is not divisible by N, earlier buckets get one extra row.\n\n"
        "**over() arg 1 — partition:** `[]` means no partitioning — all 8 rows form one global window. "
        "Use `~col` or `~[col1, col2]` to partition first.\n\n"
        "**Result column:** Integer in range [1, N]. Tile 1 = lowest values, tile N = highest.\n\n"
        "**SQL equivalent:** `NTILE(4) OVER (ORDER BY unitPrice ASC)`\n\n"
        "**Typical use:** Assign quartile/decile labels for distribution analysis or binning.",
        False,
    ),

    "34 · window percentRank — relative rank as a fraction": (
        "Window Functions",
        "Compute each row's relative rank within its partition as a float in [0.0, 1.0].",
        """\
#TDS
    product,           category,   unitPrice
    Konbu,             Seafood,    6.0
    Aniseed Syrup,     Condiments, 10.0
    Chai,              Beverages,  18.0
    Chang,             Beverages,  19.0
    Chef Anton Cajun,  Condiments, 22.0
    Ikura,             Seafood,    31.0
#->extend(over(~category, ~unitPrice->ascending()), ~pctRank:{p,w,r|$p->percentRank($w,$r)})""",
        "**Signature:** ->extend(over(partition, orderSpec), ~alias:{p,w,r|$p->percentRank($w,$r)})\n\n"
        "**percentRank()** computes: `(rank - 1) / (N - 1)` where `rank` is the 1-based rank "
        "of the row and `N` is the number of rows in the partition.\n\n"
        "**Result range:** Always in [0.0, 1.0].\n"
        "• The first row (lowest value in ascending order) always gets 0.0.\n"
        "• The last row (highest value) always gets 1.0.\n"
        "• Tied rows share the same percentRank.\n\n"
        "**Lambda parameters — p, w, r:** Standard window lambda convention "
        "(p = partition view, w = window spec, r = current row).\n\n"
        "**Example (Seafood partition, ascending price):**\n"
        "• Konbu (6.0)  → rank 1 of 2 → (1-1)/(2-1) = 0.0\n"
        "• Ikura (31.0) → rank 2 of 2 → (2-1)/(2-1) = 1.0\n\n"
        "**SQL equivalent:** `PERCENT_RANK() OVER (PARTITION BY category ORDER BY unitPrice ASC)`\n\n"
        "**vs cumulativeDistribution:** percentRank uses `(rank-1)/(N-1)`; "
        "cumulativeDistribution uses `rank/N` — so cumDist is always ≥ percentRank.",
        False,
    ),

    "35 · window cumulativeDistribution — fraction of rows ≤ current": (
        "Window Functions",
        "For each row, compute the fraction of rows in the partition with value ≤ the current row's value.",
        """\
#TDS
    product,           category,   unitPrice
    Konbu,             Seafood,    6.0
    Aniseed Syrup,     Condiments, 10.0
    Chai,              Beverages,  18.0
    Chang,             Beverages,  19.0
    Chef Anton Cajun,  Condiments, 22.0
    Ikura,             Seafood,    31.0
#->extend(over(~category, ~unitPrice->ascending()), ~cumDist:{p,w,r|$p->cumulativeDistribution($w,$r)})""",
        "**Signature:** ->extend(over(partition, orderSpec), ~alias:{p,w,r|$p->cumulativeDistribution($w,$r)})\n\n"
        "**cumulativeDistribution()** computes: `rank / N` where `rank` is the number of rows "
        "in the partition with value ≤ the current row's value, and `N` is the total partition size.\n\n"
        "**Result range:** Always in (0.0, 1.0] — the first row can be > 0 if there are ties "
        "at the bottom; the last row is always exactly 1.0.\n\n"
        "**Lambda parameters — p, w, r:** Standard window lambda convention "
        "(p = partition view, w = window spec, r = current row).\n\n"
        "**Example (Seafood partition, ascending price):**\n"
        "• Konbu (6.0)  → 1 row ≤ 6.0 out of 2 total → 1/2 = 0.5\n"
        "• Ikura (31.0) → 2 rows ≤ 31.0 out of 2 total → 2/2 = 1.0\n\n"
        "**SQL equivalent:** `CUME_DIST() OVER (PARTITION BY category ORDER BY unitPrice ASC)`\n\n"
        "**vs percentRank:** `percentRank` starts at 0.0 and uses `(rank-1)/(N-1)`; "
        "`cumulativeDistribution` starts at `1/N` and uses `rank/N`. "
        "For N=1 (single row in partition), cumDist=1.0, percentRank=0.0.",
        False,
    ),

    # ── Variant / flatten ──────────────────────────────────────────────────────

    "36 · flatten — explode array column into rows (reference)": (
        "Variant / Flatten",
        "Unnest an array-valued column so each element becomes its own row. "
        "⚠ Requires lateral + Variant support — reference syntax only in this playground.",
        """\
// ── Pattern 1: lateral + flatten (explode a JSON array column) ──────────────
// Requires: lateral() and Variant type — not yet in Legend Workbench.
// Shown here as reference; paste into the full Legend engine to execute.
//
// #TDS
//     id, payload:meta::pure::metamodel::variant::Variant
//     1, "[1,2,3]"
//     2, "[4,5,6]"
//     3, "[7,8,9]"
// #->lateral(x | $x.payload->toMany(@Integer)->flatten(~integers))
//
// Result (15 rows):
//   id | payload    | integers
//   1  | "[1,2,3]"  | 1
//   1  | "[1,2,3]"  | 2
//   1  | "[1,2,3]"  | 3
//   2  | "[4,5,6]"  | 4  ...

// ── Pattern 2: scalar list → single-column TDS ───────────────────────────────
// Also requires full engine (array literal as relation root).
//
// [1, 2, 3, 4]->flatten(~integer)
//
// Result (4 rows):  integer | 1 | 2 | 3 | 4

// ── Pattern 3: lateral + flatten + extend ────────────────────────────────────
// Unnest then immediately add a window column:
//
// $tds->lateral(x | $x.payload->toMany(@Integer)->flatten(~value))
//     ->extend(over(~id, ~value->ascending()), ~rowNum:{p,w,r|$p->rowNumber($w,$r)})

// ── Runnable demo (TDS with Variant column — no unnesting) ───────────────────
// The Variant column is readable; unnesting requires lateral.
#TDS
    id, payload:meta::pure::metamodel::variant::Variant
    1, "[1,2,3]"
    2, "[4,5,6]"
    3, "[7,8,9]"
#->select(~[id, payload])""",
        "**Signature:** values:T[*]->flatten(colSpec: ColSpec<Z=(?:T)>) : Relation<Z>[1]\n\n"
        "**⚠ Engine note:** `flatten` passes 7/7 DuckDB PCT tests in the full FINOS Legend engine. "
        "In this playground (Legend Workbench) the two required primitives — `lateral()` and `fromJson()` "
        "— are not yet implemented, so the real unnesting queries cannot be executed here. "
        "The runnable line above demonstrates that a Variant-typed TDS column is parsed correctly; "
        "the commented patterns show the complete syntax for use in the full engine.\n\n"
        "**Arg 1 — values:** The collection to unnest. Typically the result of navigating a "
        "Variant column: `$row.payload->toMany(@Integer)`. `toMany(@T)` casts the Variant to "
        "a typed list. Supported element types: `@Integer`, `@Float`, `@String`, `@Variant`.\n\n"
        "**Arg 2 — colSpec:** A `ColSpec` naming the output column: `~integers`, `~values`, etc. "
        "The tilde prefix (`~`) is the ColSpec constructor.\n\n"
        "**lateral() — the outer wrapper:**\n"
        "`->lateral(x | expr)` is the relation-level loop that calls the lambda once per row "
        "of the left TDS (here named `x`), appends the resulting relation columns to that row, "
        "and unions all per-row results. It is the Pure equivalent of SQL `CROSS JOIN LATERAL` "
        "or `UNNEST(...) WITH ORDINALITY`.\n\n"
        "**Full pipeline in the real engine:**\n"
        "1. Start with a TDS that has a `Variant`-typed column containing JSON arrays.\n"
        "2. `->lateral(x | $x.payload->toMany(@Integer)->flatten(~value))` — for each row, "
        "cast the payload Variant to `Integer[*]`, flatten to a one-column TDS, join back.\n"
        "3. Chain `->filter`, `->extend`, `->sort` etc. on the now-unnested result.\n\n"
        "**SQL equivalent:** `SELECT id, payload, f.value FROM tds CROSS JOIN LATERAL "
        "UNNEST(JSON_EXTRACT_PATH(payload, '$')) AS f(value)`\n\n"
        "**PCT test coverage (DuckDB):** 7/7 passing — "
        "Scalar, Variant_Array, Variant_Map, Variant_Navigation, LateralJoin, "
        "LateralJoin_Nested, LateralJoin_Nested_Extend.",
        False,
        False,   # executable=False → parametrised test skips this entry
    ),
}

