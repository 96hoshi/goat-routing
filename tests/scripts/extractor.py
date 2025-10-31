import csv
import glob
import json
import os


def process_file(input_filepath, output_csv_path, output_geojson_path):
    """
    Processes a single JSON file to create:
    1. A CSV file from the "all" list.
    2. A GeoJSON file containing both the "one" (origin) and "all" (destinations) points.
    """
    try:
        with open(input_filepath, "r", encoding="utf-8") as f:
            file_content = f.read()
            if not file_content.strip().startswith("{"):
                file_content = "{" + file_content + "}"
            data = json.loads(file_content)
    except FileNotFoundError:
        print(f"Error: The file '{input_filepath}' was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{input_filepath}'.")
        return

    # --- 1. Extract data for and write the CSV file ---
    all_items = data.get("all", [])
    csv_headers = ["stopId", "lat", "long", "duration"]

    with open(output_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()
        for item in all_items:
            place_data = item.get("place", {})
            writer.writerow(
                {
                    "stopId": place_data.get("stopId"),
                    "lat": place_data.get("lat"),
                    "long": place_data.get("lon"),  # Map JSON 'lon' to CSV 'long'
                    "duration": item.get("duration"),
                }
            )
    print(f"✔ Extracted {len(all_items)} records to '{output_csv_path}'.")

    # --- 2. Build the list of features for the GeoJSON file ---
    features = []

    # Add the "one" object as the ORIGIN feature
    one_data = data.get("one")
    if one_data and "lat" in one_data and "lon" in one_data:
        origin_feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [one_data["lon"], one_data["lat"]],
            },
            "properties": {
                "name": one_data.get("name"),
                "departure": one_data.get("departure"),
                "type": "ORIGIN",  # Custom property to identify the origin
            },
        }
        features.append(origin_feature)

    # Add each item from the "all" list as a DESTINATION feature
    for item in all_items:
        place = item.get("place", {})
        if place and "lat" in place and "lon" in place:
            destination_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [place["lon"], place["lat"]],
                },
                "properties": {
                    "stopId": place.get("stopId"),
                    "duration": item.get("duration"),
                    "name": place.get("name"),
                    "type": "DESTINATION",  # Custom property
                },
            }
            features.append(destination_feature)

    # --- 3. Write the complete GeoJSON file ---
    geojson_structure = {"type": "FeatureCollection", "features": features}

    with open(output_geojson_path, "w", encoding="utf-8") as geojson_file:
        json.dump(geojson_structure, geojson_file, indent=2)

    print(
        f"✔ Created GeoJSON file '{output_geojson_path}' with {len(features)} features (1 origin, {len(all_items)} destinations)."
    )


if __name__ == "__main__":
    # --- Configuration ---
    input_directory = "results/responses/"
    output_directory = "results/extracted/"

    # --- Main Execution Logic ---
    os.makedirs(output_directory, exist_ok=True)
    print(f"Input directory:  '{input_directory}'")
    print(f"Output directory: '{output_directory}'\n")

    search_pattern = os.path.join(input_directory, "motis_one_to_all_*.json")
    input_files = glob.glob(search_pattern)

    if not input_files:
        print(f"Error: No files found matching the pattern '{search_pattern}'.")
    else:
        print(f"Found {len(input_files)} files to process.")

    for input_filepath in input_files:
        filename = os.path.basename(input_filepath)
        print(f"\n--- Processing file: {filename} ---")

        base_name = filename.removesuffix(".json")
        identifier = base_name.replace("motis_one_to_all_", "")

        output_csv_file = os.path.join(
            output_directory, f"extracted_data_{identifier}.csv"
        )
        output_geojson_file = os.path.join(
            output_directory, f"map_data_{identifier}.geojson"
        )

        # Call the unified processing function
        process_file(input_filepath, output_csv_file, output_geojson_file)

    print("\n--- All files processed! ---")
