import os
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import bcrypt
import uuid

# Set up BigQuery client and table info
BIGQUERY_PROJECT = os.getenv('BIGQUERY_PROJECT', 'Project_name')
BIGQUERY_DATASET = os.getenv('BIGQUERY_DATASET', 'inventory_dataset')
STOCK_TABLE = os.getenv('STOCK_TABLE', 'product_stock')
TRANSACTION_TABLE = os.getenv('TRANSACTION_TABLE', 'inventory_transactions')
USER_TABLE = os.getenv('users', f'{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.users')

client = bigquery.Client(project=BIGQUERY_PROJECT)

# --- Inventory-related functions ---
def update_product_stock(product_name, color, packing_option, product_grade, quantity_adjustment):
    stock_table_id = f"{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.{STOCK_TABLE}"
    try:
        if quantity_adjustment < 0:
            query_check = f"""
                SELECT current_quantity FROM `{stock_table_id}`
                WHERE product_name = @product_name AND color = @color AND packing_option = @packing_option AND product_grade = @product_grade
            """
            params = [
                bigquery.ScalarQueryParameter("product_name", "STRING", product_name),
                bigquery.ScalarQueryParameter("color", "STRING", color),
                bigquery.ScalarQueryParameter("packing_option", "STRING", packing_option),
                bigquery.ScalarQueryParameter("product_grade", "STRING", product_grade),
            ]
            job_config = bigquery.QueryJobConfig(query_parameters=params)
            rows = list(client.query(query_check, job_config=job_config).result())
            if not rows or rows[0].current_quantity < abs(quantity_adjustment):
                return f"Error: Insufficient stock for {product_name} ({color})."
        
        query = f"""
            MERGE `{stock_table_id}` T
            USING (SELECT @product_name AS product_name, @color AS color, @packing_option AS packing_option, @product_grade AS product_grade) S
            ON T.product_name = S.product_name AND T.color = S.color AND T.packing_option = S.packing_option AND T.product_grade = S.product_grade
            WHEN MATCHED THEN
              UPDATE SET current_quantity = T.current_quantity + @adjustment
            WHEN NOT MATCHED BY TARGET AND @adjustment > 0 THEN
              INSERT (product_name, color, packing_option, product_grade, current_quantity)
              VALUES (S.product_name, S.color, S.packing_option, S.product_grade, @adjustment)
        """
        params = [
            bigquery.ScalarQueryParameter("product_name", "STRING", product_name),
            bigquery.ScalarQueryParameter("color", "STRING", color),
            bigquery.ScalarQueryParameter("packing_option", "STRING", packing_option),
            bigquery.ScalarQueryParameter("product_grade", "STRING", product_grade),
            bigquery.ScalarQueryParameter("adjustment", "INT64", quantity_adjustment),
        ]
        job_config = bigquery.QueryJobConfig(query_parameters=params)
        client.query(query, job_config=job_config).result()
        return None
    except Exception as e:
        return f"An Error Occurred: {e}"

def insert_transaction_record(record: dict):
    transaction_table_id = f"{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.{TRANSACTION_TABLE}"
    try:
        errors = client.insert_rows_json(transaction_table_id, [record])
        if errors:
            return f"Failed to insert transaction log: {errors}"
        return None
    except Exception as e:
        return f"An Error Occurred: {e}"

def get_all_product_stock():
    stock_table_id = f"{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.{STOCK_TABLE}"
    query = f"SELECT * FROM `{stock_table_id}`"
    return client.query(query).to_dataframe()
    
def get_inventory_records():
    transaction_table_id = f"{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.{TRANSACTION_TABLE}"
    query = f"SELECT * FROM `{transaction_table_id}`"
    return client.query(query).to_dataframe()

def bulk_insert_transaction_records(records: list):
    transaction_table_id = f"{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.{TRANSACTION_TABLE}"
    try:
        errors = client.insert_rows_json(transaction_table_id, records)
        if errors:
            return f"Failed to insert transaction logs: {errors}"
        return None
    except Exception as e:
        return f"An Error Occurred: {e}"

def bulk_update_product_stock(updates: list):
    stock_table_id = f"{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.{STOCK_TABLE}"
    try:
        using_clause_parts = []
        for u in updates:
            using_clause_parts.append(
                f"('{u['product_name']}', '{u['color']}', '{u['packing_option']}', '{u['product_grade']}', {u['adjustment']})"
            )
        using_clause = ", ".join(using_clause_parts)
        query = f"""
            MERGE `{stock_table_id}` T
            USING (
                SELECT * FROM UNNEST([
                    STRUCT<product_name STRING, color STRING, packing_option STRING, product_grade STRING, adjustment INT64>
                    {using_clause}
                ])
            ) S
            ON T.product_name = S.product_name AND T.color = S.color AND T.packing_option = S.packing_option AND T.product_grade = S.product_grade
            WHEN MATCHED THEN
              UPDATE SET current_quantity = T.current_quantity + S.adjustment
            WHEN NOT MATCHED BY TARGET AND S.adjustment > 0 THEN
              INSERT (product_name, color, packing_option, product_grade, current_quantity)
              VALUES (S.product_name, S.color, S.packing_option, S.product_grade, S.adjustment)
        """
        client.query(query).result()
        return None
    except Exception as e:
        return f"An Error Occurred during bulk update: {e}"

# --- User Authentication Functions ---

def email_exists(email):
    query = f"SELECT COUNT(1) as cnt FROM `{USER_TABLE}` WHERE email=@email"
    job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", email)])
    result = client.query(query, job_config=job_config).result()
    return next(result)["cnt"] > 0

def username_exists(username):
    query = f"SELECT COUNT(1) as cnt FROM `{USER_TABLE}` WHERE username=@username"
    job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("username", "STRING", username)])
    result = client.query(query, job_config=job_config).result()
    return next(result)["cnt"] > 0

def create_user(username, email, password):
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user_id = str(uuid.uuid4())
    ## FIXED: Added `allowed_transaction` to the INSERT statement with a default of 'all'
    query = f"""
    INSERT INTO `{USER_TABLE}` (user_id, username, email, password_hash, created_at, user_role, allowed_transaction)
    VALUES (@user_id, @username, @email, @password_hash, CURRENT_DATETIME(), 'user', 'all')
    """
    query_params = [
        bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
        bigquery.ScalarQueryParameter("username", "STRING", username),
        bigquery.ScalarQueryParameter("email", "STRING", email),
        bigquery.ScalarQueryParameter("password_hash", "STRING", password_hash)
    ]
    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    client.query(query, job_config=job_config).result()

def authenticate(email, password):
    ## FIXED: Added `allowed_transaction` to the SELECT statement
    query = f"SELECT user_id, username, password_hash, user_role, allowed_transaction FROM `{USER_TABLE}` WHERE email=@email"
    job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", email)])
    results = list(client.query(query, job_config=job_config).result())
    if not results:
        return False, None, None, None, None
    user = results[0]
    if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return True, user["username"], user["user_id"], user["user_role"], user["allowed_transaction"]
    return False, None, None, None, None

def get_all_users():
    """Fetches all users for the admin panel."""
    ## FIXED: Added `allowed_transaction` to the SELECT statement
    query = f"SELECT user_id, username, email, user_role, allowed_transaction FROM `{USER_TABLE}`"
    return client.query(query).to_dataframe()

def update_user_role(user_id, new_role):
    """Updates the role for a specific user."""
    query = f"UPDATE `{USER_TABLE}` SET user_role=@role WHERE user_id=@user_id"
    query_params = [
        bigquery.ScalarQueryParameter("role", "STRING", new_role),
        bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
    ]
    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    client.query(query, job_config=job_config).result()

def update_user_restriction(user_id, restriction_list: list):
    """Updates the allowed_transaction for a specific user."""
    restriction_value = ','.join(restriction_list) if restriction_list else 'all'
    
    query = f"UPDATE `{USER_TABLE}` SET allowed_transaction=@restriction WHERE user_id=@user_id"
    query_params = [
        bigquery.ScalarQueryParameter("restriction", "STRING", restriction_value),
        bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
    ]
    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    client.query(query, job_config=job_config).result()

def get_user_by_email(email):
    query = f"SELECT user_id FROM `{USER_TABLE}` WHERE email=@email"
    job_config = bigquery.QueryJobConfig(query_parameters=[bigquery.ScalarQueryParameter("email", "STRING", email)])
    results = list(client.query(query, job_config=job_config).result())
    return results[0] if results else None

def update_user_password(email, new_password):
    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    query = f"UPDATE `{USER_TABLE}` SET password_hash=@password_hash WHERE email=@email"
    query_params = [
        bigquery.ScalarQueryParameter("password_hash", "STRING", password_hash),
        bigquery.ScalarQueryParameter("email", "STRING", email)
    ]
    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    client.query(query, job_config=job_config).result()

def delete_user(user_id):
    """Deletes a user from the users table."""
    query = f"DELETE FROM `{USER_TABLE}` WHERE user_id=@user_id"
    query_params = [bigquery.ScalarQueryParameter("user_id", "STRING", user_id)]
    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    client.query(query, job_config=job_config).result()
