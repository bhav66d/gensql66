# GenSQL66 - Synthetic Data Generator

GenSQL66 is a tool designed to convert schemas and generate realistic synthetic data for various use cases, including testing, development, and data augmentation. It leverages AI to convert schemas between different SQL dialects and generate synthetic data based on existing data patterns or defined schemas.

## Features

-   **Schema Conversion:** Convert schemas between different SQL dialects using AI.
-   **Synthetic Data Generation:** Generate realistic synthetic data from schemas or existing data.
-   **Multiple Data Generation Methods:** Supports schema-based generation, converted schema generation, and existing data replication.
-   **Customizable AI Configuration:** Configure AI models and settings for schema conversion.
-   **Data Analysis:** Analyze existing data to understand patterns and distributions for synthetic data generation.
-   **Downloadable Data Packages:** Generate and download synthetic data in ZIP format, including CSV and Excel files.

## Setup Instructions

1.  **Prerequisites:**
    -   Python 3.9+
    -   Streamlit
    -   Pandas
    -   Faker
    -   Other dependencies (see `requirements.txt`)

2.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Configuration:**
    -   Set up the necessary environment variables for the LLM service (if applicable).

## Usage

1.  **Run the Application:**

    ```bash
    streamlit run app.py
    ```

2.  **Access the Application:**
    -   Open your browser and navigate to the URL provided by Streamlit (usually `http://localhost:8501`).

3.  **Schema Converter:**
    -   Go to the "Schema Converter" tab.
    -   Input your schema by uploading a file or pasting it directly.
    -   Select the target SQL dialect.
    -   Configure AI settings if needed.
    -   Click "Convert Schema" to convert the schema.
    -   Review the converted schema and make adjustments if necessary.
    -   Download the converted schema or use it directly for data generation.

4.  **Data Generator:**
    -   Go to the "Data Generator" tab.
    -   Select the data generation method: "Upload Schema", "Use Converted Schema", or "Generate from Existing Data".
    -   Configure the number of samples and noise level (if applicable).
    -   Click "Generate Synthetic Data" to generate the data.
    -   Preview the generated data and download it in ZIP format.

## Dockerization

1.  **Build the Docker Image:**

    ```bash
    docker build -t gensql66 .
    ```

2.  **Run the Docker Container:**

    ```bash
    docker run -p 8501:8501 gensql66
    ```

3.  **Access the Application:**
    -   Open your browser and navigate to `http://localhost:8501`.

## Contributing

Feel free to contribute to the project by submitting pull requests, reporting issues, or suggesting new features.
