import csv
import json
import os

# --- IMPORT CORE API AND MODULAR ARCHITECTURES ---
from AgenticFlowNvidiaAPI import llm
from TargetDataSchema import ZillowDataPayload
from ScrapingZillowStatic import fetch_zillow_raw_html
# Import your newly isolated Google Sheets function module
from GoogleSheetsEngine import upload_to_google_sheet_pipeline

target_url = "https://www.zillow.com/pasadena-md/houses/under-500000/"
output_filename = "pasadena_listings.csv"
spreadsheet_title = "Pasadena MD Single-Family Homes Under 500k"

if __name__ == "__main__":
    print("[Main Execution] Starting Agentic RPA Pipeline...")

    # 1. Harvest raw dynamic HTML snippets across pages using the browser controller
    raw_bundle_string = fetch_zillow_raw_html.func(target_url)

    # --- CRASH GUARD ---
    if isinstance(raw_bundle_string, str) and raw_bundle_string.startswith("Could not connect"):
        print(f"\n[CRITICAL ERROR] Browser Connection Failed:\n{raw_bundle_string}")
        raw_properties_list = []
    else:
        try:
            raw_properties_list = json.loads(raw_bundle_string)
        except Exception as parse_err:
            print(f"[Error] Failed to read scraper output: {parse_err}")
            print(f"[Raw Output Snippet]: {str(raw_bundle_string)[:500]}")
            raw_properties_list = []

    all_valid_listings = []

    # 2. Iterate and chunk data bundles through the Nvidia Structured LLM Interface
    if raw_properties_list:
        structured_llm = llm.with_structured_output(ZillowDataPayload)
        batch_size = 5
        print(f"[Main Execution] Splitting {len(raw_properties_list)} properties into batches of {batch_size}...")

        for i in range(0, len(raw_properties_list), batch_size):
            chunk = raw_properties_list[i:i + batch_size]
            print(f"\n--- Processing Batch {i // batch_size + 1} ({len(chunk)} cards) ---")

            chunk_prompt = (
                "You are an expert RPA data parsing agent and a strict data validator.\n"
                "Analyze the following raw Zillow HTML card snippets and extract all single-family house listings.\n\n"
                "CRITICAL FILTRATION RULES:\n"
                "1. PROPERTY TYPE: Extract ONLY single-family detached homes. Completely ignore townhouses, condos, apartments, or land.\n"
                "2. MAXIMUM PRICE CAP: Only extract listings where the price is strictly LESS THAN $500,000.\n"
                f"Drop any listings that fail these rules.\n\n"
                f"Data to parse:\n{json.dumps(chunk)}"
            )

            try:
                result = structured_llm.invoke(chunk_prompt)
                if result and result.listings:
                    print(f"[LLM Batch Success] Extracted {len(result.listings)} valid homes.")
                    for listing in result.listings:
                        all_valid_listings.append(listing.model_dump())
                else:
                    print("[LLM Batch Notice] No listings matched the filtering criteria in this batch.")
            except Exception as batch_err:
                print(f"[Warning] LLM failed to parse batch {i // batch_size + 1}: {batch_err}")

        # Print data console diagnostics log
        print("\n================ LOCAL COMPILATION DEPLOYED ================")
        print(json.dumps({"listings": all_valid_listings}, indent=2))

        # 3. Write data metrics file down to local system CSV storage layout
        if all_valid_listings:
            print(f"\n[Export Engine] Found {len(all_valid_listings)} valid listings. Saving locally...")
            headers = ["address", "price", "beds", "baths", "sqft", "url"]
            output_path = os.path.join(os.getcwd(), output_filename)

            try:
                with open(output_path, mode="w", newline="", encoding="utf-8") as csv_file:
                    writer = csv.DictWriter(csv_file, fieldnames=headers)
                    writer.writeheader()
                    for listing in all_valid_listings:
                        writer.writerow(listing)
                print(f"[Success] Database beautifully written locally to: {output_path}")
            except Exception as file_err:
                print(f"[Error] Failed to write local data layer layout: {file_err}")

            # 4. EXECUTE MODULAR CLOUD SYNCHRONIZATION VIA IMPORTED ENGINE
            print("\n[Main Execution] Launching Google Sheets export module...")
            upload_to_google_sheet_pipeline(all_valid_listings, spreadsheet_title)

        else:
            print("[Export Engine] Skipped writing tasks: No matching list arrays generated.")
    else:
        print("[Error] No property blocks were extracted from the browser environment.")