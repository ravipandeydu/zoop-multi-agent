# Multi-Agent Orchestration System for FNOL Claim Management

## **Background**

First Notice of Loss (FNOL) is a critical process in insurance claim management where initial claim information is captured, validated, and routed for processing. Your task is to build a proof-of-concept multi-agent system that demonstrates intelligent agent coordination for FNOL processing.

## **Business Context**

An insurance company needs to automate their FNOL process to:

- Reduce manual data entry errors
- Accelerate claim processing time
- Improve fraud detection
- Provide real-time visibility into claim status

## **Core Requirements**

### **1. Multi-Agent System**

Implement **3 specialized agents** and an orchestrator:

### **Required Agents:**

**a. Intake Agent**

- Parse incoming claim data (JSON/text format)
- Extract key information: claim type, date, amount, description
- Validate data completeness
- Output: Structured claim object

**b. Risk Assessment Agent**

- Analyze claim for fraud indicators (implement 3-5 simple rules)
- Calculate risk score (1-10)
- Categorize as: Low/Medium/High risk
- Output: Risk assessment report

**c. Routing Agent**

- Determine claim processing path based on type and risk
- Assign priority level
- Select appropriate adjuster tier
- Output: Routing decision

**d. Orchestrator Agent**

- Coordinate the flow between agents
- Handle inter-agent communication
- Manage parallel vs sequential execution
- Implement basic error handling
- Log workflow progress

### **2. Simple Dashboard**

Create a basic web interface showing:

**Required Views:**

- **Live Claim Processing**: Show a claim moving through the agent pipeline
- **Agent Status**: Display which agent is currently processing
- **Results Summary**: Show the final output from each agent
- **Basic Metrics**: Total claims processed, average processing time

**Technical Simplifications:**

- Can use mock/simulated data
- Dashboard can be basic React
- Real-time updates via polling (WebSockets optional)
- No authentication required

## **Technical Specifications**

### **Minimum Requirements:**

- **Language**: any language accepted
- **Agent Communication**: Simple message passing (can use function calls, queues, or HTTP)
- **LLM Integration**
- **Database**: In-memory or SQLite is sufficient
- **Deployment**: Local development environment only

## **Deliverables**

### **1. Working Code**

- Functional multi-agent system with 3 agents + orchestrator
- Basic dashboard with live processing view
- Sample data processing demonstration
- README with setup and run instructions

### **2. System Design**

- Simple architecture diagram (1 page)
- Agent interaction flow chart
- Brief explanation of orchestration strategy (500 words max)

### **3. Demo Video**

- 3-5 minute screen recording
- Show claim processing through the system
- Demonstrate agent coordination
- Display dashboard updates

## **Evaluation Criteria**

### **Core Functionality (40%)**

- Agents work independently and produce correct outputs
- Orchestrator successfully coordinates agent execution
- System processes claims end-to-end

### **Agent Orchestration (30%)**

- Clear communication between agents
- Appropriate use of parallel/sequential processing
- Error handling for agent failures

### **Code Quality (20%)**

- Clean, readable code
- Logical organization
- Basic error handling

### **Innovation (10%)**

- Creative approach to agent coordination
- Efficient processing strategies
- Useful insights in dashboard

## **Provided Resources**

Sample Dataset attached

## **Bonus Points (If Time Permits)**

- Add a 4th agent (e.g., Documentation Agent)
- Implement retry logic for failed agents
- Add claim queuing mechanism
- Create multiple processing strategies (fast-track vs. detailed)
- Include simple metrics/analytics

## **Tips for Success**

1. **Start Simple**: Get basic agents working before adding complexity
2. **Mock When Needed**: Use hardcoded rules instead of complex logic
3. **Focus on Orchestration**: This is the key skill being evaluated
4. **Dashboard Can Be Basic**: A simple HTML page with JavaScript is perfectly acceptable
5. **Document Assumptions**: Explain your design decisions briefly

## Sample Data
    
```json
{
  "claims": [
        {
          "claim_id": "CLM-2024-001",
          "type": "auto_collision",
          "date": "2024-01-15",
          "amount": 2500,
          "description": "Minor fender bender in parking lot",
          "customer_id": "CUST-123",
          "policy_number": "POL-789-ACTIVE",
          "incident_location": "123 Main St, Springfield",
          "police_report": null,
          "injuries_reported": false,
          "other_party_involved": true,
          "timestamp_submitted": "2024-01-15T14:30:00Z",
          "customer_tenure_days": 1095,
          "previous_claims_count": 0
        },
        {
          "claim_id": "CLM-2024-002",
          "type": "property_damage",
          "date": "2024-01-10",
          "amount": 8500,
          "description": "Water damage from burst pipe in basement",
          "customer_id": "CUST-456",
          "policy_number": "POL-234-ACTIVE",
          "incident_location": "456 Oak Ave, Riverside",
          "police_report": null,
          "injuries_reported": false,
          "other_party_involved": false,
          "timestamp_submitted": "2024-01-12T09:15:00Z",
          "customer_tenure_days": 2190,
          "previous_claims_count": 1
        },
        {
          "claim_id": "CLM-2024-003",
          "type": "auto_theft",
          "date": "2024-01-14",
          "amount": 35000,
          "description": "Vehicle stolen from driveway overnight",
          "customer_id": "CUST-789",
          "policy_number": "POL-567-NEW",
          "incident_location": "789 Elm St, Downtown",
          "police_report": "RPT-2024-234",
          "injuries_reported": false,
          "other_party_involved": false,
          "timestamp_submitted": "2024-01-14T07:45:00Z",
          "customer_tenure_days": 25,
          "previous_claims_count": 0,
          "_test_note": "HIGH RISK - New policy with high-value claim"
        },
        {
          "claim_id": "CLM-2024-004",
          "type": "auto_collision",
          "date": "2024-01-13",
          "amount": 15000,
          "description": "Hit and run, no witnesses",
          "customer_id": "CUST-111",
          "policy_number": "POL-888-ACTIVE",
          "incident_location": "Unknown location",
          "police_report": null,
          "injuries_reported": true,
          "other_party_involved": false,
          "timestamp_submitted": "2024-01-14T22:30:00Z",
          "customer_tenure_days": 180,
          "previous_claims_count": 3,
          "_test_note": "HIGH RISK - Multiple red flags"
        },
        {
          "claim_id": "CLM-2024-005",
          "type": "property_damage",
          "date": null,
          "amount": 4500,
          "description": "Storm damage to roof",
          "customer_id": "CUST-222",
          "policy_number": "POL-999-ACTIVE",
          "incident_location": "",
          "police_report": null,
          "injuries_reported": false,
          "other_party_involved": false,
          "timestamp_submitted": "2024-01-16T11:00:00Z",
          "customer_tenure_days": 730,
          "previous_claims_count": 1,
          "_test_note": "INCOMPLETE - Missing date and location"
        },
        {
          "claim_id": "CLM-2024-006",
          "type": "auto_glass",
          "date": "2024-01-16",
          "amount": 500,
          "description": "Windshield crack from road debris",
          "customer_id": "CUST-333",
          "policy_number": "POL-321-ACTIVE",
          "incident_location": "Highway 101",
          "police_report": null,
          "injuries_reported": false,
          "other_party_involved": false,
          "timestamp_submitted": "2024-01-16T13:20:00Z",
          "customer_tenure_days": 1825,
          "previous_claims_count": 2,
          "_test_note": "LOW PRIORITY - Simple glass claim"
        },
        {
          "claim_id": "CLM-2024-007",
          "type": "liability",
          "date": "2024-01-12",
          "amount": 50000,
          "description": "Customer injured on property premises",
          "customer_id": "CUST-444",
          "policy_number": "POL-654-ACTIVE",
          "incident_location": "Business premises",
          "police_report": "RPT-2024-567",
          "injuries_reported": true,
          "other_party_involved": true,
          "timestamp_submitted": "2024-01-13T08:00:00Z",
          "customer_tenure_days": 3650,
          "previous_claims_count": 0,
          "_test_note": "URGENT - Liability with injury"
        },
        {
          "claim_id": "CLM-2024-008",
          "type": "auto_collision",
          "date": "2024-01-17",
          "amount": 7500,
          "description": "Multi-vehicle accident on highway",
          "customer_id": "CUST-555",
          "policy_number": "POL-987-ACTIVE",
          "incident_location": "I-495 Mile 42",
          "police_report": "RPT-2024-890",
          "injuries_reported": false,
          "other_party_involved": true,
          "timestamp_submitted": "2024-01-17T16:45:00Z",
          "customer_tenure_days": 900,
          "previous_claims_count": 1,
          "_test_note": "STANDARD - Normal collision claim"
        },
        {
          "claim_id": "CLM-2024-009",
          "type": "flood",
          "date": "2024-01-11",
          "amount": 125000,
          "description": "Severe flood damage to entire first floor",
          "customer_id": "CUST-666",
          "policy_number": "POL-135-ACTIVE",
          "incident_location": "Flood zone area",
          "police_report": null,
          "injuries_reported": false,
          "other_party_involved": false,
          "timestamp_submitted": "2024-01-12T06:30:00Z",
          "customer_tenure_days": 4380,
          "previous_claims_count": 0,
          "_test_note": "HIGH VALUE - Requires senior adjuster"
        },
        {
          "claim_id": "CLM-2024-010",
          "type": "auto_collision",
          "date": "2024-01-18",
          "amount": 1,
          "description": "Test claim",
          "customer_id": "CUST-777",
          "policy_number": "POL-246-ACTIVE",
          "incident_location": "Test location",
          "police_report": null,
          "injuries_reported": false,
          "other_party_involved": false,
          "timestamp_submitted": "2024-01-18T23:59:00Z",
          "customer_tenure_days": 60,
          "previous_claims_count": 5,
          "_test_note": "SUSPICIOUS - $1 claim with history of multiple claims"
        },
        {
          "claim_id": "CLM-2024-011",
          "type": "auto_comprehensive",
          "date": "2024-01-19",
          "amount": 3200,
          "description": "Vandalism - car keyed in parking garage",
          "customer_id": "CUST-888",
          "policy_number": "POL-357-ACTIVE",
          "incident_location": "Downtown parking garage",
          "police_report": "RPT-2024-901",
          "injuries_reported": false,
          "other_party_involved": false,
          "timestamp_submitted": "2024-01-19T10:20:00Z",
          "customer_tenure_days": 550,
          "previous_claims_count": 0
        },
        {
          "claim_id": "CLM-2024-012",
          "type": "property_damage",
          "date": "2024-01-20",
          "amount": 18500,
          "description": "Fire damage in kitchen",
          "customer_id": "CUST-999",
          "policy_number": "POL-468-ACTIVE",
          "incident_location": "789 Pine St, Westside",
          "police_report": "RPT-2024-902",
          "injuries_reported": false,
          "other_party_involved": false,
          "timestamp_submitted": "2024-01-20T15:45:00Z",
          "customer_tenure_days": 15,
          "previous_claims_count": 0,
          "_test_note": "HIGH RISK - New customer with significant claim"
        },
        {
          "claim_id": "CLM-2024-013",
          "type": "auto_collision",
          "date": "2024-01-21",
          "amount": 5500,
          "description": "Rear-ended at traffic light",
          "customer_id": "CUST-100",
          "policy_number": "POL-579-ACTIVE",
          "incident_location": "Market St & 2nd Ave",
          "police_report": "RPT-2024-903",
          "injuries_reported": false,
          "other_party_involved": true,
          "timestamp_submitted": "2024-01-21T11:30:00Z",
          "customer_tenure_days": 2555,
          "previous_claims_count": 1
        },
        {
          "claim_id": "CLM-2024-014",
          "type": "medical_payment",
          "date": "2024-01-22",
          "amount": 12000,
          "description": "Medical expenses from auto accident",
          "customer_id": "CUST-200",
          "policy_number": "POL-680-ACTIVE",
          "incident_location": "County Hospital",
          "police_report": "RPT-2024-904",
          "injuries_reported": true,
          "other_party_involved": true,
          "timestamp_submitted": "2024-01-22T09:00:00Z",
          "customer_tenure_days": 1460,
          "previous_claims_count": 0,
          "_test_note": "URGENT - Medical claim requiring immediate attention"
        },
        {
          "claim_id": "CLM-2024-015",
          "type": "auto_collision",
          "date": "2024-01-23",
          "amount": 9999,
          "description": "Side collision at intersection",
          "customer_id": "CUST-300",
          "policy_number": "POL-791-ACTIVE",
          "incident_location": "5th St & Broadway",
          "police_report": null,
          "injuries_reported": false,
          "other_party_involved": true,
          "timestamp_submitted": "2024-01-23T14:15:00Z",
          "customer_tenure_days": 45,
          "previous_claims_count": 2,
          "_test_note": "SUSPICIOUS - Just under $10k, no police report, multiple claims"
        }
      ],
      "test_scenarios": {
        "happy_path": ["CLM-2024-001", "CLM-2024-008", "CLM-2024-011", "CLM-2024-013"],
        "high_risk_fraud": ["CLM-2024-003", "CLM-2024-004", "CLM-2024-010", "CLM-2024-012", "CLM-2024-015"],
        "incomplete_data": ["CLM-2024-005"],
        "urgent_priority": ["CLM-2024-007", "CLM-2024-014"],
        "high_value": ["CLM-2024-009"],
        "simple_claims": ["CLM-2024-006"],
        "batch_test": ["CLM-2024-001", "CLM-2024-002", "CLM-2024-003", "CLM-2024-004", "CLM-2024-005"]
      },
      "validation_rules": {
        "required_fields": [
          "claim_id",
          "type",
          "date",
          "amount",
          "description",
          "customer_id",
          "policy_number",
          "incident_location",
          "timestamp_submitted"
        ],
        "optional_fields": [
          "police_report",
          "injuries_reported",
          "other_party_involved",
          "customer_tenure_days",
          "previous_claims_count"
        ]
      },
      "expected_outputs": {
        "CLM-2024-001": {
          "risk_level": "LOW",
          "priority": "normal",
          "adjuster_tier": "standard"
        },
        "CLM-2024-003": {
          "risk_level": "HIGH",
          "priority": "urgent",
          "adjuster_tier": "fraud_specialist"
        },
        "CLM-2024-005": {
          "risk_level": "MEDIUM",
          "priority": "normal",
          "adjuster_tier": "standard",
          "validation_errors": ["missing_date", "missing_location"]
        },
        "CLM-2024-007": {
          "risk_level": "LOW",
          "priority": "urgent",
          "adjuster_tier": "senior"
        }
      }
    }
    
```