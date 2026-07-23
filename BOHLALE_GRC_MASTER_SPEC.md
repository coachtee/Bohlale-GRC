# Bohlale GRC
## Master Product & Build Specification

**Version:** 0.1 — Foundation Draft
**Date:** 23 July 2026
**Product Type:** Multi-Tenant Governance, Risk, Compliance & Management Systems Platform
**Primary Market:** South African SMEs, NPOs, NGOs, Skills Development Providers and emerging organisations
**Secondary Market:** Independent consultants, compliance practitioners, ISO implementers, internal auditors and GRC professionals

---

## 1. Product Vision

Bohlale GRC is a simple, affordable, AI-assisted Governance, Risk and Compliance platform designed to help organisations implement, operate, maintain and demonstrate compliance without requiring a dedicated GRC department.

The platform combines:

Guided Implementation + Compliance Management + Policy Management + Risk Management + Evidence Management + Audit Readiness + AI Assistance

The fundamental product principle is:

Don't just tell organisations what compliance requires. Guide them through doing it.

Bohlale GRC should be powerful underneath while remaining simple enough that an NPO director, SME owner or junior compliance practitioner can understand the organisation's compliance position within approximately 30 seconds of logging in.

The system must support both:

Consultants and practitioners managing multiple client organisations.
Individual organisations managing their own governance, risk, compliance and management systems.

## 2. Core Problem

Small organisations frequently manage compliance through disconnected tools:

Word Documents
       +
Excel Registers
       +
SharePoint / Google Drive
       +
Email Approvals
       +
PDF Policies
       +
Manual Risk Registers
       +
Consultant Reports
       =
Fragmented Compliance

After a consultant completes an engagement, the organisation may receive folders containing policies, spreadsheets and reports.

These documents often become outdated.

Bohlale GRC transforms this into:

Organisation
      ↓
Bohlale GRC
      ↓
Frameworks & Obligations
      ↓
Policies & Documents
      ↓
Risks & Controls
      ↓
Evidence
      ↓
Registers
      ↓
Incidents
      ↓
Assessments & Audits
      ↓
Actions & Improvements
      ↓
Continuous Compliance

The system becomes the organisation's living compliance workspace.

## 3. Product Positioning

Bohlale GRC is not intended initially to compete directly with large enterprise GRC platforms.

Its primary positioning is:

GRC for organisations that don't have a GRC department.

And:

A guided implementation workspace for practitioners who are still developing their GRC and management-system experience.

The product should bridge the gap between:

spreadsheets;
document repositories;
consulting engagements;
enterprise GRC platforms;
compliance automation;
policy management;
ISO implementation tools.

## 4. Primary Product Modes

### 4.1 Consultant Mode

A consultant can manage multiple organisations.

Example:

THABISO'S CONSULTANT WORKSPACE

My Organisations

NIBS
ISO 27001 Implementation
Progress: 32%

ABC Foundation
POPIA Compliance
Progress: 68%

XYZ NPO
GRC Baseline Assessment
Progress: 44%

Client D
ISO 9001
Progress: 17%

The consultant can switch between organisations without mixing tenant data.

### 4.2 Organisation Mode

An organisation manages its own compliance environment.

Example:

NIBS

Dashboard
Journey
Frameworks
Documents
Risks
Controls
Evidence
Assets
Suppliers
Incidents
Registers
Audits
Actions
Reports
Settings

Users only see information belonging to organisations they are authorised to access.

## 5. Multi-Tenancy

Bohlale GRC must be designed as a multi-tenant application from the beginning.

Core hierarchy:

Platform
   ↓
Consultant / Partner
   ↓
Organisation
   ↓
Users
   ↓
Projects / Management Systems

One consultant may manage many organisations.
One organisation may participate in multiple frameworks.

Example:

NIBS
 ├── ISO/IEC 27001
 ├── POPIA
 ├── King V
 └── Internal Governance Framework

Tenant isolation is mandatory.

No user from Organisation A may access Organisation B's information unless explicitly authorised as a consultant or platform administrator.

## 6. User Roles

Initial roles:

Platform Administrator
Consultant
Organisation Administrator
Executive / Approver
Compliance Manager
ISMS Manager
Control Owner
Risk Owner
Document Owner
Internal Auditor
Contributor
External Reviewer
Read-Only User

Permissions must use role-based access control.

Sensitive actions must be recorded in an immutable audit trail.

## 7. Organisation Onboarding

Creating an organisation should launch a guided onboarding process.

Example:

Welcome to Bohlale GRC.
What would you like to achieve?

Options:

Build a management system from scratch
Conduct a gap assessment
Improve an existing management system
Prepare for an internal audit
Prepare for certification
Assess POPIA compliance
Conduct a GRC baseline assessment
Implement a selected framework
Import a custom framework

The user's selection determines the initial guided journey.

## 8. Guided Implementation Engine

This is a core differentiator.

Bohlale GRC must not simply display requirements.

It must explain:

WHAT IS REQUIRED?

WHY IS IT REQUIRED?

WHAT DO I NEED TO DO?

WHO SHOULD BE INVOLVED?

WHAT QUESTIONS SHOULD I ASK?

WHAT DOCUMENTS MIGHT ALREADY EXIST?

WHAT EVIDENCE SHOULD I LOOK FOR?

WHAT SHOULD I CREATE?

WHO NEEDS TO APPROVE IT?

WHAT DO I DO NEXT?

Every implementation step can have:

description;
guidance;
questions;
required evidence;
recommended evidence;
responsible role;
linked requirements;
linked controls;
linked risks;
linked documents;
completion criteria;
AI assistance.

## 9. PDCA Management-System Model

Management-system journeys should support:

PLAN
 ↓
DO
 ↓
CHECK
 ↓
ACT
 ↓
CONTINUAL IMPROVEMENT

For ISO 27001 this may include:

Plan: context, interested parties, scope, leadership, risk assessment, risk treatment and objectives.
Do: implement controls, operate processes, train people and collect evidence.
Check: monitoring, measurement, internal audit and management review.
Act: corrective actions, nonconformities and continual improvement.

The interface should translate formal management-system concepts into accessible language.

## 10. Organisation Knowledge Profile

Every tenant must have a structured organisational knowledge profile.

This becomes the contextual foundation for AI assistance.

Areas include:

Organisation Profile
Business Activities
Products & Services
Locations
Departments
People & Roles
Processes
Information
Personal Information
Systems
Applications
Assets
Suppliers
Third Parties
Interested Parties
Regulatory Requirements
Contractual Requirements
Existing Policies
Risks
Controls

Information should be classified as:

Verified — confirmed by an authorised user.
AI Inference — suggested by AI but awaiting confirmation.
Missing — required information not yet obtained.

AI must prioritise verified organisational facts.

## 11. AI Guided Interview Engine

The AI assistant should operate inside workflows rather than only as a generic chatbot.

Example:

We need to define your ISMS scope.
I already know that NIBS is a Skills Development Provider.
I need additional information.

The system asks targeted questions.

Example:

Which locations should be included?

Which business processes are included?

Which information systems support these processes?

Are any locations or business units excluded?

Does the organisation use cloud providers?

Who are your key technology suppliers?

What personal information is processed?

Answers update the Organisation Knowledge Profile.

## 12. Information Request Engine

The practitioner may not know every answer.

They can select:

Request Information

Questions can be assigned to stakeholders.

Example:

CEO
 └── Business objectives

IT Manager
 └── Systems and infrastructure

HR Manager
 └── Employee information

Information Officer
 └── POPIA responsibilities

Finance
 └── Financial systems

Recipients may receive secure limited-access questionnaires without requiring access to the entire platform.

Responses return to the relevant implementation step.

## 13. AI Document Generation

AI may assist with drafting documents based on:

verified organisation information;
framework requirements;
approved templates;
user answers;
existing organisational documents.

Example:

ISMS Scope

Information Security Policy

Risk Management Procedure

Access Control Policy

Incident Management Procedure

Supplier Security Policy

The AI workflow must be:

Gather Information
       ↓
Validate Information
       ↓
Generate Draft
       ↓
Human Review
       ↓
Edit / Regenerate
       ↓
Approval
       ↓
Signature
       ↓
Publish

AI-generated content must never automatically become an approved controlled document.

Human approval is mandatory.

## 14. Document & Policy Management

This should be one of Bohlale GRC's strongest features.

Each controlled document should contain:

Document Title
Document Type
Reference Number
Version
Owner
Author
Approver
Approval Date
Effective Date
Next Review Date
Classification
Status
Related Frameworks
Related Requirements
Related Controls
Related Risks
Related Incidents
Attachments
Version History
Audit History

Statuses:

Draft
Under Review
Awaiting Approval
Approved
Published
Superseded
Archived

The dashboard must highlight:

Current
Review Due Soon
Overdue
Awaiting Approval

## 15. Document Version Control

When a document changes:

Version 1.0
    ↓
Change Requested
    ↓
Version 1.1 Draft
    ↓
Review
    ↓
Approval
    ↓
Version 1.1 Published

Previous versions remain available for audit history.

The system records:

who changed it;
when;
why;
what version replaced it.

## 16. Approval & Electronic Sign-Off

Documents may be sent for approval.

Initial native workflow should support:

Approver Name
Approver Role
Approval Decision
Typed Signature / Confirmation
Consent
Timestamp
Document Version
Document Hash
Audit Event

Possible future integration with an open-source or commercial electronic-signature service should remain possible.

## 17. Framework Engine

The framework engine must be framework-agnostic.

Core structure:

Framework
  ↓
Domains / Sections
  ↓
Requirements
  ↓
Controls
  ↓
Assessment Questions
  ↓
Evidence Expectations

Initial target frameworks:

ISO/IEC 27001 management-system implementation structure;
POPIA;
selected South African governance/compliance structures where legally permitted;
custom organisation frameworks.

Additional frameworks should be importable.

Copyrighted standards must not be redistributed without appropriate rights.

## 18. Framework Studio

Authorised users should be able to create or import frameworks.

Possible imports:

PDF
DOCX
XLSX
CSV
Structured JSON

AI may assist in identifying:

framework name;
sections;
requirements;
controls;
evidence expectations;
assessment questions.

AI extraction must produce a draft framework requiring human review.

Workflow:

Upload
 ↓
Analyse
 ↓
Extract
 ↓
Review
 ↓
Correct
 ↓
Approve
 ↓
Publish to Organisation

## 19. Common Control Library

Controls should not necessarily belong exclusively to one framework.

Example:

ACCESS CONTROL
     │
     ├── ISO 27001 Requirement
     ├── POPIA Security Safeguards
     ├── Internal Policy
     └── Client Requirement

Evidence may support multiple mapped requirements.

This reduces duplicated compliance work.

## 20. Assessment Engine

Support:

Gap Assessment
Baseline Assessment
Maturity Assessment
Compliance Assessment
Readiness Assessment
Internal Control Assessment
Custom Assessment

Possible statuses:

Not Assessed
Not Implemented
Partially Implemented
Implemented
Effective
Not Applicable

Every result may include:

rating;
comments;
evidence;
findings;
recommendations;
responsible person;
due date.

## 21. Risk Management

Risk register fields should include:

Risk ID
Title
Description
Category
Asset / Process
Threat
Vulnerability
Likelihood
Impact
Inherent Risk
Existing Controls
Residual Risk
Risk Owner
Treatment
Treatment Owner
Due Date
Status

Treatment options:

Avoid
Mitigate
Transfer
Accept

Risk methodology must be configurable.

## 22. Controls Management

Each control may have:

Control ID
Name
Description
Owner
Implementation Status
Effectiveness
Implementation Notes
Framework Mappings
Risks
Policies
Evidence
Tests
Findings

## 23. Evidence Management

Evidence should be attachable to:

controls;
requirements;
audits;
assessments;
risks;
corrective actions.

Evidence metadata:

Evidence Name
Type
Owner
Upload Date
Validity Period
Expiry Date
Related Control
Related Requirement
Verification Status

## 24. Statement of Applicability

For ISO 27001 projects, support creation and maintenance of an SoA.

Include:

Control
Applicable?
Justification
Implementation Status
Control Owner
Related Risks
Evidence

Export to PDF/Excel should be supported.

## 25. Incident Management

Simple user-facing action:

Report an Incident

Capture:

What happened?
When?
Who discovered it?
Systems affected?
Information affected?
Personal information involved?
Severity?
Immediate actions?

Incidents may trigger:

risk review;
control review;
corrective action;
policy review;
regulatory assessment.

AI may suggest related records requiring review, but a human confirms changes.

## 26. Organisational Change Events

Users should be able to report:

New Employee
Employee Departure
New Supplier
New System
New Office
New Business Process
Policy Change
Security Incident
Data Breach
Regulatory Change

The system should identify potentially affected compliance records.

Example:

A new cloud supplier has been added.

Consider reviewing:

Supplier Register
Risk Register
Operator Register
Information Asset Register

## 27. Registers

The system should support configurable registers.

Initial examples:

Risk Register
Asset Register
Information Asset Register
Supplier Register
Incident Register
Data Breach Register
Corrective Action Register
Interested Parties Register
Legal & Regulatory Register
Processing Activities Register
Training Register
Audit Findings Register

Registers should use the same underlying configurable engine where practical.

## 28. Asset Management

Support:

information assets;
systems;
applications;
hardware;
data repositories.

Assets may link to:

Owner
Classification
Risks
Controls
Suppliers
Processes
Incidents
Evidence

## 29. Supplier Management

Maintain supplier records.

Include:

Supplier
Service
Owner
Criticality
Data Access
Personal Information Access
Risk Rating
Assessment
Contract Review
Review Date

## 30. Audit Management

Support:

Internal Audits
External Audits
Readiness Reviews
Supplier Audits

Audit lifecycle:

Plan
 ↓
Scope
 ↓
Schedule
 ↓
Assign Auditor
 ↓
Conduct
 ↓
Record Evidence
 ↓
Record Findings
 ↓
Corrective Actions
 ↓
Close

## 31. Findings & Corrective Actions

Findings may originate from:

audits;
assessments;
incidents;
risk reviews;
management reviews.

Track:

Finding
Severity
Root Cause
Corrective Action
Owner
Due Date
Evidence
Verification
Closure

## 32. Management Review

Support management-review meetings.

Capture:

meeting date;
attendees;
agenda;
inputs;
decisions;
actions;
approvals;
attachments.

The system should guide the organisation through required management-review inputs for the selected management system.

## 33. Audit Readiness

Readiness should be calculated transparently.

Possible dimensions:

Requirements Completion
Control Implementation
Evidence Coverage
Risk Treatment
Document Approval
Internal Audit Completion
Management Review Completion
Open Major Findings
Corrective Actions

Example:

ISO 27001 Audit Readiness

Requirements          92%
Controls              87%
Evidence              81%
Internal Audit       100%
Management Review    100%
Open Major Gaps         0

Overall Readiness     89%

The platform must not claim to provide certification.

Use terminology such as:

Audit Readiness

or:

Ready to begin certification audit preparation.

## 34. Dashboard

The main dashboard should remain minimal.

Primary cards:

Implementation Progress
Compliance Overview
Open Actions
Risk Overview

Secondary sections:

Implementation Journey
Tasks Due Soon
Upcoming Reviews
Recent Activity
Quick Actions

Quick actions:

Create Document
Report Incident
Request Information
Start Assessment
Upload Evidence
Create Policy

## 35. Reports

Initial reports:

Executive Compliance Summary
Gap Assessment Report
Risk Register
Risk Treatment Plan
Statement of Applicability
Policy Register
Incident Register
Audit Report
Corrective Action Report
Audit Readiness Report
Framework Compliance Report

Export:

PDF
Excel
CSV where appropriate

## 36. Notifications

Notifications for:

overdue actions;
document reviews;
risk reviews;
evidence expiry;
audit dates;
approvals;
assigned questions;
new incidents.

Initial delivery:

In-App
Email

Future:

WhatsApp

## 37. AI Architecture

AI must be provider-independent.

Conceptual architecture:

Bohlale GRC
      ↓
AI Service Layer
      ↓
Provider Adapter
      ├── OpenAI-Compatible API
      ├── Qwen-Compatible Endpoint
      └── Future Providers

AI functionality:

guided interviews;
document drafting;
document review;
framework extraction;
gap explanation;
evidence suggestions;
risk suggestions;
policy improvement;
executive summaries.

AI must not autonomously approve compliance decisions.

## 38. AI Governance

Every AI-generated output must be traceable.

Record:

AI Provider
Model
Generation Date
User
Purpose
Input Context Reference
Output Version
Human Reviewer
Approval Status

Sensitive tenant data must never be used across tenants.

AI prompts must respect tenant boundaries.

## 39. Technical Architecture

Preferred stack:

Python
Django
PostgreSQL
HTMX
HTML
CSS
Minimal JavaScript

Architecture:

Django Modular Monolith

No mandatory:

Docker
Kubernetes
Redis
Microservices
Node build pipeline

unless technically justified later.

Local development may support SQLite.

Production uses PostgreSQL.

## 40. Suggested Django Modules

core
accounts
organisations
tenancy
projects
frameworks
journeys
knowledge
ai
documents
approvals
assessments
risks
controls
evidence
assets
suppliers
incidents
registers
audits
actions
reviews
reports
notifications
activity

Modules remain part of one Django project.

## 41. Deployment

Primary deployment model:

GitHub
   ↓
VPS Staging
   ↓
Nginx
   ↓
Gunicorn
   ↓
Django
   ↓
PostgreSQL

Docker must be optional.

Required deployment assets:

requirements.txt
.env.example
migration instructions
static-file instructions
Gunicorn configuration
Nginx example
deployment documentation
backup instructions

## 42. Development Workflow

Cloud Coding Environment
        ↓
GitHub
        ↓
VPS Staging
        ↓
Browser Testing
        ↓
Production

The Git repository is the source of truth.

Production must not be directly edited by AI coding agents.

## 43. Continuous AI Coding Protocol

Repository must contain:

BOHLALE_GRC_MASTER_SPEC.md
BUILD_STATUS.md
README.md
CHANGELOG.md

The coding agent must:

Read the Master Specification.
Inspect existing code.
Read BUILD_STATUS.md.
Run existing tests.
Identify incomplete requirements.
Continue implementation.
Test completed work.
Update BUILD_STATUS.md.
Commit stable progress.
Continue without asking permission after each module.

If interrupted by usage limits, the next session resumes from repository state.

Never restart the project unless explicitly instructed.

## 44. Definition of Done

A feature is not complete merely because database models exist.

A feature should include, where applicable:

Database Model
Migrations
Business Logic
Permissions
Views
URLs
Templates
Forms
Validation
Tenant Isolation
Audit Logging
Tests
User Interface
Error Handling
Documentation

## 45. Security Requirements

Minimum requirements:

secure authentication;
password hashing;
CSRF protection;
secure sessions;
tenant isolation;
role-based permissions;
audit logging;
secure file uploads;
file type validation;
environment-based secrets;
rate limiting where appropriate;
secure production configuration;
HTTPS;
database backups.

The prototype must use fictional data until security and tenant isolation have been validated.

## 46. UI Design System

Bohlale design philosophy:

Minimal. Calm. Professional. Understandable.

Primary visual direction:

White
Black
Grey
Thin Borders
Clear Typography
Simple Icons
Minimal Colour

Colour should mainly communicate status:

Green  = Good / Complete
Amber  = Attention
Red    = Critical / Overdue
Grey   = Inactive / Unknown

Avoid:

unnecessary gradients;
excessive animations;
cluttered dashboards;
technical terminology without explanation.

The user should always understand:

Where am I?
What needs attention?
What should I do next?

## 47. Reference Demonstration: NIBS

Demo tenant:

Naleli Innovators Business School — NIBS

Scenario:

Create NIBS
     ↓
Select:
Build an ISMS from Scratch
     ↓
Select:
ISO/IEC 27001
     ↓
Organisation Interview
     ↓
Request Missing Information
     ↓
Build Organisation Knowledge Profile
     ↓
Generate Draft ISMS Scope
     ↓
Human Review
     ↓
Executive Approval
     ↓
Electronic Sign-Off
     ↓
Publish Controlled Scope
     ↓
Continue Implementation
     ↓
Identify Missing Information Security Policy
     ↓
AI Guided Policy Interview
     ↓
Generate Draft
     ↓
Review
     ↓
Approve
     ↓
Publish
     ↓
Perform Risk Assessment
     ↓
Select Applicable Controls
     ↓
Build SoA
     ↓
Upload Evidence
     ↓
Internal Audit
     ↓
Management Review
     ↓
Corrective Actions
     ↓
Audit Readiness

This scenario must eventually work end-to-end.

## 48. Commercial Model

Bohlale GRC should support consulting-led deployment.

Example:

GRC Setup Engagement
        +
Organisation Workspace
        +
Initial Assessment
        +
Policies
        +
Registers
        +
Client Access

Possible future models:

One-Time Setup
Annual Maintenance
Monthly Compliance Support
Consultant Subscription
Managed GRC Service

Pricing logic will be determined after market research.

The product should remain accessible to resource-constrained South African organisations.

## 49. Competitive Research Still Required

Before freezing Version 1.0, conduct structured research into:

Eramba;
CISO Assistant;
Vanta;
Drata;
Secureframe;
Sprinto;
OneTrust;
policy-management platforms;
audit-management platforms;
South African GRC/compliance products;
open-source GRC repositories.

For each:

Product
Target Market
Pricing
Core Features
Best Feature
Why Customers Pay
Weaknesses
User Complaints
Open Source?
License
Architecture
Deployment Complexity
Reusable Concepts
Bohlale Opportunity

This research should inform, but not cause direct copying of proprietary products.

## 50. Product Principle

The ultimate goal is that an organisation does not receive compliance as a static folder.

Instead:

Consultant completes engagement
             ↓
Organisation receives Bohlale GRC
             ↓
Policies remain managed
             ↓
Risks remain active
             ↓
Registers remain current
             ↓
Incidents can be reported
             ↓
Evidence remains organised
             ↓
Reviews are scheduled
             ↓
Compliance continues

The organisation should be able to say:

"This is where we manage our governance, risk and compliance."

The practitioner should be able to say:

"This is where I manage my clients and guide them from assessment to implementation and ongoing compliance."

And the system should always answer three questions:

Where are we?
What needs attention?
What should we do next?

## Status of this specification

Version 0.1 is the foundation specification—not yet the final coding prompt.

The next revision should be v0.2 Competitive Intelligence Edition, where we conduct deep research into the reference products and GitHub repositories you're going to provide. We should then update this specification with the strongest capabilities we discover, define the complete database entity model and screen map, and only then freeze v1.0.

After v1.0, we produce the separate BOHLALE_GRC_MASTER_BUILD_PROMPT.md. That is the document we give Claude in the cloud environment with instructions to build continuously until the entire specification is implemented, using BUILD_STATUS.md to survive usage limits and resume exactly where it stopped.

---

## Appendix A — Build Implementation Notes (added during implementation)

This appendix records build-time decisions made where the specification above was intentionally high-level. These are documented assumptions per the working instructions ("if a requirement is unclear but does not prevent safe implementation, make a sensible documented assumption and continue"). See `BUILD_STATUS.md` for the live, authoritative list of assumptions and current build state.
