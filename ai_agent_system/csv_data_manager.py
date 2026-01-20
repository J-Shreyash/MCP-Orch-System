"""
CSV Data Manager - COMPLETE PRODUCTION VERSION (BUG FIXED)
Handles CSV upload, validation, and storage via Database MCP
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav

CRITICAL FIXES ADDED:
✅ SQL injection protection (sanitized table/column names)
✅ Proper type inference (handles all pandas types correctly)
✅ Input validation (size, rows, columns)
✅ Batch insertion (1000 rows at a time)
✅ NaN/None handling (converts to SQL NULL)
✅ Error recovery and detailed logging
✅ FIXED: is_integer() bug that crashes on certain float types
✅ Preserved ALL original features and functionality
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import re
import logging
from datetime import datetime
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


class CSVDataManager:
    """
    Manages CSV data operations via Database MCP
    COMPLETE VERSION - All original features + critical fixes
    """
    
    def __init__(self, db_client):
        """
        Initialize CSV Data Manager
        
        Args:
            db_client: DatabaseMCPClient instance
        """
        self.db = db_client
        
        # Configuration - ORIGINAL FEATURE
        self.max_file_size_mb = 100
        self.max_rows = 1000000
        self.max_columns = 100
        self.batch_size = 1000
        
        # Statistics tracking - ORIGINAL FEATURE
        self.upload_count = 0
        self.total_rows_uploaded = 0
        self.total_tables_created = 0
        self.errors_count = 0
        
        print("📊 CSV Data Manager initialized (PRODUCTION VERSION)")
        print(f"   Max file size: {self.max_file_size_mb} MB")
        print(f"   Max rows: {self.max_rows:,}")
        print(f"   Max columns: {self.max_columns}")
        print(f"   Batch size: {self.batch_size}")
        
        logger.info("CSV Data Manager initialized")
    
    def upload_csv(self, df: pd.DataFrame, table_name: str, 
                   replace_if_exists: bool = True,
                   show_progress: bool = True) -> Dict:
        """
        Upload CSV to MySQL database via MCP
        COMPLETE VERSION - All original features + critical fixes
        
        Args:
            df: Pandas DataFrame to upload
            table_name: Name for the table
            replace_if_exists: Whether to replace existing table (default: True)
            show_progress: Whether to show progress messages (default: True)
            
        Returns:
            {
                "success": bool,
                "table_name": str,
                "rows_inserted": int,
                "columns": list,
                "error": str (if failed),
                "metadata": dict
            }
        """
        start_time = time.time()
        
        try:
            if show_progress:
                print(f"\n{'='*80}")
                print(f"📤 CSV Upload Starting")
                print(f"   Table: {table_name}")
                print(f"   Rows: {len(df):,}")
                print(f"   Columns: {len(df.columns)}")
                print(f"{'='*80}\n")
            
            logger.info(f"Starting CSV upload: {table_name} ({len(df)} rows, {len(df.columns)} cols)")
            
            # Step 1: Validate and sanitize table name
            if show_progress:
                print("🔍 Step 1: Validating table name...")
            
            original_table_name = table_name
            table_name = self._sanitize_table_name(table_name)
            
            if not table_name:
                error_msg = "Invalid table name. Use only letters, numbers, and underscores."
                logger.error(error_msg)
                self.errors_count += 1
                return {
                    "success": False,
                    "error": error_msg
                }
            
            if table_name != original_table_name:
                if show_progress:
                    print(f"   ⚠️ Table name sanitized: '{original_table_name}' → '{table_name}'")
                logger.info(f"Table name sanitized: {original_table_name} → {table_name}")
            
            if show_progress:
                print(f"   ✅ Table name validated: '{table_name}'")
            
            # Step 2: Validate DataFrame
            if show_progress:
                print("\n🔍 Step 2: Validating DataFrame...")
            
            validation_result = self._validate_dataframe(df)
            
            if not validation_result["valid"]:
                error_msg = validation_result["error"]
                logger.error(f"DataFrame validation failed: {error_msg}")
                self.errors_count += 1
                return {
                    "success": False,
                    "error": error_msg
                }
            
            if show_progress:
                print("   ✅ DataFrame validation passed")
            
            # Step 3: Sanitize column names
            if show_progress:
                print("\n🔧 Step 3: Sanitizing column names...")
            
            df_clean = df.copy()
            original_columns = list(df.columns)
            sanitized_columns = [self._sanitize_column_name(col) for col in df.columns]
            df_clean.columns = sanitized_columns
            
            # Show column name changes
            if show_progress:
                changes = [(orig, san) for orig, san in zip(original_columns, sanitized_columns) if orig != san]
                if changes:
                    print(f"   ⚠️ {len(changes)} column(s) renamed:")
                    for orig, san in changes[:5]:  # Show first 5
                        print(f"      '{orig}' → '{san}'")
                    if len(changes) > 5:
                        print(f"      ... and {len(changes) - 5} more")
                else:
                    print("   ✅ All column names valid (no changes needed)")
            
            logger.info(f"Columns sanitized: {len(changes) if show_progress and changes else 0} changed")
            
            # Step 4: Infer column types
            if show_progress:
                print("\n🔬 Step 4: Inferring SQL column types...")
            
            column_defs = self._infer_column_types(df_clean)
            
            if show_progress:
                print(f"   ✅ Column types inferred:")
                for col_def in column_defs[:5]:  # Show first 5
                    nullable = "NULL" if col_def.get('nullable') else "NOT NULL"
                    print(f"      {col_def['name']}: {col_def['type']} {nullable}")
                if len(column_defs) > 5:
                    print(f"      ... and {len(column_defs) - 5} more columns")
            
            logger.info(f"Column types inferred for {len(column_defs)} columns")
            
            # Step 5: Check if table exists (if replace_if_exists is True)
            if replace_if_exists:
                if show_progress:
                    print(f"\n🗑️ Step 5: Checking for existing table...")
                
                # Drop table if exists
                drop_result = self._drop_table_if_exists(table_name)
                if drop_result["dropped"]:
                    if show_progress:
                        print(f"   ✅ Existing table '{table_name}' dropped")
                    logger.info(f"Existing table dropped: {table_name}")
                else:
                    if show_progress:
                        print(f"   ℹ️ Table '{table_name}' does not exist (will create new)")
            
            # Step 6: Create table
            if show_progress:
                print(f"\n🔨 Step 6: Creating table '{table_name}'...")
            
            create_result = self._create_table(table_name, column_defs)
            
            if not create_result["success"]:
                error_msg = f"Table creation failed: {create_result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                self.errors_count += 1
                return {
                    "success": False,
                    "error": error_msg
                }
            
            if show_progress:
                print(f"   ✅ Table '{table_name}' created successfully")
            
            logger.info(f"Table created: {table_name}")
            self.total_tables_created += 1
            
            # Step 7: Insert data in batches
            if show_progress:
                print(f"\n📥 Step 7: Inserting data (batch size: {self.batch_size})...")
            
            insert_result = self._insert_data(table_name, df_clean, column_defs, show_progress)
            
            if not insert_result["success"]:
                error_msg = f"Data insertion failed: {insert_result.get('error', 'Unknown error')}"
                logger.error(error_msg)
                self.errors_count += 1
                return {
                    "success": False,
                    "error": error_msg,
                    "rows_inserted": insert_result.get("rows_inserted", 0)
                }
            
            rows_inserted = insert_result["rows_inserted"]
            
            # Update statistics
            self.upload_count += 1
            self.total_rows_uploaded += rows_inserted
            
            # Calculate upload time
            elapsed_time = time.time() - start_time
            
            if show_progress:
                print(f"\n{'='*80}")
                print(f"🎉 CSV Upload Complete!")
                print(f"   Table: {table_name}")
                print(f"   Rows inserted: {rows_inserted:,} / {len(df):,}")
                print(f"   Columns: {len(column_defs)}")
                print(f"   Time taken: {elapsed_time:.2f} seconds")
                print(f"   Speed: {rows_inserted / elapsed_time:.0f} rows/sec")
                print(f"{'='*80}\n")
            
            logger.info(f"CSV upload complete: {table_name} ({rows_inserted} rows in {elapsed_time:.2f}s)")
            
            return {
                "success": True,
                "table_name": table_name,
                "rows_inserted": rows_inserted,
                "columns": [col["name"] for col in column_defs],
                "metadata": {
                    "original_table_name": original_table_name,
                    "original_columns": original_columns,
                    "sanitized_columns": sanitized_columns,
                    "column_definitions": column_defs,
                    "upload_time_seconds": elapsed_time,
                    "rows_per_second": rows_inserted / elapsed_time if elapsed_time > 0 else 0,
                    "total_rows": len(df),
                    "batch_size": self.batch_size,
                    "timestamp": datetime.now().isoformat()
                }
            }
        
        except Exception as e:
            error_msg = f"CSV upload failed: {str(e)}"
            print(f"\n❌ {error_msg}")
            logger.error(error_msg, exc_info=True)
            self.errors_count += 1
            
            return {
                "success": False,
                "error": error_msg
            }
    
    def _sanitize_table_name(self, name: str) -> Optional[str]:
        """
        CRITICAL FIX: Sanitize table name to prevent SQL injection
        
        Args:
            name: Raw table name
            
        Returns:
            Sanitized name or None if invalid
        """
        if not name:
            return None
        
        # Remove special characters, keep only alphanumeric and underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
        
        # Ensure starts with letter
        if not sanitized or not sanitized[0].isalpha():
            sanitized = 't_' + sanitized if sanitized else None
        
        # Limit length to 64 characters (MySQL limit)
        if sanitized:
            sanitized = sanitized[:64]
        
        # Validate final result
        if sanitized and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]{0,63}$', sanitized):
            return sanitized.lower()
        
        return None
    
    def _sanitize_column_name(self, name: str) -> str:
        """
        CRITICAL FIX: Sanitize column name to prevent SQL injection
        
        Args:
            name: Raw column name
            
        Returns:
            Sanitized column name
        """
        if not name:
            return "col_unnamed"
        
        # Replace spaces and special chars with underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', str(name))
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Ensure starts with letter
        if not sanitized or not sanitized[0].isalpha():
            sanitized = 'col_' + sanitized if sanitized else 'col_unnamed'
        
        # Limit length to 64 characters
        sanitized = sanitized[:64]
        
        return sanitized.lower()
    
    def _validate_dataframe(self, df: pd.DataFrame) -> Dict:
        """
        CRITICAL FIX: Validate DataFrame before upload
        
        Args:
            df: DataFrame to validate
            
        Returns:
            {"valid": bool, "error": str}
        """
        # Check if empty
        if df.empty or len(df) == 0:
            return {
                "valid": False,
                "error": "DataFrame is empty (no rows)"
            }
        
        # Check column count
        if len(df.columns) == 0:
            return {
                "valid": False,
                "error": "DataFrame has no columns"
            }
        
        if len(df.columns) > self.max_columns:
            return {
                "valid": False,
                "error": f"Too many columns ({len(df.columns)}). Maximum allowed: {self.max_columns}"
            }
        
        # Check row count
        if len(df) > self.max_rows:
            return {
                "valid": False,
                "error": f"Too many rows ({len(df):,}). Maximum allowed: {self.max_rows:,}"
            }
        
        # Check for duplicate column names
        if len(df.columns) != len(set(df.columns)):
            duplicates = [col for col in df.columns if list(df.columns).count(col) > 1]
            return {
                "valid": False,
                "error": f"Duplicate column names found: {set(duplicates)}"
            }
        
        # Check memory size (rough estimate)
        memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        if memory_mb > self.max_file_size_mb:
            return {
                "valid": False,
                "error": f"DataFrame too large ({memory_mb:.2f} MB). Maximum: {self.max_file_size_mb} MB"
            }
        
        return {"valid": True}
    
    def _infer_column_types(self, df: pd.DataFrame) -> List[Dict]:
        """
        CRITICAL FIX: Properly infer SQL types from pandas types
        🔧 BUG FIX: Fixed is_integer() crash for certain float types
        
        Args:
            df: DataFrame with sanitized column names
            
        Returns:
            List of column definitions with types
        """
        column_defs = []
        
        for col in df.columns:
            dtype = df[col].dtype
            sql_type = "VARCHAR(255)"  # Default fallback
            
            # Check for datetime types
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                sql_type = "DATETIME"
            
            # Check for date types
            elif pd.api.types.is_datetime64_ns_dtype(df[col]):
                sql_type = "DATETIME"
            
            # Check for integer types
            elif pd.api.types.is_integer_dtype(df[col]):
                try:
                    max_val = abs(df[col].max()) if len(df[col]) > 0 and not df[col].isnull().all() else 0
                    min_val = abs(df[col].min()) if len(df[col]) > 0 and not df[col].isnull().all() else 0
                    range_val = max(max_val, min_val)
                    
                    if range_val < 128:
                        sql_type = "TINYINT"
                    elif range_val < 32767:
                        sql_type = "SMALLINT"
                    elif range_val < 8388607:
                        sql_type = "MEDIUMINT"
                    elif range_val < 2147483647:
                        sql_type = "INT"
                    else:
                        sql_type = "BIGINT"
                except:
                    sql_type = "INT"  # Safe default
            
            # Check for float types
            elif pd.api.types.is_float_dtype(df[col]):
                # 🔧 BUG FIX: Safe check for integer-valued floats
                try:
                    # Drop NaN values first
                    non_null_values = df[col].dropna()
                    
                    if len(non_null_values) > 0:
                        # Check if all non-null values are integers
                        # Use modulo instead of is_integer() to avoid compatibility issues
                        all_integers = (non_null_values % 1 == 0).all()
                        
                        if all_integers:
                            sql_type = "INT"
                        else:
                            sql_type = "DOUBLE"
                    else:
                        sql_type = "DOUBLE"
                except:
                    # If any error, default to DOUBLE
                    sql_type = "DOUBLE"
            
            # Check for boolean types
            elif pd.api.types.is_bool_dtype(df[col]):
                sql_type = "BOOLEAN"
            
            # String/object type - determine appropriate length
            elif pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
                try:
                    if len(df[col]) > 0:
                        # Calculate max length of string values
                        max_length = df[col].astype(str).str.len().max()
                        
                        if pd.isna(max_length) or max_length == 0:
                            sql_type = "VARCHAR(255)"
                        elif max_length <= 50:
                            sql_type = "VARCHAR(50)"
                        elif max_length <= 100:
                            sql_type = "VARCHAR(100)"
                        elif max_length <= 255:
                            sql_type = "VARCHAR(255)"
                        elif max_length <= 500:
                            sql_type = "VARCHAR(500)"
                        elif max_length <= 1000:
                            sql_type = "VARCHAR(1000)"
                        elif max_length <= 5000:
                            sql_type = "TEXT"
                        else:
                            sql_type = "LONGTEXT"
                    else:
                        sql_type = "VARCHAR(255)"
                except:
                    sql_type = "VARCHAR(255)"
            
            # Categorical types
            elif hasattr(df[col], 'cat'):
                try:
                    # Pandas categorical
                    unique_count = df[col].nunique()
                    if unique_count <= 10:
                        max_cat_length = max([len(str(cat)) for cat in df[col].cat.categories])
                        sql_type = f"VARCHAR({min(max_cat_length + 10, 255)})"
                    else:
                        sql_type = "VARCHAR(255)"
                except:
                    sql_type = "VARCHAR(255)"
            
            # Check if column has null values
            try:
                nullable = df[col].isnull().any()
            except:
                nullable = True  # Safe default
            
            column_defs.append({
                "name": col,
                "type": sql_type,
                "nullable": nullable,
                "original_dtype": str(dtype)
            })
        
        return column_defs
    
    def _drop_table_if_exists(self, table_name: str) -> Dict:
        """
        Drop table if it exists
        ORIGINAL FEATURE - Preserved with safety checks
        
        Args:
            table_name: Sanitized table name
            
        Returns:
            {"success": bool, "dropped": bool, "error": str}
        """
        try:
            # CRITICAL FIX: Use backticks around table name
            drop_sql = f"DROP TABLE IF EXISTS `{table_name}`"
            
            result = self.db.execute_sql(drop_sql, fetch=False)
            
            if result.get("success"):
                return {
                    "success": True,
                    "dropped": True
                }
            else:
                return {
                    "success": False,
                    "dropped": False,
                    "error": result.get("error", "Unknown error")
                }
        
        except Exception as e:
            logger.error(f"Drop table error: {e}")
            return {
                "success": False,
                "dropped": False,
                "error": str(e)
            }
    
    def _create_table(self, table_name: str, column_defs: List[Dict]) -> Dict:
        """
        Create table via Database MCP
        CRITICAL FIX: Uses backticks and proper NULL handling
        
        Args:
            table_name: Sanitized table name
            column_defs: List of column definitions
            
        Returns:
            {"success": bool, "error": str}
        """
        try:
            # Build column definitions
            col_sql = []
            for col in column_defs:
                null_clause = "" if col.get("nullable", True) else "NOT NULL"
                col_sql.append(f"`{col['name']}` {col['type']} {null_clause}")
            
            # Add auto-increment ID as primary key
            col_sql.insert(0, "id INT AUTO_INCREMENT PRIMARY KEY")
            
            # CRITICAL FIX: Use backticks around table name
            create_sql = f"""
                CREATE TABLE IF NOT EXISTS `{table_name}` (
                    {', '.join(col_sql)}
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            logger.debug(f"Create table SQL: {create_sql[:200]}...")
            
            # Execute via MCP
            result = self.db.execute_sql(create_sql, fetch=False)
            
            if result.get("success"):
                return {"success": True}
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error")
                }
        
        except Exception as e:
            logger.error(f"Create table error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _insert_data(self, table_name: str, df: pd.DataFrame, 
                    column_defs: List[Dict], show_progress: bool = True) -> Dict:
        """
        Insert data in batches via Database MCP
        CRITICAL FIX: Handles NaN/None values properly, batch processing
        
        Args:
            table_name: Sanitized table name
            df: DataFrame with sanitized columns
            column_defs: Column definitions
            show_progress: Whether to show progress
            
        Returns:
            {"success": bool, "rows_inserted": int, "error": str}
        """
        try:
            # Prepare column names
            col_names = [col['name'] for col in column_defs]
            
            # Build INSERT statement with placeholders
            placeholders = ', '.join(['%s'] * len(col_names))
            
            # CRITICAL FIX: Use backticks around identifiers
            insert_sql = f"""
                INSERT INTO `{table_name}` ({', '.join(f'`{c}`' for c in col_names)})
                VALUES ({placeholders})
            """
            
            logger.debug(f"Insert SQL: {insert_sql}")
            
            # Convert DataFrame to list of tuples
            # CRITICAL FIX: Handle NaN/None values properly
            values = []
            for idx, row in df.iterrows():
                row_values = []
                for col in col_names:
                    val = row[col]
                    
                    # CRITICAL FIX: Convert NaN/NaT to None for SQL NULL
                    if pd.isna(val):
                        row_values.append(None)
                    # Handle datetime
                    elif isinstance(val, (pd.Timestamp, datetime)):
                        row_values.append(val.strftime('%Y-%m-%d %H:%M:%S'))
                    # Handle numpy types
                    elif isinstance(val, (np.integer, np.floating)):
                        row_values.append(val.item())
                    # Handle boolean
                    elif isinstance(val, (bool, np.bool_)):
                        row_values.append(int(val))
                    else:
                        row_values.append(val)
                
                values.append(tuple(row_values))
            
            # CRITICAL FIX: Batch insert (self.batch_size rows at a time)
            total_inserted = 0
            total_batches = (len(values) + self.batch_size - 1) // self.batch_size
            
            for batch_num, i in enumerate(range(0, len(values), self.batch_size), 1):
                batch = values[i:i + self.batch_size]
                
                if show_progress:
                    progress = (batch_num / total_batches) * 100
                    print(f"   Batch {batch_num}/{total_batches} ({len(batch)} rows) - {progress:.1f}% complete", end='\r')
                
                logger.debug(f"Inserting batch {batch_num}/{total_batches} ({len(batch)} rows)")
                
                # Execute batch via MCP
                result = self.db.execute_sql(
                    insert_sql,
                    params=batch,
                    fetch=False,
                    many=True
                )
                
                if result.get("success"):
                    total_inserted += len(batch)
                else:
                    error = result.get("error", "Unknown error")
                    logger.error(f"Batch insert failed: {error}")
                    
                    if show_progress:
                        print()  # New line after progress
                    
                    return {
                        "success": False,
                        "rows_inserted": total_inserted,
                        "error": f"Batch {batch_num} failed: {error}"
                    }
            
            if show_progress:
                print()  # New line after progress
                print(f"   ✅ All {total_batches} batches inserted successfully ({total_inserted:,} rows)")
            
            logger.info(f"Data insertion complete: {total_inserted} rows in {total_batches} batches")
            
            return {
                "success": True,
                "rows_inserted": total_inserted
            }
        
        except Exception as e:
            error_msg = f"Data insertion error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            if show_progress:
                print(f"\n   ❌ {error_msg}")
            
            return {
                "success": False,
                "rows_inserted": 0,
                "error": str(e)
            }
    
    def get_table_info(self, table_name: str) -> Optional[Dict]:
        """
        Get table metadata
        ORIGINAL FEATURE - Preserved
        
        Args:
            table_name: Table name
            
        Returns:
            Table information or None
        """
        try:
            # Sanitize table name
            table_name = self._sanitize_table_name(table_name)
            if not table_name:
                return None
            
            logger.info(f"Getting table info: {table_name}")
            
            # Get table structure
            sql = f"DESCRIBE `{table_name}`"
            result = self.db.execute_sql(sql, fetch=True)
            
            if result.get("success"):
                columns = result.get("results", [])
                
                # Get row count
                count_sql = f"SELECT COUNT(*) as row_count FROM `{table_name}`"
                count_result = self.db.execute_sql(count_sql, fetch=True)
                
                row_count = 0
                if count_result.get("success"):
                    rows = count_result.get("results", [])
                    if rows and len(rows) > 0:
                        row_count = rows[0][0] if isinstance(rows[0], (list, tuple)) else rows[0].get('row_count', 0)
                
                return {
                    "table_name": table_name,
                    "columns": columns,
                    "row_count": row_count,
                    "column_count": len(columns)
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Get table info failed: {e}")
            return None
    
    def list_tables(self) -> List[str]:
        """
        List all tables in database
        ORIGINAL FEATURE - Preserved
        
        Returns:
            List of table names
        """
        try:
            logger.info("Listing tables")
            
            sql = "SHOW TABLES"
            result = self.db.execute_sql(sql, fetch=True)
            
            if result.get("success"):
                tables = result.get("results", [])
                # Extract table names from results (handle tuple/list/dict/string formats)
                table_names = []
                for table in tables:
                    if isinstance(table, (list, tuple)) and len(table) > 0:
                        table_names.append(str(table[0]))
                    elif isinstance(table, dict):
                        # MySQL dict format: {'Tables_in_database': 'table_name'}
                        # Get the first value from the dict
                        table_names.append(str(list(table.values())[0]))
                    elif isinstance(table, str):
                        table_names.append(table)
                    else:
                        # Fallback: try to convert to string
                        table_names.append(str(table))
                
                logger.info(f"Found {len(table_names)} tables")
                return table_names
            
            return []
        
        except Exception as e:
            logger.error(f"List tables failed: {e}")
            return []
    
    def delete_table(self, table_name: str) -> Dict:
        """
        Delete a table
        ORIGINAL FEATURE - Preserved with safety checks
        
        Args:
            table_name: Table name to delete
            
        Returns:
            {"success": bool, "message": str, "error": str}
        """
        try:
            # Sanitize table name
            original_name = table_name
            table_name = self._sanitize_table_name(table_name)
            
            if not table_name:
                return {
                    "success": False,
                    "error": "Invalid table name"
                }
            
            logger.info(f"Deleting table: {table_name}")
            
            # Drop table
            drop_sql = f"DROP TABLE IF EXISTS `{table_name}`"
            result = self.db.execute_sql(drop_sql, fetch=False)
            
            if result.get("success"):
                logger.info(f"Table deleted: {table_name}")
                return {
                    "success": True,
                    "message": f"Table '{original_name}' deleted successfully"
                }
            else:
                error = result.get("error", "Unknown error")
                logger.error(f"Delete table failed: {error}")
                return {
                    "success": False,
                    "error": error
                }
        
        except Exception as e:
            error_msg = f"Delete table error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_statistics(self) -> Dict:
        """
        Get CSV manager statistics
        ORIGINAL FEATURE - Preserved
        
        Returns:
            Statistics dictionary
        """
        return {
            "upload_count": self.upload_count,
            "total_rows_uploaded": self.total_rows_uploaded,
            "total_tables_created": self.total_tables_created,
            "errors_count": self.errors_count,
            "average_rows_per_upload": self.total_rows_uploaded / self.upload_count if self.upload_count > 0 else 0,
            "configuration": {
                "max_file_size_mb": self.max_file_size_mb,
                "max_rows": self.max_rows,
                "max_columns": self.max_columns,
                "batch_size": self.batch_size
            }
        }
    
    def reset_statistics(self):
        """
        Reset statistics counters
        ORIGINAL FEATURE - Preserved
        """
        self.upload_count = 0
        self.total_rows_uploaded = 0
        self.total_tables_created = 0
        self.errors_count = 0
        
        logger.info("Statistics reset")
        print("📊 Statistics reset")


# Example usage and test function - ORIGINAL FEATURE
if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 CSV Data Manager - Test Mode")
    print("="*80 + "\n")
    
    # Note: This requires Database MCP client to be initialized
    print("To test CSV Data Manager:")
    print("1. Start Database MCP server: cd mcp_database && uvicorn server:app --port 8003")
    print("2. Initialize DatabaseMCPClient")
    print("3. Create CSVDataManager with the client")
    print("4. Load a CSV file with pandas")
    print("5. Call upload_csv(df, 'table_name')")
    
    print("\nExample code:")
    print("""
from mcp_clients.database_mcp_client import DatabaseMCPClient
from csv_data_manager import CSVDataManager
import pandas as pd

# Initialize
db_client = DatabaseMCPClient()
csv_manager = CSVDataManager(db_client)

# Load CSV
df = pd.read_csv('your_file.csv')

# Upload
result = csv_manager.upload_csv(df, 'my_table')
print(result)
    """)