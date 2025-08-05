import os
import pandas as pd
from utils.load_config import LoadConfig
from sqlalchemy import create_engine, inspect, text

class PrepareSQLFromTabularData:
    """
    Prepares a SQL database from CSV/XLSX files in a specified directory
    and enforces PK/FK constraints for BuyerOrder and CurrentStock.
    """

    def __init__(self, files_dir) -> None:
        APPCFG = LoadConfig()
        self.files_directory = files_dir
        self.file_dir_list = os.listdir(files_dir)

        db_path = APPCFG.stored_csv_xlsx_sqldb_directory
        db_path = f"sqlite:///{db_path}"
        self.engine = create_engine(db_path)

        print("Number of files found:", len(self.file_dir_list))

    def _prepare_db(self):
        """Create tables with PK/FK and insert cleaned CSV/XLSX data."""
        
        buyer_order_df = None
        current_stock_df = None
        
        # Read files
        for file in self.file_dir_list:
            full_file_path = os.path.join(self.files_directory, file)
            file_name, file_extension = os.path.splitext(file)
            table_name = file_name.lower().replace(" ", "_")
            
            if file_extension.lower() == ".csv":
                df = pd.read_csv(full_file_path, low_memory=False)
            elif file_extension.lower() == ".xlsx":
                df = pd.read_excel(full_file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            if "buyerorder" in table_name:
                buyer_order_df = df.copy()
            elif "currentstock" in table_name:
                current_stock_df = df.copy()
        
        if buyer_order_df is None or current_stock_df is None:
            raise ValueError("Both BuyerOrder and CurrentStock files are required.")

        # --- Clean BuyerOrder ---
        buyer_order_df.drop_duplicates(subset=["buyerorderno"], inplace=True)
        buyer_order_df["buyerorderno"] = buyer_order_df["buyerorderno"].astype(str).str.strip().str.upper()

        # --- Clean CurrentStock ---
        current_stock_df["ocnum"] = current_stock_df["ocnum"].astype(str).str.strip().str.upper()

        # --- Filter CurrentStock to only valid FK references ---
        valid_orders = set(buyer_order_df["buyerorderno"])
        current_stock_df = current_stock_df[current_stock_df["ocnum"].isin(valid_orders)]

        # --- Create schema ---
        with self.engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys = ON;"))
            conn.execute(text("DROP TABLE IF EXISTS current_stock;"))
            conn.execute(text("DROP TABLE IF EXISTS buyer_order;"))
            
            conn.execute(text("""
            CREATE TABLE buyer_order (
                buyerorderno TEXT PRIMARY KEY,
                buyername TEXT,
                buyerorderstatus TEXT,
                stylename TEXT,
                stylecode TEXT,
                productgroup TEXT,
                category TEXT,
                subcategory TEXT,
                buyerorderqty REAL,
                buyerorderdate TEXT,
                buyerordervalue REAL,
                currency TEXT,
                buyerdeliverydate TEXT,
                buyershippedqty REAL,
                buyershippedvalue REAL,
                buyershippedinvoiceno TEXT
            );
            """))
            
            conn.execute(text("""
            CREATE TABLE current_stock (
                ocnum TEXT,
                sitename TEXT,
                category TEXT,
                productgroup TEXT,
                productsubcatcode TEXT,
                articlename TEXT,
                articlecode TEXT,
                colorname TEXT,
                colorcode TEXT,
                sizename TEXT,
                sizecode TEXT,
                shade TEXT,
                count TEXT,
                content TEXT,
                construction TEXT,
                stocktype TEXT,
                quality TEXT,
                posupplierref TEXT,
                locationcode TEXT,
                indentno TEXT,
                stylename TEXT,
                stylecode TEXT,
                buyerstyleref TEXT,
                merchandiser TEXT,
                manager TEXT,
                buyer TEXT,
                supplier TEXT,
                ocstatus TEXT,
                contractno TEXT,
                contractdate TEXT,
                contractamount REAL,
                sourcebuyer TEXT,
                pcddate TEXT,
                garmentdeliverydate TEXT,
                grndetails TEXT,
                grnno TEXT,
                grncreatedby TEXT,
                grndate TEXT,
                ageing INTEGER,
                supplierpono TEXT,
                uom TEXT,
                quantity REAL,
                pendingtodispatch_underqc REAL,
                rate REAL,
                value REAL,
                FOREIGN KEY (ocnum) REFERENCES buyer_order(buyerorderno)
            );
            """))

        # --- Insert data ---
        buyer_order_df.to_sql("buyer_order", self.engine, if_exists="append", index=False)
        current_stock_df.to_sql("current_stock", self.engine, if_exists="append", index=False)

        print("==============================")
        print("BuyerOrder & CurrentStock tables created with PK/FK constraints.")

    def _validate_db(self):
        """Validate created SQL tables."""
        insp = inspect(self.engine)
        table_names = insp.get_table_names()
        print("==============================")
        print("Available tables in SQL DB:", table_names)
        print("==============================")

    def run_pipeline(self):
        """Run the import pipeline."""
        self._prepare_db()
        self._validate_db()
