# Aeon DCF Engine

**Complete Equity Valuation — DCF · WACC/CAPM · 3-Way Sensitivity · Peer Comps · Football Field · Reverse DCF**

*LiJie Guo · Aeon Nimbus Research · lijieguo.substack.com · [LinkedIn](https://www.linkedin.com/in/lijieguo-es/)*

---

## Overview

A full-cycle discounted cash flow model implemented in Python, covering every stage of the institutional valuation workflow: cost of capital derivation via CAPM with country risk premium, free cash flow projection from operating assumptions, terminal value estimation, sensitivity analysis across a WACC-by-growth matrix, peer relative valuation, football field synthesis, and reverse DCF. Pre-loaded with a live case study in **VNET Group (VNET)**, a Chinese hyperscale data centre operator and a structural beneficiary of the AI infrastructure build-out in Asia.

```bash
python main.py
```

Press Enter to accept the VNET defaults, or substitute your own assumptions. No external dependencies.

---

## Methodology

### Cost of Capital — WACC and CAPM

The discount rate applied to projected cash flows must reflect the full risk of the capital structure. The cost of equity is derived via the Capital Asset Pricing Model, extended with an emerging markets country risk premium following the Damodaran methodology:

```
Ke   = Rf + β × ERP + CRP
Kd   = pre-tax borrowing cost (weighted average coupon)
WACC = Ke × (E/V) + Kd × (1 − tax rate) × (D/V)
```

Each component carries a specific economic interpretation. The risk-free rate Rf represents the time value of money in a world without default or uncertainty, conventionally proxied by the US 10-year Treasury yield. Beta captures the systematic (non-diversifiable) component of the firm's return variability relative to the market portfolio — the only risk that demands compensation in a CAPM framework, because idiosyncratic risk can be eliminated through diversification. The equity risk premium ERP is the expected excess return of the aggregate market over the risk-free rate, typically estimated at 4.5–6.0% for US markets. For emerging market issuers, the country risk premium CRP adds a spread calibrated from sovereign CDS levels to compensate for political and institutional risks not captured by beta. The after-tax cost of debt reflects the interest tax shield, which reduces the effective cost of borrowed capital under corporate taxation.

### Free Cash Flow Projection

Unlevered free cash flow — the cash flow available to all capital providers before financing costs — is constructed from operating assumptions for each projection year:

```
Revenue_t    = Revenue_{t-1} × (1 + g_t)
EBITDA_t     = Revenue_t × margin_t              (margin expands to Y5 target)
NOPAT_t      = (EBITDA_t − D&A_t) × (1 − tax)
UFCF_t       = NOPAT_t + D&A_t − CapEx_t − ΔNWC_t
PV(UFCF_t)   = UFCF_t / (1 + WACC)^t
```

The use of UFCF rather than equity free cash flow is deliberate: discounting at WACC requires a cash flow measure that is independent of financing structure. UFCF strips out interest expense and captures what the business generates purely from operations, making it comparable across firms with different leverage profiles.

### Terminal Value

For most going-concern businesses, the terminal value represents 60–90% of enterprise value — a proportion that both underscores its importance and should prompt scepticism about the precision of DCF outputs. Two methods are implemented:

- **Exit Multiple:** TV = Y5 EBITDA × exit EV/EBITDA multiple. Anchors the terminal value in current market multiples, which some practitioners prefer for its empirical grounding.
- **Gordon Growth Model:** TV = UFCF_Y5 × (1+g) / (WACC − g). Theoretically cleaner but acutely sensitive to the assumed perpetual growth rate g, which must remain below long-run nominal GDP growth to be economically credible.

```
Enterprise Value  = Σ PV(UFCF_t) + PV(Terminal Value)
Equity Value      = Enterprise Value − Net Debt
Implied Price     = Equity Value ÷ Shares Outstanding
```

### Sensitivity Analysis

Because a DCF is a model of assumptions rather than a prediction of outcomes, the sensitivity table is arguably more informative than the base case price. A 7×6 matrix maps implied share prices across WACC (±200bp from base) and terminal growth rate (±200bp from base). This converts the DCF from a single point estimate into a conditional distribution — the range of outcomes consistent with different states of the world.

Professional investors do not read DCFs to find the "right" price. They read them to understand the asymmetry of outcomes: how much upside exists in a bull scenario relative to the downside in a bear scenario, and which variables are most sensitive in driving that spread.

### Peer Comparables

Relative valuation grounds the intrinsic analysis in market reality. EV/EBITDA and EV/Revenue multiples from comparable public companies are applied to the subject firm's projected financials to derive market-implied prices. The multi-method average — DCF, EV/EBITDA peer, EV/Revenue peer — is more robust than any single approach, and the football field chart visualises the range of implied prices across all methods simultaneously.

### Reverse DCF

Rather than asking what a company is worth, the reverse DCF inverts the question: what assumptions must hold for the current stock price to represent fair value? This is often the more productive analytical framing, because it shifts the burden of proof. Instead of asserting "the stock is worth X," the analyst demonstrates "the stock is priced for Y multiple, and here is why that is either too pessimistic or too optimistic."

```
Implied EV      = Market Cap + Net Debt
Implied TV      = Implied EV − PV(projected FCFs)
Implied Multiple = Implied TV ÷ Y5 EBITDA
```

If the market-implied exit multiple is materially below a well-reasoned base case, the stock offers a margin of safety. If it exceeds the base case, the market is priced for an outcome that requires the business to execute without error across every dimension — a structurally asymmetric short risk.

---

## Why This Matters

The DCF model occupies an unusual position in professional equity analysis: it is simultaneously the most widely used and the most widely abused framework in fundamental investing. Its abuse stems from treating the output price as a prediction. Its value lies in what the process reveals — the explicit, testable assumptions that underlie a position.

A senior PM reviewing a research note will not evaluate the price target first. They will ask: what WACC did you use, and how sensitive is the output to that choice? What terminal multiple, and is it anchored to comparable transaction history? What margin trajectory are you assuming, and what is the operating leverage mechanism that gets you there? The sensitivity table, football field, and reverse DCF are the tools that answer these questions with rigour.

The VNET case study is chosen deliberately. Emerging markets AI infrastructure is a sector where the market narrative and the financial fundamentals are in tension — high capital intensity, long payback periods, and sovereign risk interact with structural demand tailwinds from GPU compute build-out. Valuing it forces every assumption to earn its place.

---

## Example Output

```
════════════════════════════════════════════════════════════════
  AEON DCF ENGINE — VNET Group (VNET)
════════════════════════════════════════════════════════════════

  WACC / CAPM:
  ─────────────────────────────────────────────────────────────
  Risk-free rate (Rf)       :  4.69%
  Beta × ERP                :  7.98%   (β=1.45 × ERP=5.50%)
  Country risk premium      :  1.80%
  Cost of equity (Ke)       : 14.47%
  After-tax cost of debt    :  5.40%   (7.20% × (1−25%))
  Capital structure         :  82% equity / 18% debt
  WACC                      : 12.84%

  DCF PROJECTION TABLE ($M):
  ─────────────────────────────────────────────────────────────
  Metric            Y1        Y2        Y3        Y4        Y5
  Revenue        1,605     1,910     2,254     2,592     2,800
  EBITDA margin  31.1%     32.3%     33.5%     34.7%     36.0%
  EBITDA           499       617       754       899     1,008
  UFCF             (89)       42       183       310       391
  PV of UFCF       (79)       33       127       190       213

  PV of FCFs (Y1–Y5)   :  $484M
  Terminal Value        :  $10,080M  (10.0x Y5 EBITDA)
  PV of Terminal Value  :  $5,491M   (91.9% of EV)
  Enterprise Value      :  $5,975M
  Equity Value          :  $4,135M
  Implied share price   :  $15.37
  Upside vs $10.51      :  +46.2%

  SENSITIVITY — Implied Share Price
  ─────────────────────────────────────────────────────────────
  WACC \ TG     1.5%    2.5%    3.5%    4.0%    4.5%    5.0%
  10.84%         $19     $21     $23     $25     $27     $29
  12.84%         $14     $15     $17     $18     $19     $21  ← BASE
  14.84%         $10     $11     $12     $13     $14     $15

  REVERSE DCF:  Current $10.51 implies exit multiple of 5.7×
                vs base case 10.0× — market pricing a significant
                discount to fundamental fair value
```

---

*LiJie Guo · Aeon Nimbus Research · lijieguo.substack.com · [LinkedIn](https://www.linkedin.com/in/lijieguo-es/)*
