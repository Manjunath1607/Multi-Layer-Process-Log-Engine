# Multi-Layer Process Log Engineering Framework

## Overview

This project provides an automated framework to transform raw operational datasets into structured **Case Logs** and **Event Logs** compatible with enterprise process mining platforms such as Celonis and SAP Signavio.

The engine eliminates manual Power Query transformations and automates duplicate handling, event sequencing, and variant generation.

---

## Architecture Design

The framework follows a structured multi-layer architecture:

1. **Data Ingestion Layer**
   - Supports CSV and Excel files
   - Drag-and-drop upload via Jupyter widget

2. **Duplicate Cleansing Layer**
   - Automatically removes records with Disposition = "Duplicate Incident"
   - Prevents artificial recurrence and cycle-time inflation

3. **Case Structuring Layer**
   - Generates standardized Case Log
   - Deduplicates Case IDs
   - Preserves governance attributes (Partner, Tier, Domain)

4. **Event Sequencing Layer**
   - Converts wide timestamp columns into structured event log format
   - Supports:
     - Incident Created
     - L1 → L2 transition
     - Escalation to L3
     - Incident Closed
   - Sorts events chronologically

5. **Variant Intelligence Layer**
   - Generates activity path per case
   - Enables conformance and process pattern analysis

---

## Key Features

- Automatic column standardization
- Duplicate incident elimination
- Case Log generation
- Event Log generation
- Variant path construction
- Cycle time computation
- Mining-ready CSV export

---

## Output Files

- `final_case_log.csv`
- `final_event_log.csv`

Both files are compatible with:

- Celonis
- SAP Signavio Process Intelligence
- Any BPMN-based process mining tool

---

## Technology Stack

- Python
- Pandas
- NumPy
- Jupyter Notebook

---

## Business Impact

This framework reduces manual data preparation effort by approximately 60–70% and enables scalable, repeatable event-log engineering for enterprise process intelligence initiatives.

---

## Use Cases

- Seller Support Operations
- Claims Processing
- Escalation & SLA Governance
- Recurrence Analysis
- Process Conformance

---

## Author

Manjunath K S  
Process Intelligence & Business Transformation
