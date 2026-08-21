# Compliance Guardrails — ArthaInvest Capital

*ARN-267891 · IRDAI POSP (PolicyBoss) · TATA & Niva Bupa agency · DSA via corporate DSA*

Read this once. Everything in `04_Outreach_Kit.md` is already written to comply with it.
This is a practical operating guide, not legal advice — for anything contentious, check with
your AMC/insurer compliance desk or a lawyer.

---

## 1. The three rules that matter most

1. **Never promise or imply a return.** No "guaranteed", "assured", "safe 12%", "will double".
   Not in email, not on WhatsApp, not verbally.
2. **Never contact someone you have no consent for without first asking permission.**
   Your first touch to a cold record asks for permission; it does not pitch.
3. **Log every opt-out immediately in `suppression_list.csv`, and never contact them again.**

---

## 2. DPDP Act 2023 — the lead lists

The `data dump\` lists came from a friend in real estate. You have **no consent chain** for them:
those people gave their details to a property developer, for a property enquiry, not to you,
and not for financial services marketing.

**What this means practically:**

| Do | Don't |
|---|---|
| Make first contact permission-seeking, with a clear opt-out | Open with a product pitch |
| State plainly where you got their details | Pretend it's a warm intro |
| Honour any "don't contact me" instantly and permanently | Try a different channel after a refusal |
| Keep only what you need, for as long as you need it | Re-share the lists with anyone else |

**Two ignored touches = treat as a refusal.** Move them to `suppression_list.csv`. This is both
the compliant position and the commercially sensible one — a third unanswered email never converts.

You are the entity deciding how this personal data is used, so the obligations sit with you,
not with the friend who sent the file.

---

## 3. TRAI TCCCPR — calling and messaging

- **NDNC / DND scrub before dialling.** Numbers on the Do Not Disturb registry must not receive
  promotional calls. Unsolicited commercial calls from an unregistered sender attract penalties
  and can get the number disconnected.
- **Promotional SMS/WhatsApp broadcast** requires DLT-registered headers and pre-approved
  templates. A personal one-to-one WhatsApp message to someone who has already engaged with you
  is a different thing from a bulk broadcast — keep it one-to-one and conversational.
- **Email is the lowest-risk first channel**, which is exactly why the `START HERE` sheet is
  filtered to people who have an email address. Always include a working unsubscribe line.

**Time windows:** keep calls to 09:00–21:00. Never call on a number a person has asked you not to use.

---

## 4. AMFI / SEBI — mutual fund communication

- Disclose **ARN-267891** and the name **ArthaInvest Capital** on MF material.
- Carry the standard risk line: *"Mutual Fund investments are subject to market risks, read all
  scheme related documents carefully."*
- **No performance promises.** Past performance is not indicative of future returns, and should
  not be the headline of any outreach.
- Don't name a specific scheme as a recommendation in cold outreach. Talk about the *conversation*
  (a review, a plan, a goal), not the product.

### The distributor / adviser line — worth being deliberate about

As an **ARN distributor** you earn commission and may give advice that is *incidental* to
distribution. **Charging a separate fee for financial planning** is the territory of a SEBI
**Registered Investment Adviser (RIA)**, which is a different registration.

Your pipeline uses the label **"FWP"** (financial/wealth plan) as a stage. That's fine as a
service you provide around distribution. Just be careful not to market yourself as a fee-charging
independent adviser unless you hold RIA registration. If you intend to charge planning fees,
get that checked before you advertise it.

---

## 5. IRDAI — insurance communication

- **Name the insurer** (TATA AIG / TATA AIA / Niva Bupa) in any product-specific material.
  Don't market a policy as "ArthaInvest's plan".
- As a **POSP**, you may solicit only the specified simple products your certification covers.
  Stay inside that list.
- No misleading claims about claim ratios, coverage or tax benefits. Tax treatment depends on
  the individual and the prevailing law — say so.
- Never suggest surrendering or replacing an existing policy without a clear, documented reason
  that benefits the client.

---

## 6. Mandatory footer

Put this on every outbound email. It is already in every template in the outreach kit.

```
ArthaInvest Capital · AMFI Registered Mutual Fund Distributor · ARN-267891
Insurance solicited as an IRDAI-licensed POSP. Insurer: TATA / Niva Bupa as applicable.

Mutual Fund investments are subject to market risks, read all scheme related documents
carefully. Past performance is not indicative of future returns. This message is for
information only and is not investment advice or an offer to buy or sell any security.
Insurance is the subject matter of solicitation.

You received this because your details were shared with us in connection with a property
enquiry. If you'd rather not hear from us, reply "STOP" and we'll remove you permanently.
```

> Adjust the last paragraph per audience — for existing clients and referrals, replace it with
> the actual source of the relationship. Never state a source that isn't true.

---

## 7. Records to keep

Keep these for at least five years. If a complaint or audit ever lands, this is your defence.

- `suppression_list.csv` — every opt-out, with date and channel
- The `Consent` and `Touch1_Date` columns in `02_Master_Prospect_DB.xlsx`
- Anything a client signed: KYC, FATCA, risk profile, the `forms\` pack
- A note of what you recommended and why, especially where insurance replaced something existing

---

## 8. Quick self-check before you hit send

- [ ] Does this promise or imply a return? → rewrite
- [ ] Does it name a specific scheme as a recommendation to a cold contact? → rewrite
- [ ] Is the recipient on `suppression_list.csv`? → don't send
- [ ] Is this a cold record getting a pitch instead of a permission ask? → rewrite
- [ ] Is the ARN + risk disclaimer footer present? → add it
- [ ] For insurance: is the insurer named? → add it
- [ ] Calling: is it between 09:00 and 21:00, and is the number DND-scrubbed? → check
