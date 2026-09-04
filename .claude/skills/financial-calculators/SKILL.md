---
name: financial-calculators
description: Points to the right existing calculator/tool file for a client conversation - SIP, SWP, retirement corpus, health insurance comparison, life insurance need, tax regime, rent vs buy, and more. These are real local Excel/PDF tools already built, not something to recreate. Trigger phrases - "which calculator should I use", "SIP calculator", "retirement calculator", "financial calculators".
---

# Financial Calculators

A lookup, not a rebuild - these tools already exist on this machine and are the ones to actually open/use in a client meeting, not something to recreate from scratch in the CRM.

## Where they live

`C:\Users\artha\OneDrive\Desktop\Business\07 Calculators & Tools\Calculators\` - general planning tools:

| File | Use for |
|---|---|
| `10 Personal Finance Thumb Rules.xlsx` | Quick sanity-check rules in a first meeting |
| `All About SIP.xlsx` | SIP education/illustration for a prospect new to MF |
| `Annual Review Meeting Checklist.xlsx` | Structuring a client's yearly portfolio review |
| `Comparison of Health Insurance Features.xlsx`, `EBIX HEALTH INSURANCE COMPARISION.xlsx` | Side-by-side health policy comparison |
| `Data Collection Sheet for Making Financial Plans.xlsx` | Intake form for a new financial-planning client |
| `FINANCIAL PLANNING MAP.xlsm`, `MAP.xlsm` | Full financial plan mapping |
| `FIRE Number Calculator.pdf` | Early-retirement corpus target |
| `Financial Organiser.xlsx` | General client financial snapshot |
| `IRR CALCI.xlsx`, `IRR CALCUTAION.xlsx` | Internal rate of return on a specific investment |
| `Life Insurance Calculator.xlsx` | Sum-assured need calculation |
| `Master XLFP Lite.xls` | Lightweight financial-plan template |
| `NRI Investments - The Complete Tool.xlsx` | NRI-specific investment guidance |
| `Old vs New Tax Regime.pdf` | Tax regime comparison conversation |
| `Portfolio and Plan Review Template.xls` | Structured portfolio review writeup |
| `ProTool - Mutual Fund Selection Parameters.xlsx` | Fund-selection criteria walkthrough |
| `Rent vs Buy Home.xlsx`, `Renting vs Buying a House.xlsx` | Home-purchase decision support |
| `Retirement Corpus Building.xlsx`, `Retirement Income Streams Calculator.xlsx` | Retirement planning |
| `SIP Sales Presenter (1).pptx` | Client-facing SIP pitch deck |
| `SIP to foreclose EMI on Home Loan.xlsx` | Cross-sell angle: SIP sized to prepay a home loan |
| `tax calculator and tracker.xlsx` | Tax planning/tracking |

`C:\Users\artha\OneDrive\Desktop\Business\02 Mutual Funds\SWP & SIP\` - SWP/SIP specific:
- `SWP - EQUITY AND DEBT FUND.xlsx`, `SWP- DEBT FUND.xlsx`, `SWP- LIQUID FUND.xlsx` - fund-category-specific systematic withdrawal illustrations.
- `Mutual-Fund-SWP-Calculator-Report*.xlsx` (multiple numbered copies) - these look like saved output reports from prior client runs, not blank templates - check the most recently modified one if starting a fresh calculation, or open by name if it's for a specific known client.

## Workflow

1. Match the client conversation to the right tool from the table above rather than guessing - if unsure which of two similar tools (e.g. `IRR CALCI.xlsx` vs `IRR CALCUTAION.xlsx`) is the current one, open both and check which has a real formula/recent edit vs which looks abandoned.
2. Open the file directly (via the `xlsx` skill for Excel files, or a PDF viewer for the two PDFs) rather than trying to reproduce its logic manually - these are purpose-built, don't recreate them.
3. If a genuinely new type of calculation is needed that none of these cover, say so rather than forcing an existing tool to fit - offer to build a new one instead of stretching e.g. the SIP calculator into an EMI calculator.

## Web-based versions, when a quick online calculator is faster than opening a file

For a rough number during a call (not a formal client illustration), AMFI India and Value Research both host free SIP/lumpsum calculators; see the `mf-research` skill for the fuller source list. For loan EMI, see `loan-research`; for insurance premium quotes, see `insurance-research`.
