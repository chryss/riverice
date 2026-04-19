import argparse
import datetime as dt
from pathlib import Path

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

import annual_config as cfg


def get_project_root() -> Path:
    """Resolve the repository root from this script location."""
    return Path(__file__).resolve().parent.parent


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate cumulative DD plots for all sites")
    parser.add_argument(
        "-y",
        "--year",
        type=int,
        default=cfg.RUNYEAR,
        help="Forecast year to process (default: annual_config.RUNYEAR)",
    )
    parser.add_argument(
        "--report-date",
        type=str,
        default=None,
        help="Daily report date as YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Plot start date as YYYY-MM-DD (default: <year>-03-15)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show plots interactively in addition to saving",
    )
    parser.add_argument(
        "--site",
        type=str,
        default=None,
        help="Process only one siteID (exact match)",
    )
    return parser.parse_args()


def get_paths(project_root: Path, year: int, report_date: str) -> dict:
    """Build all file and directory paths used by the script."""
    return {
        "breakupfpth": project_root / "data/breakupdata/derived/breakupDate_cleaned_selected.csv",
        "combindedpth": project_root / "data/weatherstations/ACIS_combined_DD",
        "daily_reportpth": project_root / f"data/DDforecast_{year}/daily_report_{report_date}.csv",
        "outfolder": project_root / f"data/DDforecast_{year}",
    }


def river_from_siteid(siteid: str) -> str:
    """Extract a river name ending in 'River' from a siteID string."""
    if "River" not in siteid:
        return "Unknown River"
    return f"{siteid.split('River', 1)[0].strip()} River"


def loc_from_siteid(siteid: str) -> str:
    """Extract location name from the siteID after the first occurrence of 'River'."""
    if "River" not in siteid:
        return siteid
    remainder = siteid.split("River", 1)[1].strip()
    parts = remainder.split(" ")
    return " ".join(parts[1:]) if len(parts) > 1 else remainder


def get_testdd(siteid: str, combindedpth: Path, locationprefix: str) -> pd.DataFrame:
    """Read combined DD data for a site."""
    fn = f"{locationprefix}{siteid.replace(' ', '_')}.csv"
    return pd.read_csv(combindedpth / fn, skiprows=3)


def melt_testdd(testdd: pd.DataFrame) -> pd.DataFrame:
    """Melt DD table to julian_day/year index with dd25 values."""
    testdd_melted = testdd.melt(
        id_vars=["julian_day"],
        value_vars=testdd.columns[1:],
        var_name="year",
        value_name="dd25",
    )
    testdd_melted.set_index(["julian_day", "year"], inplace=True)
    return testdd_melted


def get_breakupdd25_df(siteid: str, year: int, breakup: pd.DataFrame, combindedpth: Path, locationprefix: str) -> pd.DataFrame:
    """Combine breakup JulianDay with DD25 values for all historical years."""
    breakupdd25 = []
    testdd_melted = melt_testdd(get_testdd(siteid, combindedpth, locationprefix))
    site_rows = breakup[breakup.siteID == siteid][["year", "JulianDay"]]
    for _, row_year, julian_day in site_rows.itertuples():
        breakupdd25.append([row_year, julian_day, testdd_melted.loc[(julian_day, str(row_year)), "dd25"]])

    breakupdd25_df = pd.DataFrame(breakupdd25, columns=["year", "JulianDay", "DD25"])
    breakupdd25_df["thedate"] = pd.to_datetime(
        breakupdd25_df.JulianDay - 1,
        unit="D",
        origin=pd.Timestamp(f"{year}-01-01"),
    )
    return breakupdd25_df


def get_dailyreport_items(siteid: str, daily_report: pd.DataFrame) -> tuple[str, float]:
    """Return forecasted date and +/-3 day likelihood for a site."""
    loc = loc_from_siteid(siteid)
    site_row = daily_report.loc[daily_report.location == loc]
    forecasted_date = site_row["forecasted date"].item()
    likelihood_3d = site_row[
        "probability of breakup within ± 3 days around forecasted"
    ].item() * 100
    return forecasted_date, likelihood_3d


def make_plot_for_site(
    siteid: str,
    year: int,
    start_date: str,
    today_str: str,
    daily_report: pd.DataFrame,
    breakup: pd.DataFrame,
    combindedpth: Path,
    locationprefix: str,
    outfolder: Path,
    show_plots: bool,
) -> Path:
    """Create and save one cumulative DD plot for a site."""
    testdd = get_testdd(siteid, combindedpth, locationprefix)
    breakupdd25_df = get_breakupdd25_df(siteid, year, breakup, combindedpth, locationprefix)
    forecasted_date, likelihood_3d = get_dailyreport_items(siteid, daily_report)

    forecast_dt = pd.to_datetime(forecasted_date)
    today_dt = pd.to_datetime(today_str)
    plot_end = min(today_dt, forecast_dt).strftime("%Y-%m-%d")

    meandd25 = breakupdd25_df.DD25.mean()
    stddd25 = breakupdd25_df.DD25.std()

    testdd["thedate"] = pd.to_datetime(
        testdd.julian_day - 1,
        unit="D",
        origin=pd.Timestamp(f"{year}-01-01"),
    )
    testdd.set_index("thedate", inplace=True)

    year_col = str(year)
    fig, ax = plt.subplots(figsize=(9, 4))
    f = sns.lineplot(data=testdd[f"{start_date}":plot_end], x="thedate", y=year_col, ax=ax)
    g = sns.scatterplot(
        data=breakupdd25_df,
        x="thedate",
        y="DD25",
        hue="year",
        palette="flare_r",
        s=50,
        marker="X",
        ax=ax,
        legend=None,
    )

    if forecast_dt > today_dt:
        sns.lineplot(
            data=testdd[today_str:forecasted_date],
            x="thedate",
            y=year_col,
            linestyle="--",
            color="teal",
            legend=None,
            ax=ax,
        )
        ax.scatter(forecast_dt, testdd.loc[forecasted_date][year_col], color="teal", s=50, marker="X")
        ax.scatter(today_dt, testdd.loc[today_str][year_col], color="slateblue")
    else:
        ax.scatter(forecast_dt, testdd.loc[forecasted_date][year_col], color="slateblue")

    xmin, _ = f.get_xlim()
    _, xmax = g.get_xlim()
    norm = plt.Normalize(breakupdd25_df["year"].min(), breakupdd25_df["year"].max())
    cmap = sns.color_palette("flare_r", as_cmap=True)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    fig.colorbar(sm, ax=ax, label="year")

    ax.hlines(y=meandd25, color="grey", xmin=xmin, xmax=xmax, lw=0.75)
    ax.hlines(
        y=[meandd25 - stddd25, meandd25 + stddd25],
        color="grey",
        linestyles="--",
        lw=0.5,
        xmin=xmin,
        xmax=xmax,
    )
    ax.tick_params(axis="x", rotation=30)
    ax.set_xlabel("date")
    ax.set_ylabel("cumulative degree days")
    ax.set_title(f"{siteid}, {year_col}")
    ax.text(
        forecast_dt,
        50,
        f"most likely: {forecasted_date}\n(P = {likelihood_3d:.2f} % +/- 3 days)",
        color="teal",
        ha="center",
    )

    river_name = river_from_siteid(siteid)
    river_dir = outfolder / river_name.replace(" ", "_")
    river_dir.mkdir(parents=True, exist_ok=True)
    outfn = river_dir / f"intermediate_cumul_{siteid.replace(' ', '_')}_{year_col}.png"
    fig.savefig(outfn, bbox_inches="tight")

    if show_plots:
        plt.show()
    plt.close(fig)
    return outfn


if __name__ == "__main__":
    args = parse_arguments()
    project_root = get_project_root()

    report_date = args.report_date if args.report_date else dt.datetime.now().strftime("%Y-%m-%d")
    start_date = args.start_date if args.start_date else f"{args.year}-03-15"

    paths = get_paths(project_root, args.year, report_date)
    if not paths["daily_reportpth"].exists():
        raise FileNotFoundError(f"Daily report not found: {paths['daily_reportpth']}")

    daily_report = pd.read_csv(paths["daily_reportpth"])
    breakup = pd.read_csv(paths["breakupfpth"], skiprows=3, index_col=0)
    site_ids = breakup.siteID.unique()
    if args.site:
        site_ids = [args.site]

    locationprefix = "DD25_combined_"
    saved = 0
    skipped = 0

    for siteid in site_ids:
        print(f"Processing {siteid}...")
        try:
            outpath = make_plot_for_site(
                siteid=siteid,
                year=args.year,
                start_date=start_date,
                today_str=report_date,
                daily_report=daily_report,
                breakup=breakup,
                combindedpth=paths["combindedpth"],
                locationprefix=locationprefix,
                outfolder=paths["outfolder"],
                show_plots=args.show,
            )
            saved += 1
            print(f"  saved: {outpath}")
        except Exception as exc:
            skipped += 1
            print(f"  skipped: {siteid} ({exc})")

    print(f"Done. Saved={saved}, Skipped={skipped}")