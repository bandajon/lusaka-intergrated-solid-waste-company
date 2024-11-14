# **Detailed Folder Structures for Individual Repositories of Microservices and BFF**

---

## **Introduction**

In a microservices architecture where each service is stored in its own repository, it's essential to have a consistent and well-organized folder structure for each repository. This approach promotes service independence, clear ownership, and easier access control management. This document outlines detailed folder structures for each microservice and the Backend For Frontend (BFF) service for the Lusaka Integrated Solid Waste Management Platform.

Each service will have its own repository with a consistent structure to facilitate development, testing, deployment, and maintenance. Shared code and libraries will be managed separately to maintain service independence while ensuring code reuse.

---

## **General Folder Structure for Each Service Repository**

The following is a general template for the folder structure of each service:

```
service-name/
├── README.md
├── go.mod
├── go.sum
├── cmd/
│   └── service-name/
│       └── main.go
├── internal/
│   ├── config/
│   │   └── config.go
│   ├── server/
│   │   ├── grpc_server.go
│   │   └── http_server.go (if applicable)
│   ├── handlers/
│   │   └── handlers.go
│   ├── services/
│   │   └── business_logic.go
│   ├── repositories/
│   │   └── database_access.go
│   ├── models/
│   │   └── data_models.go
│   ├── middleware/
│   │   └── middleware.go
│   └── utils/
│       └── helper_functions.go
├── pkg/
│   └── (exported packages if any)
├── api/
│   └── proto/
│       └── service-name.proto
├── migrations/
│   └── 0001_initial_schema.up.sql
├── tests/
│   ├── unit/
│   │   └── unit_test.go
│   ├── integration/
│   │   └── integration_test.go
│   └── mocks/
│       └── mock_service.go
├── scripts/
│   ├── build.sh
│   ├── test.sh
│   └── run.sh
├── Dockerfile
├── Makefile
├── .gitignore
├── .golangci.yml
├── .editorconfig
└── LICENSE
```

**Explanation:**

- **`README.md`:** Provides an overview, setup instructions, and usage information for the service.
- **`go.mod`, `go.sum`:** Go module files for dependency management.
- **`cmd/`:** Contains the main application entry point.
- **`internal/`:** Houses the core application code that should not be imported by other services.
  - **`config/`:** Configuration structures and loading logic.
  - **`server/`:** Server setup for gRPC and/or HTTP servers.
  - **`handlers/`:** Request handlers that interact with services.
  - **`services/`:** Business logic and service implementations.
  - **`repositories/`:** Data access layer for database interactions.
  - **`models/`:** Data models and structures.
  - **`middleware/`:** Middleware functions for request processing.
  - **`utils/`:** Utility functions specific to the service.
- **`pkg/`:** Exported packages that can be used by other services or repositories (if any).
- **`api/proto/`:** Contains Protocol Buffers definitions for gRPC communication.
- **`migrations/`:** Database migration scripts.
- **`tests/`:** Contains unit, integration tests, and mocks.
- **`scripts/`:** Automation scripts for building, testing, and running the service.
- **`Dockerfile`:** Instructions to build the Docker image for the service.
- **`Makefile`:** Build commands and shortcuts.
- **`.gitignore`:** Specifies files to be ignored by Git.
- **`.golangci.yml`:** Configuration for Go linters.
- **`.editorconfig`:** Ensures consistent coding styles.
- **`LICENSE`:** Licensing information.

---

## **Folder Structures for Specific Services**

### **1. Backend For Frontend (BFF) Service**

**Repository Name:** `liswmc-bff-service`

```
liswmc-bff-service/
├── README.md
├── go.mod
├── go.sum
├── cmd/
│   └── bff/
│       └── main.go
├── internal/
│   ├── config/
│   │   └── config.go
│   ├── server/
│   │   └── http_server.go
│   ├── handlers/
│   │   ├── user_handler.go
│   │   ├── payment_handler.go
│   │   ├── waste_handler.go
│   │   ├── fleet_handler.go
│   │   └── auth_handler.go
│   ├── services/
│   │   ├── user_service.go
│   │   ├── payment_service.go
│   │   ├── waste_service.go
│   │   ├── fleet_service.go
│   │   └── auth_service.go
│   ├── middleware/
│   │   ├── auth_middleware.go
│   │   ├── logging_middleware.go
│   │   └── recovery_middleware.go
│   └── utils/
│       └── response_util.go
├── pkg/
│   └── (exported packages if any)
├── api/
│   └── docs/
│       └── openapi.yaml
├── tests/
│   ├── unit/
│   │   └── bff_unit_test.go
│   ├── integration/
│   │   └── bff_integration_test.go
│   └── mocks/
│       └── mock_services.go
├── scripts/
│   ├── build.sh
│   ├── test.sh
│   └── run.sh
├── Dockerfile
├── Makefile
├── .gitignore
├── .golangci.yml
├── .editorconfig
└── LICENSE
```

**Key Points:**

- **`handlers/`:** Handles HTTP requests and translates them into gRPC calls to backend services.
- **`services/`:** Contains client code for communicating with backend microservices via gRPC.
- **`api/docs/`:** OpenAPI/Swagger documentation for the RESTful APIs exposed by the BFF.
- **`middleware/`:** Middleware functions for authentication, logging, and error recovery.

### **2. Authentication and Authorization Service**

**Repository Name:** `liswmc-auth-service`

```
liswmc-auth-service/
├── README.md
├── go.mod
├── go.sum
├── cmd/
│   └── auth-service/
│       └── main.go
├── internal/
│   ├── config/
│   │   └── config.go
│   ├── server/
│   │   └── grpc_server.go
│   ├── services/
│   │   └── auth_service.go
│   ├── repositories/
│   │   └── user_repository.go
│   ├── models/
│   │   ├── user.go
│   │   └── token.go
│   ├── middleware/
│   │   └── logging_middleware.go
│   └── utils/
│       ├── crypto_util.go
│       └── token_util.go
├── api/
│   └── proto/
│       └── auth.proto
├── migrations/
│   └── 0001_create_users_table.up.sql
├── tests/
│   ├── unit/
│   │   └── auth_unit_test.go
│   ├── integration/
│   │   └── auth_integration_test.go
│   └── mocks/
│       └── mock_user_repository.go
├── scripts/
├── Dockerfile
├── Makefile
├── .gitignore
├── .golangci.yml
├── .editorconfig
└── LICENSE
```

**Key Points:**

- **`services/auth_service.go`:** Core authentication logic, including password hashing and token generation.
- **`repositories/user_repository.go`:** Interacts with the database for user data.
- **`api/proto/auth.proto`:** Defines the gRPC service interface and messages.
- **`utils/`:** Contains utilities for cryptographic functions and token handling.

### **3. User Management Service**

**Repository Name:** `liswmc-user-service`

```
liswmc-user-service/
├── README.md
├── go.mod
├── go.sum
├── cmd/
│   └── user-service/
│       └── main.go
├── internal/
│   ├── config/
│   ├── server/
│   │   └── grpc_server.go
│   ├── services/
│   │   └── user_service.go
│   ├── repositories/
│   │   └── user_repository.go
│   ├── models/
│   │   └── user.go
│   ├── middleware/
│   └── utils/
├── api/
│   └── proto/
│       └── user.proto
├── migrations/
│   └── 0001_create_users_table.up.sql
├── tests/
│   ├── unit/
│   ├── integration/
│   └── mocks/
├── scripts/
├── Dockerfile
├── Makefile
├── .gitignore
└── LICENSE
```

**Key Points:**

- Manages user profiles, roles, and permissions.
- Exposes gRPC methods defined in `user.proto`.

### **4. Payment Service**

**Repository Name:** `liswmc-payment-service`

```
liswmc-payment-service/
├── README.md
├── go.mod
├── go.sum
├── cmd/
│   └── payment-service/
│       └── main.go
├── internal/
│   ├── config/
│   ├── server/
│   │   └── grpc_server.go
│   ├── services/
│   │   ├── payment_service.go
│   │   └── reconciliation_service.go
│   ├── integrations/
│   │   ├── mtn/
│   │   │   └── mtn_client.go
│   │   ├── airtel/
│   │   │   └── airtel_client.go
│   │   └── zamtel/
│       └── zamtel_client.go
│   ├── repositories/
│   │   └── payment_repository.go
│   ├── models/
│   │   └── payment.go
│   ├── middleware/
│   └── utils/
│       └── idempotency_util.go
├── api/
│   └── proto/
│       └── payment.proto
├── migrations/
│   └── 0001_create_payments_table.up.sql
├── tests/
│   ├── unit/
│   ├── integration/
│   └── mocks/
├── scripts/
├── Dockerfile
├── Makefile
├── .gitignore
└── LICENSE
```

**Key Points:**

- **`integrations/`:** Contains clients for interacting with mobile money providers.
- **`services/payment_service.go`:** Implements idempotent payment operations and handles transaction states.
- **`utils/idempotency_util.go`:** Provides functions to manage idempotency keys.

### **5. Waste Collection Service**

**Repository Name:** `liswmc-waste-collection-service`

```
liswmc-waste-collection-service/
├── README.md
├── go.mod
├── go.sum
├── cmd/
│   └── waste-collection-service/
│       └── main.go
├── internal/
│   ├── config/
│   ├── server/
│   ├── services/
│   │   ├── schedule_service.go
│   │   ├── zone_service.go
│   │   └── report_service.go
│   ├── integrations/
│   │   ├── google_maps/
│   │   │   └── google_maps_client.go
│   │   └── google_earth_engine/
│       └── google_earth_engine_client.go
│   ├── repositories/
│   │   ├── zone_repository.go
│   │   ├── route_repository.go
│   │   └── report_repository.go
│   ├── models/
│   │   ├── zone.go
│   │   ├── route.go
│   │   └── report.go
│   ├── middleware/
│   └── utils/
├── api/
│   └── proto/
│       └── waste_collection.proto
├── migrations/
│   └── 0001_create_zones_table.up.sql
├── tests/
│   ├── unit/
│   ├── integration/
│   └── mocks/
├── scripts/
├── Dockerfile
├── Makefile
├── .gitignore
└── LICENSE
```

**Key Points:**

- Manages waste collection schedules, zones, and issue reports.
- Integrates with Google Maps API and Google Earth Engine for route optimization and zone classification.

### **6. Fleet Management Service**

**Repository Name:** `liswmc-fleet-management-service`

```
liswmc-fleet-management-service/
├── README.md
├── go.mod
├── go.sum
├── cmd/
│   └── fleet-management-service/
│       └── main.go
├── internal/
│   ├── config/
│   ├── server/
│   ├── services/
│   │   ├── vehicle_service.go
│   │   ├── driver_service.go
│   │   └── tracking_service.go
│   ├── repositories/
│   │   ├── vehicle_repository.go
│   │   ├── driver_repository.go
│   │   └── tracking_repository.go
│   ├── models/
│   │   ├── vehicle.go
│   │   ├── driver.go
│   │   └── tracking.go
│   ├── middleware/
│   └── utils/
├── api/
│   └── proto/
│       └── fleet_management.proto
├── migrations/
│   └── 0001_create_vehicles_table.up.sql
├── tests/
│   ├── unit/
│   ├── integration/
│   └── mocks/
├── scripts/
├── Dockerfile
├── Makefile
├── .gitignore
└── LICENSE
```

**Key Points:**

- Manages vehicles, drivers, and real-time tracking data.
- Provides APIs for assigning routes and dispatching vehicles.

### **7. Notification Service**

**Repository Name:** `liswmc-notification-service`

```
liswmc-notification-service/
├── README.md
├── go.mod
├── go.sum
├── cmd/
│   └── notification-service/
│       └── main.go
├── internal/
│   ├── config/
│   ├── server/
│   ├── services/
│   │   ├── sms_service.go
│   │   ├── push_service.go
│   │   └── email_service.go
│   ├── integrations/
│   │   ├── zamtel_sms/
│   │   │   └── zamtel_sms_client.go
│   │   └── firebase_messaging/
│       └── firebase_client.go
│   ├── repositories/
│   ├── models/
│   ├── middleware/
│   └── utils/
├── api/
│   └── proto/
│       └── notification.proto
├── tests/
├── scripts/
├── Dockerfile
├── Makefile
├── .gitignore
└── LICENSE
```

**Key Points:**

- Manages sending notifications via SMS, push notifications, and email.
- Integrates with external messaging services.

### **8. Reporting and Analytics Service**

**Repository Name:** `liswmc-reporting-service`

```
liswmc-reporting-service/
├── README.md
├── go.mod
├── go.sum
├── cmd/
│   └── reporting-service/
│       └── main.go
├── internal/
│   ├── config/
│   ├── server/
│   ├── services/
│   │   ├── report_service.go
│   │   └── analytics_service.go
│   ├── repositories/
│   │   ├── report_repository.go
│   │   └── analytics_repository.go
│   ├── models/
│   │   ├── report.go
│   │   └── analytics.go
│   ├── middleware/
│   └── utils/
├── api/
│   └── proto/
│       └── reporting.proto
├── tests/
├── scripts/
├── Dockerfile
├── Makefile
├── .gitignore
└── LICENSE
```

**Key Points:**

- Generates reports and provides analytics data to LISWMC staff.
- Aggregates data from other services for comprehensive insights.

---

## **Managing Shared Code and Libraries**

In a multi-repository setup, shared code and libraries need to be managed carefully to avoid duplication and maintain consistency.

### **Options for Shared Code Management**

1. **Shared Library Repositories:**

   - Create separate repositories for shared libraries or packages.
   - Example repositories:
     - `liswmc-shared-utils`
     - `liswmc-proto-definitions`

2. **Go Modules and Versioning:**

   - Publish shared libraries as Go modules.
   - Version the modules using semantic versioning.
   - Services can import the shared modules using `go.mod`.

3. **Package Repositories:**

   - Use private package repositories (e.g., Go Proxy, Artifactory, or GitHub Packages) to host shared modules.

### **Example Shared Repository: `liswmc-proto-definitions`**

```
liswmc-proto-definitions/
├── README.md
├── go.mod
├── api/
│   ├── auth/
│   │   └── auth.proto
│   ├── user/
│   │   └── user.proto
│   ├── payment/
│   │   └── payment.proto
│   ├── waste_collection/
│   │   └── waste_collection.proto
│   ├── fleet_management/
│   │   └── fleet_management.proto
│   ├── notification/
│   │   └── notification.proto
│   └── reporting/
│       └── reporting.proto
├── scripts/
│   └── generate_protos.sh
├── Makefile
├── .gitignore
└── LICENSE
```

**Key Points:**

- Contains all Protocol Buffers definitions used across services.
- Services import the shared `proto` definitions from this repository.

### **Using the Shared Modules in Services**

- In each service's `go.mod`, include the shared module:

  ```
  module github.com/liswmc/liswmc-payment-service

  go 1.17

  require (
      github.com/liswmc/liswmc-proto-definitions v1.0.0
      ...
  )
  ```

- Import statements in the code:

  ```go
  import (
      "github.com/liswmc/liswmc-proto-definitions/api/payment"
  )
  ```

---

## **Additional Considerations**

### **Consistent Coding Standards**

- Use linters and formatters (e.g., `golangci-lint`) configured via `.golangci.yml` in each repository.
- Enforce coding standards and best practices across all services.

### **CI/CD Pipelines**

- Set up continuous integration and deployment pipelines for each repository.
- Use shared scripts or templates where possible to reduce duplication.

### **Dependency Management**

- Keep dependencies updated.
- Use tools like Dependabot or Renovate to automate dependency updates.

### **Access Control**

- Manage access permissions per repository to control who can contribute to each service.

### **Documentation**

- Maintain up-to-date `README.md` files in each repository.
- Provide service-specific documentation, including API usage and setup instructions.

### **Issue Tracking and Project Management**

- Use a centralized issue tracker with labels or tags to associate issues with specific services.
- Alternatively, enable issue tracking per repository.

### **Versioning and Releases**

- Use semantic versioning for each service.
- Tag releases in Git and maintain release notes.

---

## **Conclusion**

By organizing each microservice and the BFF in separate repositories with a consistent folder structure, the Lusaka Integrated Solid Waste Management Platform can achieve service independence, clear ownership, and better access control. Shared code and libraries are managed separately, promoting code reuse while maintaining loose coupling between services.

This approach facilitates independent development, testing, deployment, and scaling of each service, aligning with microservices architecture best practices.

---

*For any further assistance or clarifications regarding the folder structures or repository management, please feel free to reach out.*