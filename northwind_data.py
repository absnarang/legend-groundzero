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
// ── Domain classes ─────────────────────────────────────────────────────────

Class northwind::model::Category
{
    categoryId:   Integer[1];
    categoryName: String[1];
    description:  String[0..1];
}

Class northwind::model::Supplier
{
    supplierId:  Integer[1];
    companyName: String[1];
    country:     String[0..1];
    city:        String[0..1];
}

Class northwind::model::Product
{
    productId:    Integer[1];
    productName:  String[1];
    unitPrice:    Float[1];
    unitsInStock: Integer[1];
    discontinued: Integer[1];
}

Class northwind::model::Customer
{
    customerId:  String[1];
    companyName: String[1];
    contactName: String[0..1];
    city:        String[0..1];
    country:     String[0..1];
}

Class northwind::model::Employee
{
    employeeId: Integer[1];
    firstName:  String[1];
    lastName:   String[1];
    title:      String[0..1];
    city:       String[0..1];
    country:    String[0..1];
    hireDate:   String[0..1];
}

Class northwind::model::Order
{
    orderId:     Integer[1];
    orderDate:   String[0..1];
    freight:     Float[0..1];
    shipCountry: String[0..1];
    shipCity:    String[0..1];
}

Class northwind::model::OrderDetail
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
        "project() maps each lambda to a column alias. The result is a TDS (Tabular Data Set). "
        "Use camelCase aliases — they become the column names for downstream filter/sort.",
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
        "filter() before project() works on the class properties directly. "
        "After project() you use $row.alias syntax (see example 04).",
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
        "sort('col') sorts ascending. For descending, use sort(~col->descending()). "
        "Chain multiple sorts: ->sort(~a->descending())->sort('b').",
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
        "take(N) is the Pure equivalent of SQL LIMIT. Always pair with sort() "
        "to get a deterministic top-N.",
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
        "Once you've projected, use $row.alias to reference columns. "
        "The && operator maps to SQL AND. Use || for OR.",
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
        "distinct() maps to SQL DISTINCT. Apply it after project() on the TDS. "
        "Useful for finding unique values of a column.",
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
        "groupBy() takes three lists: (1) group-key lambdas, "
        "(2) aggregation lambdas, (3) output column aliases. "
        "Aggregators: ->count(), ->sum(), ->avg(), ->min(), ->max().",
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
        "->sum() aggregates Float or Integer columns. The output alias "
        "is the third list element matching the aggregation position.",
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
        "Multiple aggregations: add one lambda per agg to the second list, "
        "and one alias per result to the third list. "
        "Here we navigate Product → Category to get categoryName.",
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
        "There is no dedicated HAVING clause in Pure — apply "
        "->filter({row | ...}) after ->groupBy() instead. "
        "The engine translates it into a SQL HAVING or subquery WHERE.",
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
        "Navigation like $p.category.categoryName crosses the Product_Category "
        "association. The engine emits a LEFT OUTER JOIN on the foreign key. "
        "No explicit join syntax required.",
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
        "$d.product.productName navigates the OrderDetail→Product association. "
        "The engine emits a LEFT OUTER JOIN on PRODUCT_ID. "
        "Combined with sort + take, this gives the top 10 largest order lines.",
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
        "Filtering on $o.customer.country before project generates a "
        "SQL EXISTS or JOIN + WHERE — the engine picks the most efficient form. "
        "The result only shows rows where the related country matches.",
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
        "Order→Employee is navigated via the EMP_ID foreign key. "
        "Projecting Order's own columns (orderId, freight) together with "
        "Employee columns (firstName, lastName) generates a single LEFT OUTER JOIN.",
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
        "extend() with over() appends a window-computed column to the TDS. "
        "over(~partition, ~orderKey) defines the window. "
        "The result column (priceRank) appears after all existing columns. "
        "Window extends can be chained for multiple derived columns.",
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
        "Running SUM uses {p,w,r|$r.col}:y|$y->plus(). "
        "The inner lambda selects the value per row; :y|$y->plus() accumulates it "
        "within each partition ordered by unitPrice. "
        "Compare this to window RANK — both use extend(over(…), …) syntax.",
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
        "over(~partition, ~orderKey) defines the window frame. "
        "rank() assigns 1,2,3… with gaps on ties (SQL RANK). "
        "The TDS literal (#TDS…#) provides inline test data — no DB seeding needed.",
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
        "denseRank() maps to SQL DENSE_RANK. If two products share a rank, "
        "the next product gets rank+1 (not rank+2). "
        "Use when you want contiguous rank numbers despite ties.",
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
        "lag($r).colName retrieves the previous row's value in the window "
        "(SQL LAG). The first row in each partition returns null. "
        "Useful for period-over-period comparisons.",
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
        "lead($r).colName retrieves the next row's value (SQL LEAD). "
        "The last row in each partition returns null. "
        "Useful to show what comes next without a self-join.",
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
        "Running SUM uses the form {p,w,r|$r.col}:y|$y->plus(). "
        "The inner lambda selects the value; :y|$y->plus() accumulates it. "
        "Use ->sum() for a total, ->plus() for a running accumulation.",
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
        "asOfJoin(rightTDS, timeCondition, equalityCondition) joins each left row "
        "to the most recent right row satisfying both conditions. "
        "The time condition selects the correct quote; the equality condition "
        "ensures symbol matching. Maps to DuckDB ASOF JOIN.",
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
        "When there is only one condition (time), every trade is matched to "
        "the last quote whose quoteTime is strictly before the tradeTime. "
        "tradeId=3 gets quoteC (11:15), not quoteD (12:00).",
        False,
    ),
}

