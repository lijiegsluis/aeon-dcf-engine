import contextlib
import io
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import main as dcf  # noqa: E402

# Default VNET example from the interactive prompts
BASE = dict(rev0=1372.0, growth_rates=[0.17, 0.19, 0.18, 0.15, 0.08], ebitda_margin_0=411 / 1372,
            ebitda_margin_5=0.36, da0=88.0, capex_rev_pct_y5=0.22, tax_rate=0.25,
            net_debt=1840.0, shares=269.0)


def wacc():
    return dcf.compute_wacc(0.0469, 0.055, 1.45, 0.018, 0.072, 0.25, 0.18)["wacc"]


def run(w=None, exit_multiple=10.0, tg=0.035, **over):
    args = {**BASE, **over}
    return dcf.run_dcf(args["rev0"], args["growth_rates"], args["ebitda_margin_0"], args["ebitda_margin_5"],
                       args["da0"], args["capex_rev_pct_y5"], args["tax_rate"], wacc() if w is None else w,
                       args["net_debt"], args["shares"], exit_multiple, tg)


class Wacc(unittest.TestCase):
    def test_capm_build_up(self):
        w = dcf.compute_wacc(0.0469, 0.055, 1.45, 0.018, 0.072, 0.25, 0.18)
        self.assertAlmostEqual(w["ke"], 0.0469 + 1.45 * 0.055 + 0.018, places=12)
        self.assertAlmostEqual(w["kd_at"], 0.072 * 0.75, places=12)
        self.assertAlmostEqual(w["wacc"], 0.82 * w["ke"] + 0.18 * w["kd_at"], places=12)


class Dcf(unittest.TestCase):
    def test_reference_case(self):
        d = run()
        self.assertAlmostEqual(d["price_exit"], 14.8437, places=3)
        self.assertAlmostEqual(d["ev_exit"], 5832.96, places=1)

    def test_terminal_value_is_exit_multiple_of_y5_ebitda(self):
        d = run()
        self.assertAlmostEqual(d["tv_exit"], d["ebitdas"][-1] * 10.0, places=9)
        self.assertAlmostEqual(d["pv_tv_exit"], d["tv_exit"] / (1 + wacc()) ** 5, places=9)
        self.assertAlmostEqual(d["ev_exit"], sum(d["pv_ufcfs"]) + d["pv_tv_exit"], places=9)

    def test_price_moves_the_right_way(self):
        self.assertGreater(run(exit_multiple=12)["price_exit"], run(exit_multiple=10)["price_exit"])
        self.assertLess(run(w=wacc() + 0.02)["price_exit"], run()["price_exit"])

    def test_zero_growth_is_respected(self):
        d = run(growth_rates=[0, 0, 0, 0, 0])
        self.assertTrue(all(abs(r - 1372.0) < 1e-9 for r in d["revenues"]))

    def test_gordon_growth_undefined_when_growth_exceeds_wacc(self):
        self.assertIsNone(run(tg=0.20)["price_ggm"])


class Reports(unittest.TestCase):
    def test_report_sections_run(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            dcf.sensitivity_analysis(wacc(), BASE["rev0"], BASE["growth_rates"], BASE["ebitda_margin_0"],
                                     BASE["ebitda_margin_5"], BASE["da0"], BASE["capex_rev_pct_y5"],
                                     BASE["tax_rate"], BASE["net_debt"], BASE["shares"], 25.0)
        self.assertIn("25.0x", out.getvalue(), "sensitivity columns should bracket the chosen multiple")


if __name__ == "__main__":
    unittest.main()
