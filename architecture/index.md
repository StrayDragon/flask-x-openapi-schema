# Architecture

This page describes the architecture of Flask-X-OpenAPI-Schema using Mermaid diagrams.

## Component Overview

The following diagram shows the main components of Flask-X-OpenAPI-Schema and their relationships:

```
graph TD
    A[Flask Application] --> B[Flask-X-OpenAPI-Schema]
    B --> C[Core]
    B --> D[Flask Extensions]
    B --> E[Flask-RESTful Extensions]

    C --> C1[Schema Generator]
    C --> C2[Configuration]
    C --> C3[Cache]
    C --> C4[Decorator Base]
    C --> C5[Utilities]

    D --> D1[MethodView Integration]
    D --> D2[Route Decorators]

    E --> E1[Resource Integration]
    E --> E2[RequestParser Integration]

    B --> F[Models]
    F --> F1[Base Models]
    F --> F2[File Models]
    F --> F3[Response Models]

    B --> G[Internationalization]
    G --> G1[I18n String]
    G --> G2[I18n Model]
    G --> G3[Language Management]
```

## Request Flow

The following sequence diagram shows how a request is processed:

```
sequenceDiagram
    participant Client
    participant Flask
    participant Decorator
    participant SchemaGenerator
    participant ModelBinder
    participant Handler

    Client->>Flask: HTTP Request
    Flask->>Decorator: Route Match
    Decorator->>SchemaGenerator: Get Schema
    SchemaGenerator-->>Decorator: Return Schema
    Decorator->>ModelBinder: Bind Request Data
    ModelBinder-->>Decorator: Return Bound Models
    Decorator->>Handler: Call with Bound Models
    Handler-->>Decorator: Return Response
    Decorator->>Flask: Format Response
    Flask-->>Client: HTTP Response
```

## Class Diagram

The following class diagram shows the main classes and their relationships:

```
classDiagram
    class OpenAPIMetadataBase {
        +summary: str
        +description: str
        +tags: List[str]
        +responses: Dict
        +__call__(func)
    }

    class OpenAPIMethodView {
        +get_openapi_info()
    }

    class OpenAPIResource {
        +get_openapi_info()
    }

    class SchemaGenerator {
        +generate_schema_from_model(model)
        +generate_schema_from_function(func)
    }

    class BaseRespModel {
        +to_response()
    }

    class FileUploadModel {
        +file: FileStorage
        +validate()
    }

    class I18nStr {
        +translations: Dict[str, str]
        +__str__()
    }

    OpenAPIMetadataBase <|-- FlaskOpenAPIMetadata
    OpenAPIMetadataBase <|-- FlaskRESTfulOpenAPIMetadata

    OpenAPIMethodView --> FlaskOpenAPIMetadata
    OpenAPIResource --> FlaskRESTfulOpenAPIMetadata

    FlaskOpenAPIMetadata --> SchemaGenerator
    FlaskRESTfulOpenAPIMetadata --> SchemaGenerator

    BaseRespModel <|-- CustomResponseModel
    FileUploadModel <|-- ImageUploadModel
    FileUploadModel <|-- AudioUploadModel
```

## Entity Relationship Diagram

The following ER diagram shows the data model:

```
erDiagram
    OPENAPI_SCHEMA ||--o{ ENDPOINT : contains
    ENDPOINT ||--o{ PARAMETER : has
    ENDPOINT ||--o{ RESPONSE : returns
    PARAMETER }|--|| MODEL : uses
    RESPONSE }|--|| MODEL : uses
    MODEL ||--o{ PROPERTY : has

    OPENAPI_SCHEMA {
        string title
        string version
        string description
    }

    ENDPOINT {
        string path
        string method
        string summary
        string description
        array tags
    }

    PARAMETER {
        string name
        string location
        string description
        boolean required
        string schema_ref
    }

    RESPONSE {
        string status_code
        string description
        string schema_ref
    }

    MODEL {
        string name
        string type
        string description
    }

    PROPERTY {
        string name
        string type
        string description
        boolean required
    }
```

## State Diagram

The following state diagram shows the lifecycle of a request:

```
stateDiagram-v2
    [*] --> Received
    Received --> Parsing
    Parsing --> Validating
    Validating --> Processing
    Processing --> Responding
    Responding --> [*]

    Parsing --> Error: Invalid Format
    Validating --> Error: Invalid Data
    Processing --> Error: Processing Failed
    Error --> Responding
```
