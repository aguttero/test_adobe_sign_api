# src/export.py

import pandas as pd
import logging
from typing import List, Dict, Any

import models
import db

logger = logging.getLogger(__name__)

def export_agreements_to_excel(filename: str = "agreements_export.xlsx") -> None:
    """Fetches agreement data from the database and exports it to an Excel file.

    Args:
        filename: The name of the Excel file to create.
    """
    logger.info(f"Starting export of agreements to {filename}")

    try:
        # Fetch all agreements with related data (user, group, signers, doc_field_contents)
        agreement_data = db.get_all_agreements_for_export()

        if not agreement_data:
            logger.warning("No agreement data found to export.")
            return

        # --- Data Transformation for Export ---
        # Flatten the related data (signers, doc_field_contents) and select required columns
        export_data = []
        for agreement in agreement_data:
            base_data = {
                "Agreement last modification date": agreement.get("modified_date"),
                "Agreement created date": agreement.get("created_date"),
                "Agreement name": agreement.get("name"),
                "Agreement workflow ID": agreement.get("workflow_id"), # Placeholder for workflow name, needs joining
                "Agreement sender": f"{agreement.get('user_first_name', '')} {agreement.get('user_last_name', '')}".strip() if agreement.get('user_first_name') or agreement.get('user_last_name') else agreement.get('user_email'),
                "Agreement group name": agreement.get("group_name"),
            }

            # Process signers (up to 4)
            signers = agreement.get("signers", [])
            for i in range(4):
                if i < len(signers):
                    base_data[f"Agreement signer {i+1} name"] = signers[i].get("signer_full_name")
                    base_data[f"Agreement signer {i+1} role"] = signers[i].get("signer_role")
                else:
                    base_data[f"Agreement signer {i+1} name"] = None
                    base_data[f"Agreement signer {i+1} role"] = None

            # Process document field contents (up to 6)
            doc_fields = agreement.get("doc_field_contents", [])
            for i in range(6):
                if i < len(doc_fields):
                    # The API response structure for doc fields might vary. 
                    # Assuming 'requester_area' holds the content based on previous observations.
                    # If document field content is elsewhere, this needs adjustment.
                    base_data[f"Agreement doc_field_content {i+1}"] = doc_fields[i].get("requester_area") 
                    # Note: 'agreement_subtype' is not directly mapped to a required column, but could be added if needed.
                else:
                    base_data[f"Agreement doc_field_content {i+1}"] = None
            
            export_data.append(base_data)

        df_export = pd.DataFrame(export_data)

        # Ensure the order of columns matches the required output
        # This list is based on the scope of work requirements.
        final_columns = [
            'Agreement last modification date',
            'Agreement created date',
            'Agreement sender',
            'Agreement name',
            'Agreement workflow name', # Placeholder for workflow name, needs joining
            'Agreement signer 1 name', 'Agreement signer 1 role',
            'Agreement signer 2 name', 'Agreement signer 2 role',
            'Agreement signer 3 name', 'Agreement signer 3 role',
            'Agreement signer 4 name', 'Agreement signer 4 role',
            'Agreement doc_field_content 1',
            'Agreement doc_field_content 2',
            'Agreement doc_field_content 3',
            'Agreement doc_field_content 4',
            'Agreement doc_field_content 5',
            'Agreement doc_field_content 6'
        ]
        
        # Reindex the DataFrame to ensure correct column order and inclusion
        # Missing columns will be created with NaN values if they don't exist.
        df_export = df_export.reindex(columns=final_columns)

        # Export to Excel
        df_export.to_excel(filename, index=False)
        logger.info(f"Successfully exported {len(df_export)} agreements to {filename}")

    except Exception as e:
        logger.error(f"Failed to export agreements to Excel: {e}")
        raise DatabaseError(f"Failed to export agreements to Excel: {e}", original_exc=e)

