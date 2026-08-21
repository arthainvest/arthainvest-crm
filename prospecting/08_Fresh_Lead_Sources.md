# Fixing the stale-data problem at source

You said the list on the laptop isn't updated. You're right, and it's worth seeing how badly:

| Enquiry year | Records |
|---|---|
| 2018 | 1,047 |
| 2020 | 16 |
| 2021 | 1,905 |
| **2022 – 2026** | **0** |

The lead files were last touched in **early 2024**. It is now **August 2026**. Another 8,625
records carry no date at all, so their age is unknown but almost certainly the same era.

**What this means honestly:** mining that database is a *one-off harvest*, not a pipeline. Even
if every message lands, you exhaust it and you're back where you started. Expect heavy phone
disconnection too — 5–8 year old mobile numbers churn a lot. That is normal and not a sign the
list was bad.

So the database work is worth doing once, and then the real job is building **flow**.

---

## What I can't do for you

I can't source new leads from outside your own files. Scraping or buying personal data would put
you straight back into the DPDP problem you already have with the real-estate lists — no consent
chain, no lawful basis, and a suppression list that grows faster than your pipeline.

Every source below produces leads where **the person chose to engage with you**. That's what
makes them both compliant and worth more.

---

## The five sources that produce fresh leads, ranked

### 1. Real-estate brokers — 220 of them, already in your files
**This is the single best answer to "my list is old."**

Sheet 5 of `07_Loan_Prospects.xlsx` and `outbox\G_loan_broker_channel.csv` (message pre-written).

Brokers close property deals every month. Every buyer they close needs a home loan **that month**,
and needs cover on a large new EMI. You hold a DSA code and a POSP licence. One broker
relationship produces fresh loan leads indefinitely.

- A 2021 lead list is a harvest. A broker channel is an annuity.
- You don't need 220. You need **5 who actually send you business**.
- Start with the ones whose firm name is filled in — they're real agencies, not one-off entries.

**Effort:** 5 WhatsApp messages a week. **Payoff:** compounding.

### 2. The bankers already sending you business — DBS and SCB
They gave you **8 of your 12 current prospects** with no systematic effort. This is proven flow
that nobody is maintaining.

`outbox\C_referral_partners.csv` is written. You need to fill in the RM contacts.

**Effort:** one thank-you and one ask per month. **Payoff:** your highest-quality leads, and the
NRI segment you convert best in.

### 3. Your 27 existing clients
The only people who have already paid you. Referral asks are in `outbox\B_client_referral_asks.csv`.
None of them has a loan on file either — sheet 4 of `07_Loan_Prospects.xlsx`.

**Effort:** 5 asks a week. **Payoff:** highest conversion of any channel, no compliance risk.

### 4. Sessions — housing societies, clinics, one employer
You already own the decks: `finrakshak session ppt.pptx`, `MedMoney - MGM.pptx`,
`MONEY MINDFULLNESS-ARTHAINVEST.pdf`.

Everyone who attends and leaves their details is a **first-party consented lead** — the DPDP
problem disappears entirely, because they gave the data to you, for this purpose.

- One society session ≈ 30 people in a room who chose to be there.
- Ask the society committee, or a doctor you already know, or one HR manager.

**Effort:** one session a month. **Payoff:** 20–30 clean leads plus local reputation.

### 5. Your own digital presence
The slowest to start and the only one that works while you sleep. One post a week on the topics
you already have decks for. Not a priority while sources 1–4 are unworked.

---

## What to actually do

| | Source | Weekly effort |
|---|---|---|
| **Now** | Harvest the old database once — confirmed buyers, live enquiries, START HERE list | Already prepared |
| **Now** | Brokers (5/week) + bankers (monthly) | ~30 min |
| **Ongoing** | Client referral asks | ~30 min |
| **Month 2** | Book one session | ~2 hrs, once |
| **Later** | Content | — |

**The test:** by October, are new names arriving without you mining a spreadsheet? If yes, the
stale-data problem is solved permanently. If no, the harvest just bought you a few months.

---

## Keeping it from going stale again

Two habits, both about five minutes:

1. **Log every new lead the day it arrives** in `03_Pipeline_CRM.xlsx` — with source, date and a
   next action. Not in your phone, not in a notebook.
2. **Re-run the build when new lists arrive.** Drop files in `data dump\` and run the scripts in
   `prospecting\build\` in order. The engine rebuilds itself; it doesn't need rewriting.

The reason this database aged out isn't that the leads were bad. It's that nothing was capturing
new ones. Fix the capture and the ageing stops being a problem.
