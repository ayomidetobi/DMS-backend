# Project Name: Document Management System (DMS)

## Overview
This Django-based project provides a document management system that offers users the ability to manage and explore judicial documents seamlessly. The system extracts metadata from raw HTML files and entities from associated JSON files, processes the data into a clean format, and stores them in a robust database structure. The frontend interfaces with a RESTful API that follows best practices in API design, ensuring a seamless user experience.

## Features
- RESTful API with support for all frontend functionalities.
- Metadata extraction from raw HTML and associated JSON files.
- Robust database seeder to populate and manage judicial documents.
- Well-designed database schema for storing documents and entities.
- Comprehensive error handling in both backend and frontend operations.
- API documentation available at: [Swagger Documentation](https://tobi-neural.azurewebsites.net/swagger/)

## Technologies Used
- **Backend**: Django, Django REST Framework (DRF)
- **Database**: PostgreSQL
- **Docker**
- **Other Dependencies**: BeautifulSoup for HTML parsing.

## Setup and Installation

### Prerequisites
- Python 3.9+
- PostgreSQL

### Backend Setup

## Run Docker Image

    ```
        docker run -p 8000:8000 tobineural.azurecr.io/neuralshift-web:latest
    ```
 
1. Clone the repository:
   ```sh
   git clone https://github.com/ayomidetobi/DMS-backend.git
   
   ```
2. Navigate to the project directory:
   ```sh
   cd DMS-backend
   ```


3. venv
    ```sh
    python -m venv venv
    ```
4. Activate environment
    ```sh
    # On Windows
        venv\Scripts\activate
    ```

    ```sh
    # On macOS or Linux
    source venv/bin/activate
    ```



5. Install Python dependencies:
   ```sh
   pip install -r requirements.txt
   ```
6. Set up the PostgreSQL database and update your environment variables for database connectivity in `settings.py`.
   - **Environment Variables**: Set the following variables in your environment or `.env` file:
     - `DEBUG`: Set to `True` for development or `False` for production.
     - `SECRET_KEY`: A secret key for your Django application.
     - `ALLOWED_HOSTS`: A list of strings representing the host/domain names that this Django site can serve.
     - `CSRF_TRUSTED_ORIGINS`: Comma-separated list of trusted origins for CSRF.
     - `DB_NAME`: Name of your PostgreSQL database.
     - `DB_USER`: Username for the database.
     - `DB_PASSWORD`: Password for the database user.
     - `DB_HOST`: Host address for the database.
     - `DB_PORT`: Port number for the database.
     - `CORS_ALLOWED_ORIGINS`: Comma-separated list of allowed origins for CORS (e.g., `http://localhost:3000, http://example.com`).
     - `CORS_ALLOW_ALL_ORIGINS`: Set to `True` or `False` to allow all origins.

     Example `.env` file using `decouple`:
     ```env
     DEBUG=True
     SECRET_KEY=your_secret_key_here
     ALLOWED_HOSTS=localhost, 127.0.0.1
     CSRF_TRUSTED_ORIGINS=http://localhost:3000, http://example.com
     DB_NAME=dms_db
     DB_USER=your_db_user
     DB_PASSWORD=your_db_password
     DB_HOST=localhost
     DB_PORT=5432
     CORS_ALLOWED_ORIGINS=http://localhost:3000, http://example.com
     CORS_ALLOW_ALL_ORIGINS=True
     ```
7. Run migrations:
   ```sh
   python manage.py migrate
   ```
8. Run the server:
   ```sh
   python manage.py runserver
   ```
9. Populate the database from HTML and JSON files:
   ```sh
   python manage.py seed_database
   ```

### Running Tests
To run the backend tests, use:
```sh
pytest
```
This will execute all available test cases and display the results.


## Seeder Mechanism
The system includes a database seeder script that:
- Extracts metadata from raw HTML files.
- Parses and standardizes the content.
- Extracts entities from associated JSON files.
- Stores the parsed data in the database.

To populate the database, use the following command:
```sh
python manage.py seed_database
```
This seeder ensures that judicial documents are well-organized and easily searchable in the system.

## SWOT Analysis for the API

### Strengths

- **Comprehensive Error Handling**: All endpoints provide appropriate error responses, ensuring robust user interactions.
- **Data Extraction**: The automated metadata extraction from HTML and JSON files ensures consistent and high-quality data in the database.
- **Scalable Design**: Uses Django REST Framework with an efficient database design that is well-suited for scaling.
- **ETag Implementation**: Utilizes ETags to optimize caching and reduce unnecessary data transfer.
- **ThreadPoolExecutor**: The use of ThreadPoolExecutor for seeding operations ensures efficient concurrent processing of multiple files.

### Weaknesses

- **Complexity in Seeder**: The HTML parsing relies heavily on structure consistency, and unexpected variations in HTML structure might lead to errors.
- **Dependency Management**: Heavy reliance on multiple Python libraries for parsing, which can cause version conflicts or security vulnerabilities if not managed correctly.

### Opportunities

- **Expand API Features**: Adding advanced search and filter capabilities to the API could improve the end-user experience.
- **Use AI for Parsing**: Incorporate machine learning to intelligently handle inconsistencies in HTML structure during parsing.


### Threats

- **Data Inconsistencies**: Potential for data inconsistencies if the HTML files provided do not follow a uniform structure.
- **Scaling Issues**: If the number of documents grows rapidly, scaling the database and optimizing queries could become challenging.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss changes.

