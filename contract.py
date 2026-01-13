import os
import json
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_CONTRACTS_DIR = os.path.join(BASE_DIR, "generated_contracts")
NODE_SCRIPT = os.path.join(BASE_DIR, "generate_contract.js")

os.makedirs(GENERATED_CONTRACTS_DIR, exist_ok=True)

def generate_contract(fields: dict) -> str:
    """
    Generates contract Word document (.docx) using Node.js script
    Required fields in dict:
    contractor_name, signer_name, relationship_to_vendor,
    address, email, vendor_account, service, amount, due_date, end_date,
    number_of_content, contract_type
    """

    safe_name = fields["contractor_name"].replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    contract_type = fields.get("contract_type", "regular")
    filename = f"contract_{safe_name}_{timestamp}.docx"
    output_path = os.path.join(GENERATED_CONTRACTS_DIR, filename)

    # Prepare data for Node.js script
    data_json = json.dumps(fields)
    
    try:
        # Call Node.js script to generate Word document
        result = subprocess.run(
            ["node", NODE_SCRIPT, data_json, output_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"✅ Contract generated: {result.stdout}")
        return output_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating contract: {e.stderr}")
        raise Exception(f"Contract generation failed: {e.stderr}")
    except FileNotFoundError:
        raise Exception("Node.js is not installed. Please install Node.js to generate contracts.")


# Example local test
if __name__ == "__main__":
    data = {
        "contractor_name": "Bella Kotak",
        "signer_name": "",
        "relationship_to_vendor": "Self",
        "address": "123 Main St, San Francisco, CA 94102",
        "email": "bella@example.com",
        "vendor_account": "Needed",
        "service": "Video Production",
        "amount": "5000",
        "due_date": "December 31, 2025",
        "end_date": "December 31, 2025",
        "number_of_content": "3",
        "contract_type": "regular",  # or "campfire"
        "po": ""
    }

    path = generate_contract(data)
    print(f"✅ Contract generated at: {path}")
