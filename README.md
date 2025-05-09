# 3PL Workflow Automation

A workflow automation system for Third-Party Logistics (3PL) operations, streamlining the end-to-end process from sales order to delivery using a clear, role-based process model. Designed to integrate seamlessly with ERP systems like Frappe/ERPNext or be adapted into other platforms.

## 🚀 Features

- Full 3PL cycle: Sales Order → Pick List → Delivery Note → Freight Processing → Invoice
- Distinct roles and approvals: Sales, Stores, Logistics, Billing
- Custom document flows and status tracking
- Automated notifications and handovers
- Supports multiple delivery partners and customers
- Integrated freight charge reconciliation and billing

## 📦 Workflow Overview

### 1. **Sales Team**
- Create Sales Order (Customer + Items)
- Submit for processing

### 2. **Stores**
- Generate Pick List
- Hand over goods to 3PL partner

### 3. **Logistics (3PL Partner)**
- Receive goods and generate Delivery Note
- Manage freight movement and logistics milestones

### 4. **Billing**
- Reconcile freight and logistics charges
- Generate Invoice to Customer
- Link to Purchase Invoice (for freight from vendors)

### 5. **Admin**
- Oversee approvals and document linkage
- Track delivery and billing completion
