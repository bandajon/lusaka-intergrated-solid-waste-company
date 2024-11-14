# **Comprehensive System Design for the Lusaka Integrated Solid Waste Management Platform**

---

## **Table of Contents**

1. [Introduction](#introduction)
2. [System Overview](#system-overview)
3. [User Roles and Permissions](#user-roles-and-permissions)
4. [System Components](#system-components)
    - a. [Backend API Service](#backend-api-service)
    - b. [Database Design (PostgreSQL)](#database-design-postgresql)
    - c. [Frontend Clients](#frontend-clients)
    - d. [Integration Services](#integration-services)
    - e. [Google Earth Engine Integration](#google-earth-engine-integration)
5. [Key Features and Functionalities](#key-features-and-functionalities)
6. [Additional Design Considerations](#additional-design-considerations)
7. [Implementation Plan](#implementation-plan)
8. [Potential Challenges and Mitigations](#potential-challenges-and-mitigations)
9. [Conclusion](#conclusion)
10. [Next Steps](#next-steps)

---

## **Introduction**

The Lusaka Integrated Solid Waste Management Company (LISWMC) aims to revolutionize waste management in Lusaka by leveraging modern software and web technologies. The proposed system is a robust, scalable platform that integrates various stakeholders—LISWMC staff, franchise collectors, and citizens—to enhance effective garbage collection and solid waste management. This document outlines the comprehensive system design, incorporating features such as payments management via mobile money (MTN, Airtel, and Zamtel), mapping of homes using plus codes, customer account linking via phone numbers, real-time tracking, fleet management for both franchise collectors and LISWMC, and advanced zone classification using Google Earth Engine APIs.

**Note:** Integration with bank payments will be implemented in **Phase 2** of the project.

---

## **System Overview**

The system is designed as a headless backend, developed in Go (Golang) with PostgreSQL as the database. It provides APIs consumed by various clients, including mobile apps (Android/iOS), a web application, and a USSD service for feature phones. Key integrations include mobile money payment gateways, mapping services, messaging platforms, and Google Earth Engine for zone density classification.

**Key Objectives:**

- **Efficiency:** Optimize waste collection routes and schedules.
- **Transparency:** Provide real-time tracking and updates to users.
- **Engagement:** Enable user participation through reporting and feedback mechanisms.
- **Scalability:** Design for future expansion and integration with advanced technologies.
- **Fleet Management:** Manage both franchise collectors' and LISWMC's own collection fleets, including emergency collections.
- **Payment Flexibility:** Allow users to make payments via MTN, Airtel, and Zamtel mobile money platforms, with bank integrations planned for Phase 2.

---

## **User Roles and Permissions**

### **1. Super Admin (LISWMC Staff)**

- Full system access.
- Approve franchise collector registrations.
- Assign zones and routes.
- Monitor operations and generate reports.
- Manage LISWMC's own fleet and scheduling.
- Dispatch emergency collections.

### **2. Franchise Collectors**

- Register their companies and upload required documents.
- Manage fleet and staff.
- Register users during collection.
- Access assigned zones and routes.

### **3. LISWMC Fleet Operators**

- Manage LISWMC's own collection trucks.
- Schedule regular and emergency collections.
- Update collection statuses and truck locations.

### **4. Citizens (Users)**

- Self-register to receive services.
- View collection times and schedules.
- Make payments via mobile money.
- Report uncollected or illegally dumped garbage.
- Receive notifications and alerts.

### **5. Drivers/Truck Staff (Franchise and LISWMC)**

- Use mobile app for route navigation and updates.
- Enable location services for real-time tracking.
- Report collection statuses.

### **6. Support Staff**

- Handle customer inquiries and issues.
- Manage reported problems and track resolutions.

---

## **System Components**

### **a. Backend API Service**

- **Language:** Go (Golang)
- **Frameworks:** Gin or Echo for RESTful API development.
- **Architecture:** Headless backend providing APIs for various clients.
- **Authentication & Authorization:** OAuth 2.0, JWT tokens, and role-based access control.
- **API Documentation:** Swagger/OpenAPI.

### **b. Database Design (PostgreSQL)**

#### **Entities and Relationships**

1. **Users**
   - `UserID`, `Name`, `PhoneNumbers`, `Addresses`, `PaymentStatus`, `Notifications`, `PlusCode`, `Occupants`, `AssignedCollectionPointID` (optional).

2. **FranchiseCollectors**
   - `CollectorID`, `CompanyInfo`, `Documents`, `AssignedZones`, `FleetDetails`, `Status`.

3. **LISWMCFleet**
   - `VehicleID`, `VehicleType`, `CurrentLocation`, `RouteID`, `DriverInfo`, `Status`, `AssignedTasks`.

4. **Trucks**
   - **Updated to include both Franchise and LISWMC Trucks**
   - `TruckID`, `OwnerType` (Franchise, LISWMC), `OwnerID`, `CurrentLocation`, `RouteID`, `DriverInfo`, `Status`.

5. **Zones**
   - `ZoneID`, `GeoPolygon`, `DensityInfo`, `AssignedCollectorID` (can be a FranchiseCollector or LISWMC).

6. **Routes**
   - `RouteID`, `ZoneID`, `PickupPoints`, `OptimizedPath`, `Schedule`, `AssignedTo` (FranchiseCollector or LISWMCFleet).

7. **CollectionPoints**
   - `CollectionPointID`, `Name`, `Location`, `ZoneID`, `Type`, `Capacity`, `CurrentFillLevel`, `Schedule`, `Status`.

8. **Payments**
   - `PaymentID`, `UserID`, `Amount`, `Date`, `Method`, `Status`.
   - **Payment Methods:** MTN Mobile Money, Airtel Money, Zamtel Kwacha.
   - **Note:** Bank payment methods to be added in Phase 2.

9. **Reports**
   - `ReportID`, `UserID`, `Type`, `Description`, `PhotoURL`, `Location`, `Timestamp`, `Status`.

10. **Notifications**
    - `NotificationID`, `UserID`, `Message`, `Type`, `DateSent`, `ReadStatus`.

11. **WasteEstimates**
    - `EstimateID`, `TruckID`, `RouteID`, `Date`, `EstimatedWasteVolume`.

12. **EmergencyCollections**
    - **New Entity Added**
    - `EmergencyID`, `RequestorID` (User or Staff), `Description`, `Location`, `Status`, `AssignedVehicleID`, `Timestamp`.

### **c. Frontend Clients**

#### **i. Mobile Applications (Android/iOS)**

- **Technology:** Flutter for cross-platform development.
- **Features:**
  - User registration/login.
  - View collection schedules and real-time truck tracking.
  - Make payments via mobile money.
  - Report issues with photo uploads.
  - Receive notifications.
  - Multi-language support.
  - **LISWMC Fleet Management Module:**
    - For LISWMC fleet operators and drivers.
    - Schedule management.
    - Emergency dispatching.

#### **ii. Web Application**

- **Technology:** React.js for responsive design.
- **Features:**
  - Similar to mobile app functionalities.
  - Admin dashboard for LISWMC staff.
  - Franchise collector portal for document upload and management.
  - Data visualization and reporting tools.
  - **Fleet Management Dashboard:**
    - For managing LISWMC's own collection fleet.
    - Real-time tracking of all vehicles.
    - Scheduling and dispatching tools.
    - Emergency collection management.

#### **iii. USSD Service**

- **Integration:** Partnership with Zamtel for USSD services.
- **Features:**
  - User registration.
  - View next collection dates.
  - Make payments via mobile money.
  - Receive SMS notifications.

### **d. Integration Services**

#### **i. Mapping and Routing**

- **Google Maps API:**
  - Geocoding addresses using plus codes.
  - Defining zones using geo polygons.
  - Optimizing routes for collection.
- **Google Earth Engine API:**
  - Utilize satellite imagery to classify building density.
  - Assist in zone creation and density analysis.

#### **ii. Real-time Tracking**

- **GPS Tracking:**
  - Trucks (both Franchise and LISWMC) equipped with smartphones running the driver app.
  - Continuous location updates to the backend.

#### **iii. Messaging Services**

- **SMS Delivery:**
  - Integration with Zamtel APIs for SMS notifications.
- **Push Notifications:**
  - Firebase Cloud Messaging for mobile app users.

#### **iv. Payment Gateways**

- **Mobile Money Integration:**
  - **Phase 1:** MTN Mobile Money, Airtel Money, Zamtel Kwacha.
- **Bank Integrations:**
  - **Planned for Phase 2:** Local bank APIs for direct transfers.
- **Security:**
  - Compliance with PCI DSS standards.
- **Payment Processing:**
  - Secure handling of mobile money transactions in Phase 1.

### **e. Google Earth Engine Integration**

#### **Purpose:**

- To classify zones based on building density, proximity to markets, and other geographical factors.
- Enhance zone creation by providing data-driven insights.

#### **Implementation:**

- **Data Acquisition:**
  - Access satellite imagery and geospatial datasets through Google Earth Engine APIs.
- **Building Classifiers:**
  - Use machine learning algorithms to classify areas based on:
    - Building density.
    - Land use patterns.
    - Proximity to roads and natural barriers.
- **Zone Creation:**
  - Generate geo polygons representing zones.
  - Adjust zones based on classifier outputs for optimal resource allocation.

#### **Benefits:**

- **Efficiency:**
  - More accurate zone definitions leading to better route planning.
- **Scalability:**
  - Automated processes for future expansion or reclassification.
- **Data-Driven Decisions:**
  - Leverage real-time data for continuous improvements.

---

## **Key Features and Functionalities**

### **1. Onboarding Franchise Collectors**

- **Registration Portal:**
  - Collect company details and vital documents (TPIN clearance, PACRA documents, vehicle and office photos).
- **Verification Process:**
  - LISWMC staff review submissions and approve or reject applications.
- **Zone Assignment:**
  - Assign collectors to zones based on capacity and resources.
  - Utilize data from Google Earth Engine classifiers for informed decisions.

### **2. LISWMC Fleet Management**

- **Fleet Registration:**
  - Register LISWMC's own collection vehicles.
  - Input vehicle details, capacity, and status.
- **Scheduling and Dispatching:**
  - Schedule regular collections in zones not covered by franchise collectors.
  - Dispatch vehicles for emergency collections.
- **Real-time Tracking:**
  - Monitor the location and status of LISWMC vehicles.
- **Driver Management:**
  - Assign drivers to vehicles and routes.
  - Track driver performance and compliance.

### **3. Emergency Collection Management**

- **Emergency Requests:**
  - Citizens or staff can submit emergency collection requests.
  - Input description, location, and urgency level.
- **Dispatching:**
  - Assign available LISWMC vehicles to handle emergencies.
  - Provide drivers with necessary information and directions.
- **Status Updates:**
  - Track the progress of emergency collections.
  - Notify requestors upon completion.

### **4. Zone and Route Management**

- **Zone Creation:**
  - Define zones using geo polygons.
  - Use building density classifiers from Google Earth Engine.
- **Route Optimization:**
  - Incorporate collection points and pickup locations.
  - Optimize routes using Google Maps API.
- **Natural Barriers:**
  - Major streets and natural features act as zone boundaries.

### **5. Real-time Truck Tracking**

- **Driver App Features:**
  - GPS tracking enabled for real-time updates.
  - Route guidance and updates.
- **User Notifications:**
  - Citizens receive alerts about truck proximity.
- **Data Handling:**
  - Efficient processing of high-frequency location data.

### **6. Waste Collection Data Estimation**

- **Data Collection:**
  - Record estimated waste collected per pickup point.
  - Input from drivers or sensors.
- **Analytics:**
  - Estimate total waste heading to landfills.
  - Generate reports for planning.

### **7. User Self-Registration and Management**

- **Registration Options:**
  - Mobile app, web application, USSD service.
- **Profile Management:**
  - Update information, add multiple phone numbers.
- **Payment Features:**
  - View balances, make payments via mobile money, receive confirmations.

### **8. Payment Management**

- **Payment Methods:**
  - **Phase 1:** MTN Mobile Money, Airtel Money, Zamtel Kwacha.
  - **Phase 2:** Integration with bank payments.
- **Payment Reminders:**
  - Automated SMS notifications for due payments.
- **Payment Processing:**
  - Secure transactions with real-time status updates.
- **Overdue Accounts:**
  - Visual indicators on maps (e.g., red highlights).
  - Generate lists of overdue accounts.

### **9. Reporting Issues**

- **Uncollected Garbage Reporting:**
  - Users report missed pickups with photos.
- **Illegal Dumping Reporting:**
  - Report incidents with location and images.
- **Issue Management:**
  - Support staff address reports and track resolutions.
- **Emergency Collections:**
  - Reports can trigger emergency collections by LISWMC.

### **10. Franchise Collector User Registration**

- **On-site Registration:**
  - Collectors register users during pickups.
  - Capture location, phone number, plus code, occupants.
- **Data Syncing:**
  - Information syncs with the central database.

### **11. Notifications and Alerts**

- **Customizable Notifications:**
  - Users select preferred channels.
- **Event-based Alerts:**
  - Payment dues, truck approaching, service disruptions.
- **Emergency Notifications:**
  - Alerts for emergency collections or service changes.

### **12. LISWMC Real-time Dashboard**

- **Operational Monitoring:**
  - View active pickups, truck locations, zone performance.
  - Monitor both franchise collectors and LISWMC fleet.
- **Fleet Management:**
  - Manage LISWMC's own vehicles.
  - Schedule and dispatch operations.
- **Financial Overview:**
  - Track payments, visualize paid/unpaid households.
- **Waste Management Analytics:**
  - Estimate daily waste inflow to landfills.
  - Use data from waste estimates and Google Earth Engine.

---

## **Additional Design Considerations**

### **1. Scalability**

- **Microservices Architecture:**
  - Separate services for authentication, payments, tracking.
- **Containerization:**
  - Use Docker and Kubernetes.
- **Load Balancing:**
  - Handle high traffic periods efficiently.

### **2. Security**

- **Data Protection:**
  - Encrypt data in transit and at rest.
- **Authentication:**
  - Strong password policies, two-factor authentication.
- **Compliance:**
  - Adherence to local data protection laws.

### **3. Performance Optimization**

- **Caching:**
  - Use Redis for caching frequently accessed data.
- **Efficient Data Handling:**
  - Batch processing for location updates.
- **Asynchronous Tasks:**
  - Message queues (e.g., RabbitMQ) for non-blocking operations.

### **4. Monitoring and Logging**

- **Application Monitoring:**
  - Tools like Prometheus and Grafana.
- **Log Management:**
  - ELK Stack (Elasticsearch, Logstash, Kibana).
- **Alerting Mechanisms:**
  - System anomaly alerts.

### **5. Backup and Disaster Recovery**

- **Automated Backups:**
  - Regular database backups.
- **Redundancy:**
  - Failover mechanisms.
- **Recovery Plan:**
  - Documented and tested procedures.

### **6. User Experience and Accessibility**

- **Intuitive Interfaces:**
  - User-friendly designs.
- **Multilingual Support:**
  - Local languages (e.g., English, Bemba, Nyanja).
- **Accessibility Features:**
  - Design for users with disabilities.

### **7. Regulatory Compliance**

- **Environmental Reporting:**
  - Compliance with environmental regulations.
- **Financial Compliance:**
  - Auditable financial transactions.

### **8. Integration with Existing Systems**

- **LISWMC Internal Systems:**
  - Integrate with existing fleet management tools if any.
- **Data Sharing:**
  - Ensure seamless data flow between new and existing systems.

---

## **Implementation Plan**

### **Phase 1: Planning and Requirement Analysis**

- **Stakeholder Meetings:**
  - Gather detailed requirements, including fleet management needs.
- **Documentation:**
  - Create requirement specifications.

### **Phase 2: System Design**

- **Architectural Design:**
  - Define system architecture, including fleet management modules.
- **Database Schema Design:**
  - Design database tables and relationships, including new entities.
- **API Design:**
  - Define endpoints and data models.
- **Google Earth Engine Integration:**
  - Plan integration for zone classification.

### **Phase 3: Development**

- **Backend Development:**
  - Set up Go project structure.
  - Implement core services and integrations.
  - Develop fleet management and emergency collection modules.
- **Frontend Development:**
  - Develop mobile and web applications.
  - Design user interfaces, including fleet management dashboards.
- **USSD Service Development:**
  - Implement USSD menus with Zamtel.

### **Phase 4: Integration**

- **Third-party APIs:**
  - Integrate Google Maps, Earth Engine, mobile money payment gateways.
- **Payment Gateway Integration:**
  - **Phase 1:** Implement MTN, Airtel, and Zamtel mobile money.
  - **Phase 2:** Plan for bank payment integration.
- **Testing Integrations:**
  - Ensure seamless service interactions.

### **Phase 5: Testing**

- **Unit Testing:**
  - Test individual components.
- **Integration Testing:**
  - Test combined system parts.
- **System Testing:**
  - Perform end-to-end testing.
- **User Acceptance Testing (UAT):**
  - Feedback from end-users.

### **Phase 6: Deployment**

- **Staging Environment:**
  - Deploy for final testing.
- **Production Deployment:**
  - Move to live environment.

### **Phase 7: Maintenance and Support**

- **Monitoring:**
  - Continuous system performance monitoring.
- **Updates:**
  - Release updates and new features.
  - **Phase 2 Implementation:**
    - Integrate bank payment options.
- **Support:**
  - Provide user support channels.

---

## **Potential Challenges and Mitigations**

### **1. Data Connectivity**

- **Challenge:**
  - Limited internet access.
- **Mitigation:**
  - Offline functionality with data syncing.
  - Optimize data usage.

### **2. Adoption by Franchise Collectors and LISWMC Staff**

- **Challenge:**
  - Resistance to new technology.
- **Mitigation:**
  - Training sessions.
  - Demonstrate operational benefits.

### **3. Accurate Location Data**

- **Challenge:**
  - Inaccurate plus codes or GPS errors.
- **Mitigation:**
  - Data validation steps.
  - Allow manual corrections.

### **4. Emergency Response Coordination**

- **Challenge:**
  - Efficiently handling emergency collections.
- **Mitigation:**
  - Real-time communication tools.
  - Clear protocols and priority systems.

### **5. System Scaling**

- **Challenge:**
  - Handling increased load.
- **Mitigation:**
  - Scalable design.
  - Cloud services for resource scaling.

### **6. Payment Integration**

- **Challenge:**
  - Ensuring secure and seamless payment processing.
- **Mitigation:**
  - Focus on mobile money integration in Phase 1.
  - Plan and allocate resources for bank integration in Phase 2.
  - Regular security audits and compliance checks.

### **7. Integration of Google Earth Engine**

- **Challenge:**
  - Complexity in integrating Earth Engine APIs.
- **Mitigation:**
  - Dedicated team for integration.
  - Utilize existing libraries and tools.

### **8. Fleet Maintenance and Management**

- **Challenge:**
  - Keeping LISWMC vehicles operational.
- **Mitigation:**
  - Implement maintenance schedules.
  - Integrate fleet management tools.

---

## **Conclusion**

The proposed system is a comprehensive solution designed to modernize solid waste management in Lusaka. By integrating advanced technologies like Google Earth Engine for zone density classification and incorporating fleet management for both franchise collectors and LISWMC, the system enhances efficiency and data-driven decision-making. It addresses the needs of all stakeholders and is built with scalability and future enhancements in mind.

The payment system focuses on integrating MTN, Airtel, and Zamtel mobile money platforms in Phase 1 to provide immediate and accessible payment options for users. Bank payment integration is planned for Phase 2, allowing for a phased approach that ensures stability and user adoption.

---

## **Next Steps**

1. **Finalize Requirements:**
   - Review the design with stakeholders for alignment.

2. **Prototype Development:**
   - Create prototypes of key components.

3. **Project Planning:**
   - Develop detailed timelines and resource allocation.

4. **Risk Assessment:**
   - Identify risks and develop mitigation strategies.

5. **Community Engagement:**
   - Begin awareness campaigns and user education.

6. **Pilot Testing:**
   - Implement in a pilot area for data collection and refinement.

7. **Phase 2 Planning:**
   - Begin planning for bank payment integration and any additional features.

---

**Note:** This document serves as a comprehensive guide for the development of the LISWMC platform, including the management of LISWMC's own collection fleet and emergency collections. It reflects the updated payment methods, focusing on mobile money integration in Phase 1 and planning for bank payments in Phase 2. Further details can be expanded upon as the project progresses, and adjustments can be made based on stakeholder feedback and evolving requirements.

---

*For any clarifications or additional information, please feel free to reach out.*