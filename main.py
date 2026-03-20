"""
Aeon DCF Engine — Complete Valuation Engine
============================================
Implements WACC/CAPM, 5-Year DCF, Sensitivity Analysis, Peer Comparables,
Football Field, Reverse DCF, and Scenario Analysis.

Uses Python standard library only (math, statistics).
"""

import math
import statistics


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def prompt_float(label: str, default: float) -> float:
    raw = input(f"  {label} [{default}]: ").strip()
    return float(raw) if raw else default


def prompt_int(label: str, default: int) -> int:
    raw = input(f"  {label} [{default}]: ").strip()
    return int(raw) if raw else default


def prompt_str(label: str, default: str) -> str:
    raw = input(f"  {label} [{default}]: ").strip()
    return raw if raw else default


def separator(char: str = "=", width: int = 78) -> None:
    print(char * width)


def section(title: str) -> None:
    separator()
    print(f"  {title}")
    separator()


def fmt_m(value: float, decimals: int = 1) -> str:
    """Format value in millions with suffix."""
    return f"${value:,.{decimals}f}M"


def fmt_b(value: float, decimals: int = 2) -> str:
    """Format value in billions."""
    return f"${value / 1000:,.{decimals}f}B"


def fmt_pct(value: float, decimals: int = 1) -> str:
    return f"{value * 100:.{decimals}f}%"


def fmt_x(value: float, decimals: int = 1) -> str:
    return f"{value:.{decimals}f}x"


def fmt_price(value: float) -> str:
    return f"${value:.2f}"


# ---------------------------------------------------------------------------
# 1. WACC / CAPM
# ---------------------------------------------------------------------------

def compute_wacc(rf: float, erp: float, beta: float, crp: float,
                 kd: float, tax_rate: float, debt_weight: float) -> dict:
    """
    CAPM: Ke = Rf + Beta * ERP + CRP
    After-tax cost of debt: Kd_AT = Kd * (1 - tax_rate)
    WACC = Ke * equity_weight + Kd_AT * debt_weight
    All rates as decimals (e.g., 0.0469 for 4.69%).
    """
    equity_weight = 1.0 - debt_weight
    ke = rf + beta * erp + crp
    kd_at = kd * (1.0 - tax_rate)
    wacc = ke * equity_weight + kd_at * debt_weight
    return {
        "ke": ke,
        "kd_at": kd_at,
        "wacc": wacc,
        "equity_weight": equity_weight,
        "debt_weight": debt_weight,
    }


# ---------------------------------------------------------------------------
# 2. DCF Model
# ---------------------------------------------------------------------------

def run_dcf(rev0: float, growth_rates: list, ebitda_margin_0: float,
            ebitda_margin_5: float, da0: float, capex_rev_pct_y5: float,
            tax_rate: float, wacc: float, net_debt: float,
            shares: float, exit_multiple: float, terminal_growth: float) -> dict:
    """
    5-year unlevered free cash flow DCF.

    Parameters
    ----------
    rev0            : TTM revenue ($M)
    growth_rates    : list of 5 annual revenue growth rates (decimal)
    ebitda_margin_0 : current EBITDA margin (decimal)
    ebitda_margin_5 : Y5 target EBITDA margin (decimal)
    da0             : current D&A ($M); grows 8% per year
    capex_rev_pct_y5: CapEx as % of revenue in Y5 (decimal)
    tax_rate        : corporate tax rate (decimal)
    wacc            : WACC (decimal)
    net_debt        : net debt ($M)
    shares          : shares outstanding (millions)
    exit_multiple   : EV/EBITDA exit multiple
    terminal_growth : Gordon Growth Model terminal growth rate (decimal)
    """
    years = list(range(1, 6))
    revenues = []
    ebitda_margins = []
    ebitdas = []
    das = []
    ebits = []
    nopats = []
    capexes = []
    wcs = []
    delta_wcs = []
    ufcfs = []
    pv_ufcfs = []

    prev_rev = rev0
    prev_wc = rev0 * 0.02  # WC = 2% of revenue

    for i, yr in enumerate(years):
        g = growth_rates[i]
        rev = prev_rev * (1.0 + g)
        revenues.append(rev)

        # Linear interpolation of EBITDA margin from Y0 to Y5
        margin = ebitda_margin_0 + (ebitda_margin_5 - ebitda_margin_0) * (yr / 5.0)
        ebitda_margins.append(margin)

        ebitda = rev * margin
        ebitdas.append(ebitda)

        # D&A grows 8% per year from da0
        da = da0 * (1.08 ** yr)
        das.append(da)

        ebit = ebitda - da
        ebits.append(ebit)

        nopat = ebit * (1.0 - tax_rate)
        nopats.append(nopat)

        # CapEx: linearly interpolate from Y1 CapEx% to Y5 target
        # We'll use a simple assumption: CapEx scales with a linear path from
        # current CapEx (as % of initial rev) down to Y5 target.
        # We'll compute current capex pct from the inputs implicitly via
        # building it from Y5 target only — the engine lets user pass Y5 capex pct.
        # For years 1-4 we hold CapEx% constant at a level that reaches y5 target.
        # Simpler convention: CapEx% linearly interpolates from Y1 (same as y5 target
        # for simplicity unless caller overrides). We expose capex_rev_pct_y5 only.
        capex_pct = capex_rev_pct_y5  # use single pct for all years (user-supplied)
        capex = rev * capex_pct
        capexes.append(capex)

        wc = rev * 0.02
        wcs.append(wc)
        delta_wc = wc - prev_wc
        delta_wcs.append(delta_wc)

        ufcf = nopat + da - capex - delta_wc
        ufcfs.append(ufcf)

        # Discount factor: (1 + WACC)^year
        df = (1.0 + wacc) ** yr
        pv_ufcfs.append(ufcf / df)

        prev_rev = rev
        prev_wc = wc

    # Terminal Value via Exit Multiple
    tv_exit = ebitdas[-1] * exit_multiple
    pv_tv_exit = tv_exit / ((1.0 + wacc) ** 5)

    # Terminal Value via Gordon Growth Model (for reference)
    if wacc > terminal_growth:
        tv_ggm = ufcfs[-1] * (1.0 + terminal_growth) / (wacc - terminal_growth)
        pv_tv_ggm = tv_ggm / ((1.0 + wacc) ** 5)
    else:
        tv_ggm = None
        pv_tv_ggm = None

    sum_pv_ufcf = sum(pv_ufcfs)
    ev_exit = sum_pv_ufcf + pv_tv_exit
    equity_value_exit = ev_exit - net_debt
    price_exit = equity_value_exit / shares if shares > 0 else 0.0

    if pv_tv_ggm is not None:
        ev_ggm = sum_pv_ufcf + pv_tv_ggm
        equity_value_ggm = ev_ggm - net_debt
        price_ggm = equity_value_ggm / shares if shares > 0 else 0.0
    else:
        ev_ggm = None
        equity_value_ggm = None
        price_ggm = None

    return {
        "years": years,
        "revenues": revenues,
        "ebitda_margins": ebitda_margins,
        "ebitdas": ebitdas,
        "das": das,
        "ebits": ebits,
        "nopats": nopats,
        "capexes": capexes,
        "wcs": wcs,
        "delta_wcs": delta_wcs,
        "ufcfs": ufcfs,
        "pv_ufcfs": pv_ufcfs,
        "sum_pv_ufcf": sum_pv_ufcf,
        "tv_exit": tv_exit,
        "pv_tv_exit": pv_tv_exit,
        "tv_ggm": tv_ggm,
        "pv_tv_ggm": pv_tv_ggm,
        "ev_exit": ev_exit,
        "equity_value_exit": equity_value_exit,
        "price_exit": price_exit,
        "ev_ggm": ev_ggm,
        "equity_value_ggm": equity_value_ggm,
        "price_ggm": price_ggm,
    }


def print_dcf_table(d: dict, net_debt: float, shares: float) -> None:
    section("5-YEAR DCF MODEL")

    col_w = 12
    label_w = 28

    header = f"{'':>{label_w}}" + "".join(f"{'Y' + str(y):>{col_w}}" for y in d["years"])
    print(header)
    separator("-", label_w + col_w * 5)

    def row(label, values, fmt_fn):
        line = f"{label:>{label_w}}" + "".join(f"{fmt_fn(v):>{col_w}}" for v in values)
        print(line)

    row("Revenue ($M)", d["revenues"], lambda v: fmt_m(v, 0))
    row("EBITDA Margin", d["ebitda_margins"], lambda v: fmt_pct(v))
    row("EBITDA ($M)", d["ebitdas"], lambda v: fmt_m(v, 0))
    row("D&A ($M)", d["das"], lambda v: fmt_m(v, 0))
    row("EBIT ($M)", d["ebits"], lambda v: fmt_m(v, 0))
    row("NOPAT ($M)", d["nopats"], lambda v: fmt_m(v, 0))
    row("CapEx ($M)", d["capexes"], lambda v: fmt_m(v, 0))
    row("Delta WC ($M)", d["delta_wcs"], lambda v: fmt_m(v, 0))
    separator("-", label_w + col_w * 5)
    row("UFCF ($M)", d["ufcfs"], lambda v: fmt_m(v, 0))
    row("PV of UFCF ($M)", d["pv_ufcfs"], lambda v: fmt_m(v, 0))

    separator("-", label_w + col_w * 5)
    print(f"\n  {'Sum PV of UFCFs:':<30} {fmt_m(d['sum_pv_ufcf'])}")
    print(f"  {'Terminal Value (Exit Mult.):':<30} {fmt_m(d['tv_exit'])}")
    print(f"  {'PV of TV:':<30} {fmt_m(d['pv_tv_exit'])}")
    print(f"  {'Enterprise Value (EV):':<30} {fmt_m(d['ev_exit'])}")
    print(f"  {'Less: Net Debt:':<30} {fmt_m(net_debt)}")
    print(f"  {'Equity Value:':<30} {fmt_m(d['equity_value_exit'])}")
    print(f"  {'Shares Outstanding (M):':<30} {shares:.1f}M")
    print(f"  {'Implied Share Price:':<30} {fmt_price(d['price_exit'])}")
    if d["price_ggm"] is not None:
        print(f"  {'Implied Price (GGM TV):':<30} {fmt_price(d['price_ggm'])}")


# ---------------------------------------------------------------------------
# 3. Sensitivity Analysis
# ---------------------------------------------------------------------------

def sensitivity_analysis(base_wacc: float, rev0: float, growth_rates: list,
                         ebitda_margin_0: float, ebitda_margin_5: float,
                         da0: float, capex_rev_pct_y5: float, tax_rate: float,
                         net_debt: float, shares: float,
                         exit_multiple: float) -> None:
    section("SENSITIVITY ANALYSIS — Implied Share Price")
    print("  Rows: WACC  |  Columns: Exit Multiple\n")

    wacc_deltas = [-0.02, -0.01, 0.00, +0.01, +0.02, +0.03, +0.04]
    exit_multiples = [8.0, 9.0, 10.0, 11.0, 12.0, 14.0]

    col_w = 10
    label_w = 12

    # Header row
    header = f"{'WACC \\ EV/EBITDA':>{label_w}}"
    for em in exit_multiples:
        header += f"{fmt_x(em):>{col_w}}"
    print(header)
    separator("-", label_w + col_w * len(exit_multiples))

    for dw in wacc_deltas:
        w = base_wacc + dw
        label = fmt_pct(w)
        marker = " <--" if dw == 0.00 else ""
        line = f"{label:>{label_w}}"
        for em in exit_multiples:
            result = run_dcf(rev0, growth_rates, ebitda_margin_0, ebitda_margin_5,
                             da0, capex_rev_pct_y5, tax_rate, w, net_debt, shares,
                             em, 0.035)
            p = result["price_exit"]
            cell = fmt_price(p)
            line += f"{cell:>{col_w}}"
        line += marker
        print(line)

    print()
    print("  Note: WACC sensitivity uses exit multiple as the column driver.")
    print("        Arrow (<--) marks the base-case WACC row.")


# ---------------------------------------------------------------------------
# 4. Peer Comparables
# ---------------------------------------------------------------------------

PEERS = [
    {
        "name": "GDS Holdings",
        "ticker": "GDS",
        "ev_ebitda": 14.1,
        "ev_rev": 1.22,
        "rev_growth": 0.194,
        "ebitda_margin": 0.338,
        "fcf_yield": 0.032,
    },
    {
        "name": "Chindata Group",
        "ticker": "CNDT",
        "ev_ebitda": 13.8,
        "ev_rev": 1.18,
        "rev_growth": 0.162,
        "ebitda_margin": 0.341,
        "fcf_yield": 0.028,
    },
    {
        "name": "Equinix (US)",
        "ticker": "EQIX",
        "ev_ebitda": 22.4,
        "ev_rev": 4.81,
        "rev_growth": 0.083,
        "ebitda_margin": 0.422,
        "fcf_yield": 0.019,
    },
    {
        "name": "Digital Realty (US)",
        "ticker": "DLR",
        "ev_ebitda": 18.9,
        "ev_rev": 3.42,
        "rev_growth": 0.101,
        "ebitda_margin": 0.387,
        "fcf_yield": 0.024,
    },
]


def peer_comps(rev_ttm: float, ebitda_ttm: float, net_debt: float,
               shares: float, current_price: float) -> dict:
    section("PEER COMPARABLES")

    name_w = 22
    col_w = 14

    headers = ["EV/EBITDA", "EV/Revenue", "Rev Growth", "EBITDA Mgn", "FCF Yield"]
    print(f"{'Company':>{name_w}}" + "".join(f"{h:>{col_w}}" for h in headers))
    separator("-", name_w + col_w * len(headers))

    ev_ebitdas = []
    ev_revs = []

    for p in PEERS:
        ev_ebitdas.append(p["ev_ebitda"])
        ev_revs.append(p["ev_rev"])
        line = (
            f"{p['name']:>{name_w}}"
            f"{fmt_x(p['ev_ebitda']):>{col_w}}"
            f"{fmt_x(p['ev_rev']):>{col_w}}"
            f"{fmt_pct(p['rev_growth']):>{col_w}}"
            f"{fmt_pct(p['ebitda_margin']):>{col_w}}"
            f"{fmt_pct(p['fcf_yield']):>{col_w}}"
        )
        print(line)

    separator("-", name_w + col_w * len(headers))

    med_ev_ebitda = statistics.median(ev_ebitdas)
    med_ev_rev = statistics.median(ev_revs)

    print(
        f"{'Median':>{name_w}}"
        f"{fmt_x(med_ev_ebitda):>{col_w}}"
        f"{fmt_x(med_ev_rev):>{col_w}}"
        f"{fmt_pct(statistics.median([p['rev_growth'] for p in PEERS])):>{col_w}}"
        f"{fmt_pct(statistics.median([p['ebitda_margin'] for p in PEERS])):>{col_w}}"
        f"{fmt_pct(statistics.median([p['fcf_yield'] for p in PEERS])):>{col_w}}"
    )

    # Implied prices
    ev_from_ebitda = ebitda_ttm * med_ev_ebitda
    price_from_ebitda = (ev_from_ebitda - net_debt) / shares

    ev_from_rev = rev_ttm * med_ev_rev
    price_from_rev = (ev_from_rev - net_debt) / shares

    print(f"\n  Peer Median EV/EBITDA ({fmt_x(med_ev_ebitda)}) implied price: {fmt_price(price_from_ebitda)}")
    print(f"  Peer Median EV/Revenue ({fmt_x(med_ev_rev)}) implied price:  {fmt_price(price_from_rev)}")
    print(f"  Current market price: {fmt_price(current_price)}")

    return {
        "med_ev_ebitda": med_ev_ebitda,
        "med_ev_rev": med_ev_rev,
        "price_from_ebitda": price_from_ebitda,
        "price_from_rev": price_from_rev,
    }


# ---------------------------------------------------------------------------
# 5. Football Field
# ---------------------------------------------------------------------------

def football_field(methods: list, field_width: int = 55) -> None:
    """
    methods: list of dicts with keys: label, low, high, current
    current: the market price for reference
    """
    section("FOOTBALL FIELD — Valuation Range Summary")

    all_vals = [v for m in methods for v in (m["low"], m["high"])]
    global_min = min(all_vals) * 0.85
    global_max = max(all_vals) * 1.10

    price_range = global_max - global_min

    def to_pos(val: float) -> int:
        if price_range == 0:
            return 0
        return int((val - global_min) / price_range * field_width)

    label_w = 28
    print(f"  {'Method':>{label_w}}  {'Range & Price':}")
    print(f"  {'-' * label_w}  {'-' * (field_width + 14)}")

    for m in methods:
        lo_pos = to_pos(m["low"])
        hi_pos = to_pos(m["high"])
        lo_pos = max(0, min(lo_pos, field_width))
        hi_pos = max(0, min(hi_pos, field_width))

        bar = [" "] * (field_width + 1)
        for j in range(lo_pos, hi_pos + 1):
            bar[j] = "█"
        bar_str = "".join(bar)

        label = m["label"]
        lo_str = fmt_price(m["low"])
        hi_str = fmt_price(m["high"])
        print(f"  {label:>{label_w}}  |{bar_str}|  {lo_str} – {hi_str}")

    # Scale bar
    scale_line = " " * (label_w + 3)
    ticks = 5
    step = price_range / ticks
    tick_labels = ""
    for i in range(ticks + 1):
        val = global_min + i * step
        pos = to_pos(val)
        lbl = f"{val:.0f}"
        if i == 0:
            tick_labels += lbl.ljust(field_width // ticks + 1)
        else:
            tick_labels += lbl.rjust(field_width // ticks)

    separator("-", label_w + field_width + 16)
    print(f"\n  Scale (USD):  {fmt_price(global_min)} {'':>{int(field_width * 0.35)}} {fmt_price((global_min + global_max) / 2)} {'':>{int(field_width * 0.25)}} {fmt_price(global_max)}")

    # Current price marker
    current_prices = [m.get("current") for m in methods if m.get("current") is not None]
    if current_prices:
        cp = current_prices[0]
        cp_pos = to_pos(cp)
        marker_line = " " * (label_w + 3) + " " + " " * cp_pos + "▲"
        price_label_line = " " * (label_w + 3) + " " + " " * max(0, cp_pos - 3) + fmt_price(cp) + " (mkt)"
        print(marker_line)
        print(price_label_line)


# ---------------------------------------------------------------------------
# 6. Reverse DCF
# ---------------------------------------------------------------------------

def reverse_dcf(current_price: float, net_debt: float, shares: float,
                rev0: float, growth_rates: list, ebitda_margin_0: float,
                ebitda_margin_5: float, da0: float, capex_rev_pct_y5: float,
                tax_rate: float, wacc: float) -> None:
    section("REVERSE DCF — What Exit Multiple Does the Market Imply?")

    # Target equity value from market price
    target_eq = current_price * shares
    target_ev = target_eq + net_debt

    # Binary search for exit multiple that yields target_ev
    lo, hi = 1.0, 50.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        result = run_dcf(rev0, growth_rates, ebitda_margin_0, ebitda_margin_5,
                         da0, capex_rev_pct_y5, tax_rate, wacc, net_debt,
                         shares, mid, 0.035)
        if result["ev_exit"] < target_ev:
            lo = mid
        else:
            hi = mid

    implied_multiple = (lo + hi) / 2.0
    y5_ebitda = run_dcf(rev0, growth_rates, ebitda_margin_0, ebitda_margin_5,
                        da0, capex_rev_pct_y5, tax_rate, wacc, net_debt,
                        shares, implied_multiple, 0.035)["ebitdas"][-1]

    print(f"\n  Current market price:         {fmt_price(current_price)}")
    print(f"  Implied equity value:         {fmt_m(target_eq)}")
    print(f"  Implied enterprise value:     {fmt_m(target_ev)}")
    print(f"  Y5 EBITDA (model):            {fmt_m(y5_ebitda)}")
    print(f"  Implied exit EV/EBITDA:       {fmt_x(implied_multiple)}")
    print()
    if implied_multiple > 15:
        print("  Interpretation: The market is pricing in aggressive growth or")
        print("  a premium exit multiple. The stock appears to already reflect")
        print("  optimistic assumptions.")
    elif implied_multiple < 8:
        print("  Interpretation: The market implies a very low exit multiple,")
        print("  suggesting bearish growth expectations or elevated risk premium.")
    else:
        print("  Interpretation: The implied exit multiple is within a reasonable")
        print("  range relative to peers, suggesting balanced risk/reward.")


# ---------------------------------------------------------------------------
# 7. Scenario Analysis
# ---------------------------------------------------------------------------

def scenario_analysis(wacc_base: float, rev0: float, growth_rates: list,
                      ebitda_margin_0: float, ebitda_margin_5: float,
                      da0: float, capex_rev_pct_y5: float, tax_rate: float,
                      net_debt: float, shares: float,
                      exit_multiple: float, terminal_growth: float) -> dict:
    section("SCENARIO ANALYSIS")

    scenarios = [
        {
            "name": "Bear",
            "wacc_delta": +0.02,
            "tg_delta": -0.01,
            "margin5_delta": -0.03,
            "prob": 0.25,
        },
        {
            "name": "Base",
            "wacc_delta": 0.0,
            "tg_delta": 0.0,
            "margin5_delta": 0.0,
            "prob": 0.50,
        },
        {
            "name": "Bull",
            "wacc_delta": -0.01,
            "tg_delta": +0.005,
            "margin5_delta": +0.02,
            "prob": 0.25,
        },
    ]

    col_w = 14
    label_w = 10
    headers = ["WACC", "TG Rate", "Mrgn Y5", "Exit EV", "Eq Value", "Price"]
    print(f"  {'Scenario':<{label_w}}" + "".join(f"{h:>{col_w}}" for h in headers))
    separator("-", label_w + col_w * len(headers) + 2)

    weighted_price = 0.0
    weighted_ev = 0.0
    prices = {}

    for sc in scenarios:
        w = wacc_base + sc["wacc_delta"]
        m5 = ebitda_margin_5 + sc["margin5_delta"]
        m5 = max(0.05, min(m5, 0.99))

        result = run_dcf(rev0, growth_rates, ebitda_margin_0, m5,
                         da0, capex_rev_pct_y5, tax_rate, w, net_debt,
                         shares, exit_multiple, terminal_growth + sc["tg_delta"])

        p = result["price_exit"]
        ev = result["ev_exit"]
        eq = result["equity_value_exit"]
        weighted_price += p * sc["prob"]
        weighted_ev += ev * sc["prob"]
        prices[sc["name"]] = p

        line = (
            f"  {sc['name']:<{label_w}}"
            f"{fmt_pct(w):>{col_w}}"
            f"{fmt_pct(terminal_growth + sc['tg_delta']):>{col_w}}"
            f"{fmt_pct(m5):>{col_w}}"
            f"{fmt_m(ev, 0):>{col_w}}"
            f"{fmt_m(eq, 0):>{col_w}}"
            f"{fmt_price(p):>{col_w}}"
        )
        print(line)

    separator("-", label_w + col_w * len(headers) + 2)
    print(f"\n  Probability-Weighted Price: {fmt_price(weighted_price)}")
    print(f"  Probability-Weighted EV:    {fmt_m(weighted_ev)}")
    print(f"\n  Probabilities: Bear=25%, Base=50%, Bull=25%")

    return {
        "bear_price": prices.get("Bear", 0),
        "base_price": prices.get("Base", 0),
        "bull_price": prices.get("Bull", 0),
        "weighted_price": weighted_price,
    }


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary(ticker: str, current_price: float, dcf_result: dict,
                  peer_result: dict, scenario_result: dict) -> None:
    section(f"VALUATION SUMMARY — {ticker}")

    rows = [
        ("DCF Base Case (Exit Multiple)", dcf_result["price_exit"]),
        ("Peer Median EV/EBITDA", peer_result["price_from_ebitda"]),
        ("Peer Median EV/Revenue", peer_result["price_from_rev"]),
        ("Scenario Bear (25%)", scenario_result["bear_price"]),
        ("Scenario Bull (25%)", scenario_result["bull_price"]),
        ("Probability-Weighted Price", scenario_result["weighted_price"]),
    ]

    label_w = 38
    for label, price in rows:
        upside = (price / current_price - 1.0) * 100 if current_price > 0 else 0
        updown = "up" if upside >= 0 else "down"
        print(f"  {label:<{label_w}} {fmt_price(price):>8}   ({abs(upside):.1f}% {updown})")

    print(f"\n  Current Market Price: {fmt_price(current_price)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    separator("=")
    print("  AEON DCF ENGINE — Complete Valuation Engine")
    print("  WACC/CAPM | 5-Year DCF | Sensitivity | Comps | Football Field")
    separator("=")
    print()

    print("  [1/7] Company & Market Data")
    print("  Press Enter to accept defaults (VNET Group example)\n")

    ticker = prompt_str("Ticker", "VNET")
    company = prompt_str("Company Name", "VNET Group")
    current_price = prompt_float("Current Price ($)", 10.51)
    shares = prompt_float("Shares Outstanding (M)", 269.0)
    net_debt = prompt_float("Net Debt ($M)", 1840.0)

    print()
    print("  [2/7] Income Statement & Cash Flow Inputs\n")
    rev_ttm = prompt_float("Revenue TTM ($M)", 1372.0)
    ebitda_ttm = prompt_float("EBITDA TTM ($M)", 411.0)
    ebitda_margin_0 = ebitda_ttm / rev_ttm
    print(f"    => Computed EBITDA Margin Y0: {fmt_pct(ebitda_margin_0)}")
    da0 = prompt_float("D&A TTM ($M)", 88.0)
    capex_ttm = prompt_float("CapEx TTM ($M)", 1138.0)
    capex_pct_y5 = prompt_float("CapEx as % of Revenue (Y5 target, e.g. 22 for 22%)", 22.0) / 100.0
    tax_rate = prompt_float("Tax Rate (%, e.g. 25)", 25.0) / 100.0

    print()
    print("  [3/7] Revenue Growth Rates (%, e.g. 17 for 17%)\n")
    growth_rates = []
    defaults = [17.0, 19.0, 18.0, 15.0, 8.0]
    for i, d in enumerate(defaults, 1):
        g = prompt_float(f"  Y{i} Revenue Growth (%)", d) / 100.0
        growth_rates.append(g)

    print()
    print("  [4/7] Margin & Terminal Value Assumptions\n")
    ebitda_margin_5_pct = prompt_float("EBITDA Margin Y5 Target (%)", 36.0)
    ebitda_margin_5 = ebitda_margin_5_pct / 100.0
    exit_multiple = prompt_float("Exit EV/EBITDA Multiple", 10.0)
    terminal_growth = prompt_float("Terminal Growth Rate (%, Gordon Growth)", 3.5) / 100.0

    print()
    print("  [5/7] WACC / CAPM Inputs (all in %)\n")
    rf = prompt_float("Risk-Free Rate (Rf, %)", 4.69) / 100.0
    erp = prompt_float("Equity Risk Premium (ERP, %)", 5.5) / 100.0
    beta = prompt_float("Beta", 1.45)
    crp = prompt_float("Country Risk Premium (CRP, %)", 1.8) / 100.0
    kd = prompt_float("Pre-Tax Cost of Debt (Kd, %)", 7.2) / 100.0
    debt_weight = prompt_float("Debt Weight in Capital Structure (%)", 18.0) / 100.0

    # ---- Compute WACC ----
    wacc_dict = compute_wacc(rf, erp, beta, crp, kd, tax_rate, debt_weight)
    wacc = wacc_dict["wacc"]

    section("WACC / CAPM BUILD-UP")
    print(f"  {'Risk-Free Rate (Rf):':<35} {fmt_pct(rf)}")
    print(f"  {'Beta:':<35} {beta:.2f}x")
    print(f"  {'Equity Risk Premium (ERP):':<35} {fmt_pct(erp)}")
    print(f"  {'Country Risk Premium (CRP):':<35} {fmt_pct(crp)}")
    print(f"  {'Cost of Equity (Ke = Rf+β·ERP+CRP):':<35} {fmt_pct(wacc_dict['ke'])}")
    print()
    print(f"  {'Pre-Tax Cost of Debt (Kd):':<35} {fmt_pct(kd)}")
    print(f"  {'Tax Rate:':<35} {fmt_pct(tax_rate)}")
    print(f"  {'After-Tax Cost of Debt:':<35} {fmt_pct(wacc_dict['kd_at'])}")
    print()
    print(f"  {'Equity Weight:':<35} {fmt_pct(wacc_dict['equity_weight'])}")
    print(f"  {'Debt Weight:':<35} {fmt_pct(wacc_dict['debt_weight'])}")
    print(f"  {'WACC:':<35} {fmt_pct(wacc)}")

    # ---- DCF ----
    dcf_result = run_dcf(
        rev_ttm, growth_rates, ebitda_margin_0, ebitda_margin_5,
        da0, capex_pct_y5, tax_rate, wacc,
        net_debt, shares, exit_multiple, terminal_growth,
    )
    print_dcf_table(dcf_result, net_debt, shares)

    # ---- Sensitivity ----
    sensitivity_analysis(
        wacc, rev_ttm, growth_rates, ebitda_margin_0, ebitda_margin_5,
        da0, capex_pct_y5, tax_rate, net_debt, shares, exit_multiple,
    )

    # ---- Peer Comps ----
    peer_result = peer_comps(rev_ttm, ebitda_ttm, net_debt, shares, current_price)

    # ---- Scenario Analysis ----
    scenario_result = scenario_analysis(
        wacc, rev_ttm, growth_rates, ebitda_margin_0, ebitda_margin_5,
        da0, capex_pct_y5, tax_rate, net_debt, shares,
        exit_multiple, terminal_growth,
    )

    # ---- Football Field ----
    methods = [
        {
            "label": "DCF — Bear Case",
            "low": scenario_result["bear_price"] * 0.95,
            "high": scenario_result["bear_price"] * 1.05,
            "current": current_price,
        },
        {
            "label": "DCF — Base Case",
            "low": dcf_result["price_exit"] * 0.92,
            "high": dcf_result["price_exit"] * 1.08,
            "current": current_price,
        },
        {
            "label": "DCF — Bull Case",
            "low": scenario_result["bull_price"] * 0.95,
            "high": scenario_result["bull_price"] * 1.05,
            "current": current_price,
        },
        {
            "label": "Peer EV/EBITDA",
            "low": peer_result["price_from_ebitda"] * 0.88,
            "high": peer_result["price_from_ebitda"] * 1.12,
            "current": current_price,
        },
        {
            "label": "Peer EV/Revenue",
            "low": peer_result["price_from_rev"] * 0.88,
            "high": peer_result["price_from_rev"] * 1.12,
            "current": current_price,
        },
    ]
    football_field(methods)

    # ---- Reverse DCF ----
    reverse_dcf(
        current_price, net_debt, shares,
        rev_ttm, growth_rates, ebitda_margin_0, ebitda_margin_5,
        da0, capex_pct_y5, tax_rate, wacc,
    )

    # ---- Summary ----
    print_summary(ticker, current_price, dcf_result, peer_result, scenario_result)

    separator("=")
    print("  Aeon DCF Engine — Analysis Complete")
    separator("=")
    print()


if __name__ == "__main__":
    main()
