---
name: loan-prospecting
description: Find and rank loan prospects (LAP, Home, Business, Project, OD, CC) from the CRM's raw leads and the local prospecting engine spreadsheets, matched to the right loan product. Trigger phrases - "find loan prospects", "who should I prospect today", "loan prospecting", "new loan leads".
---

# Loan Prospecting

Finds loan-fit prospects from two sources - the live CRM and the local prospecting spreadsheets - and produces a ranked call list matched to a loan product, not a generic contact list.

## Data sources

1. **CRM leads** - `GET https://arthainvest-crm.onrender.com/api/leads?token=<token>&status=New`
   Log in first: `POST /api/auth/login {"username": "...", "password": "..."}` to get the token.
2. **Local prospecting engine** - `prospecting/02_Master_Prospect_DB.xlsx` (the full universe), `prospecting/11_ICP_Lists.xlsx` (who actually fits), `prospecting/14_Warm_Network.xlsx` (existing relationships - always prioritize these first, warm beats cold). Read with the `xlsx` skill or pandas, not by hand.

## Loan products in this CRM

`LAP` (Loan Against Property), `Home`, `Business`, `Project`, `OD` (Overdraft), `CC` (Cash Credit) - these are the exact `loan_product` values `POST /api/deals` accepts. Don't invent other labels.

## Workflow

1. Pull CRM leads with `status=New` and cross-reference against the Warm Network sheet first - anyone already there gets called before a cold Master Prospect DB entry, regardless of loan size.
2. For each remaining prospect, infer a loan-product fit from what's known about them (owns property / mentions a business / mentions a home purchase / needs working-capital language) - don't guess a product with zero signal, mark it "needs qualifying call" instead.
3. Rank: warm network > recent inbound (WhatsApp/website source) > cold DB, and within each tier, larger inferred ticket size first (bigger LAP/Business deals are worth calling before small ones, given capacity is the binding constraint - see the business profile memory).
4. Cap the list to what's actually callable today (check `arthainvest-business-profile.md` memory for current capacity) - a list of 40 that never gets called is worse than 8 that do.
5. For each prospect on the final list: name, phone, one-line reason they're ranked here, and the loan product to open the call with.
6. Offer to create them as CRM leads (`POST /api/leads`) if they aren't already in the system, and to hand the list to the `telecalling` skill to actually place calls.

## What this skill does NOT do

Doesn't create deals or dial numbers itself - hands off to `telecalling` for that. Doesn't do credit assessment - that's `credit-manager`, and happens after a prospect is qualified, not before.
