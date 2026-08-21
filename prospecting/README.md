# ArthaInvest — Prospecting Engine

Built 2026-08-02 from the files already in `C:\Users\artha\OneDrive\Desktop\ArthaInvest`.
**No original file was modified** — verified by MD5 comparison in `build\90_verify.ps1`.

---

## The finding

You do not have a lead shortage.

| | |
|---|---|
| Unique contactable people across your lead files | **11,466** |
| Rows in your actual worked pipeline | **12** |
| Existing clients | **27** |
| Clients with health or life cover on file | **0** |

11,466 contacts produced a 12-row pipeline. The constraint is triage and follow-up, not volume.
Your telecaller worked those lists cold and produced nothing — which is the expected result:
they're third-party property-enquiry records, the people raised their hand about a *flat*, and
there was no relationship or consent behind the call.

So this engine does two things: it cuts 11,466 down to a workable few hundred, and it points you
first at the people who already trust you.

---

## Work in this order

### 1. `01_Client_Gap_Matrix.xlsx` ← start here
Your 27 existing clients, ₹48.8L tracked AUM, ₹88,000/month SIP book. You hold AMFI ARN + TATA +
Niva Bupa + POSP + a DSA code — but **every one of the 27 shows no health or life cover on file**.
That's revenue with zero acquisition cost and no consent problem.

Also includes a **Referral Asks** sheet and an **Insurance Tracker Seed** pre-filled in the exact
EBIX/TATA column format, since those trackers are currently empty templates.

### 2. `03_Pipeline_CRM.xlsx`
Your 12 live prospects, with real stages, next actions and next-action dates. Two things it surfaces:

- **All 12 have no phone or email on file.** Four already have a plan shared with them. Recovering
  those contact details is the highest-value hour available to you.
- **DBS gave 4 leads and SCB gave 4** — 8 of 12 came from bankers, and 5 of 12 are NRIs. That
  channel is working with no systematic effort behind it.

### 3. `02_Master_Prospect_DB.xlsx`
11,466 people, deduplicated and scored. Work the **START HERE** sheet — 120 Tier A people who have
an email address, so the first touch can be a value-first email with an unsubscribe. That's about
8 weeks at 15 touches a week.

| Sheet | Rows | What it is |
|---|---|---|
| START HERE | 120 | Tier A with email — your working list |
| Tier A - Qualified | 258 | Full qualified pool |
| Tier B - Nurture | 2,330 | Lower priority |
| Channel Partners | 220 | Real-estate brokers — a B2B referral route, not retail prospects |
| Confirmed Buyers | 21 | People who actually purchased a flat — highest intent in the file |
| Tier C - Archive | 8,878 | Kept for audit only. **Do not call.** |

### 4. `04_Outreach_Kit.md`
Templates per segment, all compliance-checked. The key change: **email → WhatsApp → call**, the
reverse of what the telecaller did. Includes objection handling and disposition codes.

### 5. `05_Weekly_Cadence.md`
5 referral asks · 15 warm touches · 1 content touchpoint · 1 pipeline review. ~3–4 hours a week,
sized so it survives a bad week. Includes the 90-day arc across all four of your target segments —
sequenced, not run in parallel.

### 6. `06_Compliance_Guardrails.md`
DPDP 2023 (the lists came from a friend — no consent chain), TRAI TCCCPR (DND scrub, DLT for bulk),
AMFI/SEBI and IRDAI rules. Includes the mandatory footer and a pre-send checklist.

### 7. `07_Loan_Prospects.xlsx`
Loans scored separately, because loan approval rewards *provable income* (salaried + named
employer) and *collateral*, not wealth. Best sheets first:

| Sheet | Rows | What |
|---|---|---|
| 1. Confirmed Buyers | 29 | Bought flats Feb 2021 — agreement value and booking date known. **~₹39.8cr of loan book in play.** ~5.5 years into a 20-year loan = prime balance-transfer window |
| 2. Live Loan Enquiries | 15 | Already raised a loan need with you |
| 3. Loan Prospects A–B | 3,094 | Scored for loan intent (511 Tier A) |
| 4. Client Cross-Sell | 27 | Every client, no loan on file |
| 5. Broker Channel | 220 | Your source of *fresh* loan leads |

Messages pre-written in `outbox\F_loan_balance_transfer.csv` and `G_loan_broker_channel.csv`.
**DSA rule:** never promise approval, a rate, or a saving — the lender decides. Verified by the build.

### 8. `08_Fresh_Lead_Sources.md`
Every dated record in your files is from 2018/2020/2021 — **nothing since**, and the files were
last touched in early 2024. Mining that database is a one-off harvest, not a pipeline. This
covers the five sources that produce genuinely new, consented leads, ranked.

### 9. `09_Dashboard.html` ← everything in one screen
Double-click to open in your browser. Works offline, no internet needed, nothing to install.
Eight tabs: Overview, Leverage, Clients, Pipeline, Loans, Cold list, Brokers, This week.
Every table is searchable and sortable — click a column header.

**Two findings the dashboard surfaces that the spreadsheets don't:**

- **BARC — 16 prospects, plus "Anushakti Nagar" in your top localities.** One employer *and* one
  residential colony: salaried government scientists in the same place. The best single FinRakshak
  session target you have, and session attendees are first-party consented leads.
- **Two of your eight lists carry all the value.** One Marina averages 35.9 with 9.5% Tier A.
  Runwal (2,561), book 4 (1,792) and 2.xlsx (481) produce **zero** Tier A between them — they're
  name+phone only, with nothing to qualify on.

> Deliberately **not** published to a web address. It contains names, mobiles, emails and PANs of
> real people — hosting that would be the same DPDP problem this engine exists to avoid.

### 10. `suppression_list.csv`
Opt-outs. Check before every send; add to it immediately. This is your audit defence.

### `outbox\` — 476 personalised messages, none sent
Ready to review and send yourself. See `WEEK_1_ACTION_PLAN.md` for what goes out when.

---

## Rebuilding

If new lead lists arrive, drop them in `data dump\` and re-run in order:

```bash
powershell -ExecutionPolicy Bypass -File "prospecting\build\10_extract.ps1"
```
```bash
powershell -ExecutionPolicy Bypass -File "prospecting\build\20_score.ps1"
```
```bash
powershell -ExecutionPolicy Bypass -File "prospecting\build\30_client_gap.ps1"
```
```bash
powershell -ExecutionPolicy Bypass -File "prospecting\build\40_pipeline_crm.ps1"
```
```bash
powershell -ExecutionPolicy Bypass -File "prospecting\build\90_verify.ps1"
```

Tune `$TierACut` at the top of `20_score.ps1` to grow or shrink the working list.

---

## Known limitations — read these

- **"NOT TRACKED" ≠ uninsured.** Your EBIX/TATA files are empty templates, so the matrix can only
  say *no policy is recorded*. Confirm in conversation before advising anyone to buy cover.
- **~65 international numbers** were detected from country codes. A handful look like data errors
  (e.g. `+116157080355`). Eyeball before dialling.
- **Client name matching is fuzzy.** "Ashish Dhakite" was merged with "AASHISH RAMESH DHAKITE" on
  a surname + near-spelling match. Correct for 27 clients; re-check if the book grows a lot.
- **`book 4.xlsx` and `Micl Ghatkopar- book 4.xlsx`** are near-identical (both 1,827 rows, different
  hashes). Deduplication is on mobile number, so this doesn't inflate counts.
- **Budget bands come from property enquiries**, and are a proxy for wealth, not a verified figure.
- **Tier C is not a backlog to get to.** It is largely junk-marked, nameless or stale records,
  retained only so the archive is auditable.
