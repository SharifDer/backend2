import asyncio
import json
import os
import sys
# Add parent directory (saudi_census) to path to import saudi_census_common
current_script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_script_dir, ".."))
sys.path.append(parent_dir)
from backend_common.common_config import CONF
from google.oauth2 import service_account
from firebase_admin import firestore_async
import asyncpg  # For PostgreSQL operations
from backend_common.dtypes.auth_dtypes import UserProfileSettings
from typing import Dict, Any
from rich import print_json

# Please double check the updated user profile **settings** data before writing it to firestore
WRITE_TO_FIRESTORE = False

# Initialize Firestore client
google_auth_creds = service_account.Credentials.from_service_account_file(
    "secrets/secret_dev-s-locator-SA.json"
)
db = firestore_async.AsyncClient(credentials=google_auth_creds)


async def update_all_user_profiles():
    try:
        users_ref = db.collection("all_user_profiles")
        users_docs = await users_ref.get()

        temp_settings = UserProfileSettings(user_id="temp")
        default_settings = {"settings": temp_settings.model_dump(exclude={"user_id"})}
        print("\nDefault Settings Template:")
        print_json(json.dumps(default_settings))

        for user in users_docs:
            try:
                user_id = user.id
                user_ref = db.collection("all_user_profiles").document(user_id)

                profile = await user_ref.get()
                if not profile.exists:
                    continue

                print(f"{'='*80}")
                print(f"User: {user_id}")
                print(f"{'='*80}")

                current_data = profile.to_dict()

                print("Current Profile Data:")
                print_json(json.dumps(current_data))

                updated_data = current_data.copy()
                if "settings" not in updated_data:
                    updated_data["settings"] = {}

                for key, value in default_settings["settings"].items():
                    if key not in updated_data["settings"]:
                        updated_data["settings"][key] = value

                print("\nUpdated Profile Data:")
                print_json(json.dumps(updated_data))
                print()

                if WRITE_TO_FIRESTORE:
                    await user_ref.set(updated_data, merge=True)

            except Exception as e:
                print(f"Error updating user {user_id}: {str(e)}")
                continue

    except Exception as e:
        print(f"Error listing users: {str(e)}")
        raise


async def clear_user_data(user_id: str):
    """
    Clears the datasets, layers, and catalogs for a specific user.
    """
    user_ref = db.collection("all_user_profiles").document(user_id)
    user_doc = await user_ref.get()

    if user_doc.exists:
        user_data = user_doc.to_dict()
        if "prdcer" in user_data:
            # Clear the datasets, layers, and catalogs
            user_data["prdcer"] = {
                "prdcer_dataset": {},
                "prdcer_lyrs": {},
                "prdcer_ctlgs": {},
                "draft_ctlgs": {},
            }
            await user_ref.update({"prdcer": user_data["prdcer"]})
            print(f"Cleared data for user: {user_id}")
        else:
            print(f"No 'prdcer' data found for user: {user_id}")
    else:
        print(f"User profile not found for user: {user_id}")


async def clear_all_users_data():
    """
    Clears the datasets, layers, and catalogs for all users.
    """
    users_ref = db.collection("all_user_profiles")
    users_docs = await users_ref.get()

    for user_doc in users_docs:
        user_id = user_doc.id
        await clear_user_data(user_id)


async def clear_fields_in_document(
    collection_name: str, document_id: str, fields_to_clear: list
):
    """
    Clears specific fields in a Firestore document.
    """
    doc_ref = db.collection(collection_name).document(document_id)
    doc = await doc_ref.get()

    if doc.exists:
        update_data = {
            field: {} for field in fields_to_clear
        }  # Set fields to empty dictionaries
        await doc_ref.update(update_data)
        print(
            f"Cleared fields {fields_to_clear} in document {document_id} in collection {collection_name}"
        )
    else:
        print(f"Document {document_id} not found in collection {collection_name}")


async def clear_dataset_and_user_matching():
    """
    Deletes all data inside dataset_matching and user_matching documents
    in the layer_matching collection.
    """
    # Clear the dataset_matching document
    await db.collection("layer_matchings").document("dataset_matching").set({})
    print("Cleared all data in dataset_matching document")

    # Clear the user_matching document
    await db.collection("layer_matchings").document("user_matching").set({})
    print("Cleared all data in user_matching document")


async def truncate_postgresql_table():
    """
    Truncates the `schema_marketplace.datasets` table in PostgreSQL.
    """
    with open("secrets/postgres_db.json", "r") as file:
        config = json.load(file)
        db_url = config["DATABASE_URL"]
    
    connection = await asyncpg.connect(db_url)

    try:
        await connection.execute('TRUNCATE TABLE "schema_marketplace"."datasets"')
        print("Truncated table schema_marketplace.datasets in PostgreSQL")
    except Exception as e:
        print(f"Error truncating PostgreSQL table: {e}")
    finally:
        await connection.close()


async def main():
    # # Clear all user profiles' datasets, layers, and catalogs
    await clear_all_users_data()

    # # Clear fields in dataset_matching and user_matching documents
    await clear_dataset_and_user_matching()

    # # Truncate the PostgreSQL table
    # await truncate_postgresql_table()

    # Update all user profiles' settings
    # await update_all_user_profiles()


if __name__ == "__main__":
    asyncio.run(main())
