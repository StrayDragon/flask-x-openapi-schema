# Flask-X-OpenAPI-Schema Documentation

## Project Overview

Flask-X-OpenAPI-Schema is a library that simplifies the generation of OpenAPI schemas from Flask-RESTful resources and Pydantic models. It provides a seamless integration between Flask, Flask-RESTful, and Pydantic, allowing developers to create well-documented APIs with minimal effort.

The library focuses on automating the process of generating OpenAPI documentation by leveraging Python type annotations and Pydantic models, while also providing support for internationalization (i18n) and file uploads.

## Core Features

- **Automatic OpenAPI Schema Generation**: Generate OpenAPI schemas from Flask-RESTful resources
- **Pydantic Integration**: Convert Pydantic models to OpenAPI schemas
- **Parameter Auto-Detection**: Automatically detect and inject request parameters from function signatures
- **Type Preservation**: Preserve type annotations from Pydantic models for better IDE support
- **Multiple Output Formats**: Output schemas in YAML or JSON format
- **Internationalization Support**: Support for i18n in API documentation
- **File Upload Handling**: Simplified handling of file uploads with automatic parameter injection

## Architecture

The following diagram illustrates the high-level architecture of Flask-X-OpenAPI-Schema:

```mermaid
graph TD
    A[Flask Application] --> B[Flask-RESTful API]
    B --> C[OpenAPIIntegrationMixin]
    C --> D[OpenAPISchemaGenerator]
    D --> E[OpenAPI Schema]
    
    F[Resource Methods] --> G[openapi_metadata Decorator]
    G --> H[Parameter Auto-Detection]
    H --> I[Request Processing]
    I --> J[Response Generation]
    
    K[Pydantic Models] --> L[Schema Conversion]
    L --> D
    
    M[I18nString/I18nBaseModel] --> N[Internationalization]
    N --> D
    
    O[File Upload Models] --> P[File Processing]
    P --> I
```

## Core Components

### 1. Decorator System

The `openapi_metadata` decorator is the primary entry point for adding OpenAPI metadata to API endpoints:

```mermaid
sequenceDiagram
    participant D as Developer
    participant O as openapi_metadata
    participant F as Flask Resource Method
    participant S as Schema Generator
    
    D->>O: Apply decorator with metadata
    O->>F: Wrap method with parameter binding
    O->>F: Attach OpenAPI metadata
    F->>S: Provide metadata during schema generation
    S->>D: Generate OpenAPI schema
```

### 2. Parameter Auto-Detection

The library automatically detects parameters with special prefixes and their types:

```mermaid
graph LR
    A[Function Parameters] --> B{Parameter Prefix?}
    B -->|x_request_body| C[Request Body]
    B -->|x_request_query| D[Query Parameters]
    B -->|x_request_path_*| E[Path Parameters]
    B -->|x_request_file| F[File Upload]
    
    C --> G[Pydantic Model]
    D --> G
    E --> H[Parameter Binding]
    F --> I[File Processing]
    
    G --> J[Type Preservation]
    H --> K[Request Handling]
    I --> K
    J --> K
```

### 3. Schema Generation Process

The schema generation process involves scanning Flask blueprints and resources:

```mermaid
flowchart TD
    A[Initialize Schema Generator] --> B[Scan Blueprint]
    B --> C[Process Resources]
    C --> D[Extract Paths]
    D --> E[Process HTTP Methods]
    E --> F[Build Operations]
    F --> G[Register Models]
    G --> H[Generate Schema]
    
    I[Pydantic Models] --> J[Convert to OpenAPI]
    J --> G
    
    K[I18n Strings] --> L[Language Processing]
    L --> F
```

### 4. Internationalization Support

The i18n support allows for multilingual API documentation:

```mermaid
graph TD
    A[I18nString] --> B[Language Mapping]
    B --> C{Current Language?}
    C -->|Found| D[Return Language String]
    C -->|Not Found| E[Return Default Language]
    
    F[I18nBaseModel] --> G[Model with I18n Fields]
    G --> H[Language-Specific Schema]
    
    I[Thread-Local Storage] --> J[get_current_language]
    J --> C
    K[set_current_language] --> I
```

### 5. File Upload Handling

The file upload handling simplifies working with uploaded files:

```mermaid
sequenceDiagram
    participant C as Client
    participant F as Flask Request
    participant D as Decorator
    participant R as Resource Method
    
    C->>F: POST multipart/form-data
    F->>D: Process request
    D->>F: Extract files
    D->>R: Inject file objects
    R->>C: Return response
```

## Data Flow

The following diagram illustrates the data flow when processing an API request:

```mermaid
flowchart LR
    A[Client Request] --> B[Flask Router]
    B --> C[Flask-RESTful Resource]
    C --> D[openapi_metadata Wrapper]
    D --> E{Parameter Type?}
    
    E -->|Body| F[Parse JSON]
    E -->|Query| G[Parse Query String]
    E -->|Path| H[Extract Path Params]
    E -->|File| I[Process Files]
    
    F --> J[Create Pydantic Model]
    G --> J
    H --> K[Bind to Parameters]
    I --> L[Create File Model]
    
    J --> M[Validate Data]
    K --> N[Original Method]
    L --> N
    M --> N
    
    N --> O[Generate Response]
    O --> P[Convert to Flask Response]
    P --> Q[Client]
```

## Integration Points

Flask-X-OpenAPI-Schema integrates with several components:

```mermaid
graph TD
    A[Flask-X-OpenAPI-Schema] --- B[Flask]
    A --- C[Flask-RESTful]
    A --- D[Pydantic]
    A --- E[OpenAPI]
    
    B --- F[Web Framework]
    C --- G[REST API]
    D --- H[Data Validation]
    E --- I[API Documentation]
    
    A --- J[Werkzeug]
    J --- K[File Handling]
```

## Usage Patterns

### Basic Usage Pattern

```mermaid
sequenceDiagram
    participant D as Developer
    participant P as Pydantic Model
    participant R as Resource Method
    participant O as openapi_metadata
    participant S as Schema Generator
    
    D->>P: Define request/response models
    D->>R: Create API endpoint
    D->>O: Apply decorator with metadata
    D->>S: Generate OpenAPI schema
    S->>D: Return schema document
```

### Advanced Usage with I18n

```mermaid
sequenceDiagram
    participant D as Developer
    participant I as I18nString/I18nBaseModel
    participant O as openapi_metadata
    participant L as Language Setting
    participant S as Schema Generator
    
    D->>I: Define multilingual strings/models
    D->>O: Apply decorator with i18n metadata
    D->>L: Set current language
    D->>S: Generate OpenAPI schema
    S->>L: Get current language
    L->>S: Return language code
    S->>I: Request strings for language
    I->>S: Return localized strings
    S->>D: Return localized schema
```

## Implementation Details

### Key Classes and Their Relationships

```mermaid
classDiagram
    class OpenAPISchemaGenerator {
        +title: str
        +version: str
        +description: str
        +language: str
        +paths: dict
        +components: dict
        +tags: list
        +scan_blueprint(blueprint)
        +generate_schema()
    }
    
    class OpenAPIIntegrationMixin {
        +generate_openapi_schema(title, version, description)
    }
    
    class I18nString {
        +strings: dict
        +default_language: str
        +get(language)
        +__str__()
    }
    
    class I18nBaseModel {
        +for_language(language)
    }
    
    class BaseRespModel {
        +to_response(status_code)
    }
    
    class FileUploadModel {
        +file: FileStorage
        +validate_file()
    }
    
    OpenAPIIntegrationMixin --> OpenAPISchemaGenerator
    I18nBaseModel --|> BaseModel
    BaseRespModel --|> BaseModel
    FileUploadModel --|> BaseModel
```

## Conclusion

Flask-X-OpenAPI-Schema provides a powerful yet easy-to-use solution for generating OpenAPI documentation from Flask-RESTful APIs. By leveraging Python type annotations and Pydantic models, it automates much of the documentation process while providing rich features like internationalization and file upload handling.

The library's architecture is designed to be flexible and extensible, allowing developers to customize the documentation generation process to suit their specific needs.