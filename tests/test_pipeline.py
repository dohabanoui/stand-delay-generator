"""Tests unitaires (cahier des charges §11) : rotations, quantiles, lambda, recouvrement, contrainte physique,
baseline indépendante, MILP jouet, rejeu."""
import numpy as np
import pandas as pd
import pytest

from delaygen import generate
from delaygen.allocation import instance, milp, replay
from delaygen.data.loaders import hhmm_to_minutes
from delaygen.data.rotations import build_rotations
from delaygen.models import dependence, marginals, propagation, regime

REGIONS = {"NC": "Southeast", "NY": "Northeast", "TX": "South-Central"}


def _flights():
    """Mini-CSV synthétique : 20 vols avec cas limites (minuit, nuitée, tail manquant)."""
    rows = []
    d = "2023-03-01"
    # avion N1 : arrive 08:00, repart 09:30 ; arrive 14:00, repart 15:10 (2 rotations)
    rows += [dict(FlightDate=d, Reporting_Airline="AA", Tail_Number="N1", Flight_Number_Reporting_Airline=1, Origin="JFK", OriginState="NY", Dest="CLT", DestState="NC", CRSDepTime=600, DepTime=605, DepDelay=5, CRSArrTime=800, ArrTime=810, ArrDelay=10),
             dict(FlightDate=d, Reporting_Airline="AA", Tail_Number="N1", Flight_Number_Reporting_Airline=2, Origin="CLT", OriginState="NC", Dest="DFW", DestState="TX", CRSDepTime=930, DepTime=940, DepDelay=10, CRSArrTime=1200, ArrTime=1200, ArrDelay=0),
             dict(FlightDate=d, Reporting_Airline="AA", Tail_Number="N1", Flight_Number_Reporting_Airline=3, Origin="DFW", OriginState="TX", Dest="CLT", DestState="NC", CRSDepTime=1230, DepTime=1230, DepDelay=0, CRSArrTime=1400, ArrTime=1350, ArrDelay=-10),
             dict(FlightDate=d, Reporting_Airline="AA", Tail_Number="N1", Flight_Number_Reporting_Airline=4, Origin="CLT", OriginState="NC", Dest="JFK", DestState="NY", CRSDepTime=1510, DepTime=1600, DepDelay=50, CRSArrTime=1700, ArrTime=1750, ArrDelay=50)]
    # avion N2 : arrive 22:30, repart le lendemain (nuitée) -> rotation ouverte
    rows += [dict(FlightDate=d, Reporting_Airline="DL", Tail_Number="N2", Flight_Number_Reporting_Airline=10, Origin="JFK", OriginState="NY", Dest="CLT", DestState="NC", CRSDepTime=2000, DepTime=2000, DepDelay=0, CRSArrTime=2230, ArrTime=5, ArrDelay=95)]
    # avion N3 : premier départ du jour sans arrivée
    rows += [dict(FlightDate=d, Reporting_Airline="DL", Tail_Number="N3", Flight_Number_Reporting_Airline=20, Origin="CLT", OriginState="NC", Dest="DFW", DestState="TX", CRSDepTime=600, DepTime=600, DepDelay=0, CRSArrTime=800, ArrTime=800, ArrDelay=0)]
    # tail manquant : arrivée non appariable
    rows += [dict(FlightDate=d, Reporting_Airline="UA", Tail_Number=None, Flight_Number_Reporting_Airline=30, Origin="JFK", OriginState="NY", Dest="CLT", DestState="NC", CRSDepTime=900, DepTime=900, DepDelay=0, CRSArrTime=1100, ArrTime=1100, ArrDelay=0)]
    # vol programmé 23:50, réel 00:20 (après minuit)
    rows += [dict(FlightDate=d, Reporting_Airline="UA", Tail_Number="N4", Flight_Number_Reporting_Airline=40, Origin="JFK", OriginState="NY", Dest="CLT", DestState="NC", CRSDepTime=2100, DepTime=2130, DepDelay=30, CRSArrTime=2350, ArrTime=20, ArrDelay=30)]
    df = pd.DataFrame(rows)
    df["FlightDate"] = pd.to_datetime(df.FlightDate)
    df["Tail_Number"] = df.Tail_Number.astype("string")
    for c in ["CRSDepTime", "DepTime", "CRSArrTime", "ArrTime"]:
        df[c + "_min"] = hhmm_to_minutes(df[c])
    for c in ["LateAircraftDelay", "WeatherDelay", "NASDelay", "CarrierDelay", "TaxiIn", "TaxiOut", "Distance"]:
        df[c] = 0.0
    df["category"] = "NB"
    return df


def test_hhmm():
    assert list(hhmm_to_minutes(pd.Series([0, 130, 2359, 2400]))) == [0, 90, 1439, 1440]


def test_rotations_reconstruction():
    rot, rep = build_rotations(_flights(), "CLT", REGIONS)
    full = rot[(~rot.open_rotation) & (~rot.first_departure)]
    assert len(full) == 2 and set(full["tail"]) == {"N1"}
    r1 = full.sort_values("a_sched").iloc[0]
    assert r1.a_sched == 480 and r1.d_sched == 570 and r1.A == 10 and r1.D == 10
    assert rot.open_rotation.sum() == 3           # N2 (nuitée), tail manquant, N4 (après minuit, pas de départ)
    assert rot.first_departure.sum() == 1         # N3
    n2 = rot[(rot["tail"] == "N2") & rot.open_rotation].iloc[0]
    assert n2.a_real == 1440 + 5                   # arrivée réelle après minuit corrigée
    assert n2.d_sched == n2.a_sched + 480
    assert rot.loc[rot.origin_state == "NY", "origin_region"].eq("Northeast").all()


def test_quantile_table_roundtrip():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"hour_block_arr": rng.integers(6, 10, 5000), "regime": "normal", "A": rng.gamma(2, 15, 5000) - 20})
    t = marginals.fit(df, "A", min_obs=100, regimes=["normal"])
    x = np.linspace(-15, 80, 50)
    u = t.cdf((7, "normal"), x)
    back = t.inverse_cdf((7, "normal"), u)
    assert np.allclose(back, x, atol=2.0)
    # classes pauvres fusionnées : heure 20 absente -> fusion vers une autre classe
    assert t.resolved[(9, "normal")] == (9, "normal")


def test_lambda_normalisation():
    p = dependence.scale_lambdas({"lambda_d": .3, "lambda_h": .3, "lambda_c": .3, "lambda_r": .3}, 1.0)
    s = sum(p[k] ** 2 for k in ["lambda_d", "lambda_h", "lambda_c", "lambda_r"]) + p["sigma_eps"] ** 2
    assert abs(s - 1) < 1e-9
    p0 = dependence.scale_lambdas(p, 0.0)
    assert p0["sigma_eps"] == 1.0


def test_moments_recovery():
    """Données synthétiques avec lambda connus -> fit_moments les retrouve à +-0.05."""
    rng = np.random.default_rng(1)
    true = {"lambda_d": .25, "lambda_h": .30, "lambda_c": .20, "lambda_r": .15}
    true["sigma_eps"] = float(np.sqrt(1 - sum(v ** 2 for v in true.values())))
    rows = []
    for day in range(60):
        n = 400
        h = rng.integers(6, 22, n); c = rng.choice(["AA", "OH", "DL", "UA"], n); r = rng.choice(list("ABCDE"), n)
        sched = pd.DataFrame({"hour_block_arr": h, "carrier": c, "origin_region": r, "date": pd.Timestamp("2023-01-01") + pd.Timedelta(days=day)})
        S, _ = dependence.sample_scores(sched, true, rng, 1)
        sched["A"] = S[0]  # A gaussien -> scores normaux = A standardisés dans la classe
        sched["regime"] = "normal"
        rows.append(sched)
    df = pd.concat(rows, ignore_index=True)
    S = dependence.normal_scores(df, ["hour_block_arr", "regime"], "A")
    est = dependence.fit_moments(df, S, max_pairs_per_day=30000)
    for k in ["lambda_d", "lambda_h", "lambda_c", "lambda_r"]:
        assert abs(est[k] - true[k]) < 0.06, (k, est[k], true[k])


def _params():
    rng = np.random.default_rng(2)
    df = pd.DataFrame({"hour_block_arr": rng.integers(6, 22, 20000), "regime": rng.choice(["normal", "degrade"], 20000),
                       "A": rng.gamma(2, 15, 20000) - 20})
    tA = marginals.fit(df, "A", min_obs=100, regimes=["normal", "degrade"])
    dfg = pd.DataFrame({"hour_block_dep": rng.integers(6, 23, 20000), "regime": rng.choice(["normal", "degrade"], 20000),
                        "D": np.clip(rng.gamma(1, 8, 20000) - 3, 0, None)})
    tG = marginals.fit(dfg, "D", "hour_block_dep", min_obs=100, regimes=["normal", "degrade"])
    lam = {"lambda_d": .2, "lambda_h": .2, "lambda_c": .2, "lambda_r": .2, "sigma_eps": float(np.sqrt(1 - 4 * .04))}
    return {"states": ["normal", "degrade"], "regime": regime.fit(pd.Series(["normal"] * 8 + ["degrade"] * 2), ["normal", "degrade"]),
            "marginals_A_table": tA, "ground_table": tG, "marginals_D_table": tG,
            "dependence": {"all": lam, "normal": lam, "degrade": lam}, "mtt": {"RJ": 25, "NB": 35, "WB": 60}, "rho_G": .3, "peak_hours": [8, 17]}


def _schedule(n=200, seed=3):
    rng = np.random.default_rng(seed)
    a = rng.integers(360, 1300, n).astype(float)
    return pd.DataFrame({"rot_id": np.arange(n), "category": rng.choice(["RJ", "NB", "WB"], n, p=[.3, .68, .02]),
                         "carrier": rng.choice(["AA", "OH"], n), "origin_region": rng.choice(["Northeast", "Southeast"], n),
                         "a_sched": a, "d_sched": a + rng.integers(40, 180, n), "hour_block_arr": (a // 60).astype(int),
                         "hour_block_dep": ((a + 60) // 60).clip(0, 23).astype(int), "pax": 140.0,
                         "open_rotation": False, "first_departure": False})


def test_physical_constraint_and_scenarios_shape():
    p = _params(); sch = _schedule()
    out = generate.generate_day(sch, p, 50, 0)
    assert out["A"].shape == (50, 200)
    mtt = sch.category.map(p["mtt"]).to_numpy()
    ground_sched = (sch.d_sched - sch.a_sched).to_numpy()
    # contrainte physique : temps au sol réalisé >= min(MTT, temps au sol programmé)
    assert np.all(out["d_real"] - out["a_real"] >= np.minimum(mtt, ground_sched) - 1e-9)
    assert np.all(out["D"] >= out["A"] - np.clip(ground_sched - mtt, 0, None) - 1e-9)
    p2 = dict(p); p2["allow_early_departure"] = False
    assert np.all(generate.generate_day(sch, p2, 20, 0)["D"] >= 0)


def test_independent_baseline_equivalence():
    """correlation_scale = 0 et propagation off -> scores i.i.d. : corrélation intra-heure ~ 0."""
    from delaygen.validation.structural import intra_group_corr
    p = _params(); sch = _schedule(400)
    out = generate.generate_day(sch, p, 200, 0, correlation_scale=0.0, propagation_on=False, independent_D=True)
    c0 = intra_group_corr(out["A"], sch.hour_block_arr.to_numpy())
    assert abs(c0) < 0.02
    assert np.all(out["D_react"] == 0)
    out2 = generate.generate_day(sch, p, 200, 0, correlation_scale=1.0)
    c1 = intra_group_corr(out2["A"], sch.hour_block_arr.to_numpy())
    assert c1 > 0.02 and c1 > c0 + 0.02   # lambda_d^2 + lambda_h^2 = 0.08 en espace des scores


def test_milp_toy():
    """5 rotations / 2 stands : solution connue (2 rotations chevauchantes ne partagent pas de stand)."""
    sch = pd.DataFrame({"rot_id": range(5), "category": ["NB"] * 5, "a_sched": [0, 10, 100, 110, 300.], "d_sched": [50, 60, 150, 160, 350.], "pax": [100.] * 5})
    stands = pd.DataFrame({"stand": ["S0", "S1"], "cat": ["NB", "NB"], "dist": [100., 200.], "cat_rank": [1, 1]})
    sol = milp.solve(sch, stands, 0, 10, workers=2)
    al = sol["allocation"]
    assert sol["n_unassigned"] == 0
    assert al[0] != al[1] and al[2] != al[3]
    assert al[4] == "S0"  # rotation isolée -> stand le plus proche
    assert abs(sol["objective"] - (100 * 100 * 3 + 100 * 200 * 2)) < 1e-6


def test_replay_known_conflicts():
    sch = pd.DataFrame({"rot_id": range(4), "category": ["NB"] * 4, "a_sched": [0, 100, 200, 300.], "d_sched": [60, 160, 260, 360.], "pax": 100.})
    stands = pd.DataFrame({"stand": ["S0", "S1"], "cat": ["NB", "NB"], "dist": [100., 200.], "cat_rank": [1, 1]})
    alloc = {0: "S0", 1: "S0", 2: "S0", 3: "S1"}
    a_real = np.array([[0, 100, 200, 300.], [0, 90, 200, 300.]])       # scénario 2 : rot 1 arrive à 90
    d_real = np.array([[60, 160, 260, 360.], [95, 160, 262, 360.]])     # scénario 2 : rot 0 part à 95 -> conflit avec rot 1 ; rot 2 vs rot 1 : 200 < 160+5 ? non
    m = replay.evaluate(sch, stands, alloc, a_real, d_real, b_ops=5, n_recourse=2)
    assert list(m.conflicts) == [0, 1]
    assert m.overlap_minutes.iloc[1] == 10          # 95 + 5 - 90
    assert m.reassignments.iloc[0] == 0 and m.reassignments.iloc[1] >= 1


def test_instance_peak():
    sch = _schedule(300)
    st = instance.build(sch, None, 0.88, {"WB": .03, "NB": .67, "RJ": .30}, seed=0)
    assert len(st) >= instance.peak_occupancy(sch)
    assert (st.cat == "WB").sum() >= instance.peak_occupancy(sch[sch.category == "WB"])
