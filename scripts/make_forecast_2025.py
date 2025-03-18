from pathlib import Path
import pandas as pd
import datetime as dt 
from sklearn import linear_model
from sklearn.metrics import root_mean_squared_error
import scipy.stats as stats
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
import riverice_util as ru
import warnings

warnings.filterwarnings("ignore")
prefix = "DD25" 
xs = np.arange(-101, 101)
year = 2025
for_ffmpeg = False
DAILY = False
PLOTS = True

PROJPATH = Path().resolve().parent
tdd_anomalycorr = PROJPATH / f"data/breakupdata/derived/{prefix}_anomaly_correlations.csv"
breakup_stats = PROJPATH / f"data/breakupdata/derived/breakupdate_mean_std_JD.csv"
breakupdata = PROJPATH / 'data/breakupdata/'
breakuppth = breakupdata / "derived/breakupDate_cleaned_selected.csv"
stationfolder = PROJPATH / f"data/weatherstations/ACIS/{prefix}/dd_cumul_bystation"
combinedpath = PROJPATH / 'data/weatherstations/ACIS_combined_DD'
# huctablepath = PROJPATH / "data/breakupdata/derived/breakupDate_mean_std_HUC_augmented.csv"
outfolder = PROJPATH / f"data/DDforecast_2025"
broken_up = "broken_up_2025.csv"

def get_brokenup():
    try:
        return set(pd.read_csv(outfolder / broken_up).location)
    except:
        return set()
    

def make_likelihood_DF(breakupDF):
    """Generate a dataframe of breakup likelihoods from historical data"""
    possible_days = sorted(list(set(breakupDF['JulianDay'])))
    records = []
    for jdays in range(72, 135):
        days_from_now_possible = [item-jdays for item in possible_days]
        print(days_from_now_possible)
        if len(days_from_now_possible) != 0:
            for days in days_from_now_possible:
                days_possible = days + jdays
                years = breakup[breakup['JulianDay']==days_possible].year.astype(str).to_list()
                if len(years) == 0: 
                    print("This shouldnt happen")
                    continue
                for year in years:
                    records.append({
                        'forecast_day_jday': jdays,
                        'year': year,
                        'days_from_then': days,
                        'mean_DD': mean_station[year][jdays]}
                    )
    likelihoodDF = pd.DataFrame.from_records(records)
    likelihoodDF['jday_absolute'] = likelihoodDF['forecast_day_jday'] + likelihoodDF['days_from_then']
    likelihoodDF['forecastdate'] = likelihoodDF['forecast_day_jday'].apply(ru.julianday2date)
    return likelihoodDF

if __name__ == '__main__':
    days_start = 72
    days_end = 90
    if DAILY:
        today = dt.datetime.now().strftime('%Y-%m-%d')
        # we start and end the day before today b/c day with newest ACIS data
        days_end = ru.datestr2julianday(today)
        days_start = ru.datestr2julianday(today) - 1

    breakupstats = pd.read_csv(breakup_stats, skiprows=4, index_col=0)
    breakupDF = pd.read_csv(breakuppth, header=3, index_col=0)
    breakupDF['JulianDay'] = breakupDF.apply(
        lambda row: ru.datestr2julianday(row.breakup), axis=1)
    broken_upSet = get_brokenup()
    # print(broken_upSet)

    results = {}
    for _, item in breakupstats.iterrows():
        location = item.siteID
        if location in broken_upSet:
            print(f"{location} has broken up")
            continue
        river = item.river
        locality = item.locality
        print(f"working on {location}")
        # load combined station data
        mean_station = pd.read_csv(combinedpath / f"{prefix}_combined_{location.replace(' ', '_')}.csv", 
            skiprows=3, index_col=0)
        # filter breakup data
        breakup = breakupDF.copy()
        breakup = breakup[breakup.siteID == location].sort_values(by='year').reset_index(drop=True)
        likelihoodDF = make_likelihood_DF(breakup)

        # do calculation and generate plots
        if for_ffmpeg: icount = 1
        for ii in range (days_start, days_end, 1):
            breakup_avg_model = linear_model.LinearRegression() 
            DF = likelihoodDF[likelihoodDF.forecast_day_jday==ii].copy()
            DDval = mean_station[f'{year}'][ii].squeeze()
            breakup_avg_model.fit(DF[['mean_DD']].values, DF[['days_from_then']].values)
            try: 
                mu_0 = breakup_avg_model.predict([[DDval]]).item()
            except ValueError:
                break
            sigma_0 = root_mean_squared_error([breakup_avg_model.predict([[dd]]).item() for dd in DF['mean_DD'].tolist()],
                        DF['days_from_then'].tolist())
            # normalize on > 0 values
            pdf = stats.norm.pdf(xs, mu_0, sigma_0)/stats.norm.pdf(xs[101:], mu_0, sigma_0).sum()
            prob_12 = pdf[101:103].sum()
            prob_37 = pdf[103:108].sum()
            prob_wk2 = pdf[108:115].sum()
            prob_wk3 = pdf[115:122].sum()
            forecastdate = ru.julianday2date(ii + 1, year) # forecast is one day later than data
            mostlikely = int(np.round(mu_0))
            forecasteddate = ru.julianday2date(mostlikely+ii, year)
            startidx = max(101, 100 + mostlikely-3)
            endidx = startidx + 6
            plusminus3daysprob = pdf[startidx:endidx+1].sum()
            print(f"Forecast on {forecastdate}")
            print(mu_0, np.round(mu_0), sigma_0, prob_12, prob_37, prob_wk2, prob_wk3)
            if PLOTS:
                fig, ax1 = plt.subplots()
                ax1.plot(xs[:102], pdf[:102], linestyle='dashed', color='grey', linewidth=1)
                ax1.plot(xs[101:], pdf[101:], color='black')
                ax1.vlines(0, 0, 0.4, colors='black', linestyles='dotted')
                # Add most likely +/- 3 days
                ax1.vlines(mu_0, 0, 0.4, colors='grey')
                shiftflag = False   # do we have to shift the +/- 3 day window?
                if  100 + mostlikely-3 < 101:
                    shiftflag = True
                ax1.fill_between(xs[startidx+1:endidx+2], pdf[startidx+1:endidx+2], color='tab:purple', alpha=0.5)
                ax1.text(139-ii, .36, f"Most likely breakup: ", color='tab:purple')
                ax1.text(139-ii, .34, f"in {mostlikely} d on {forecasteddate}", 
                        color='tab:purple')
                if shiftflag: 
                    textsnippet = "7d"
                else:
                    textsnippet = "±3d"
                ax1.text(139-ii, .32, f"P({textsnippet}) = {plusminus3daysprob*100:.1f} %", color='tab:purple')
                ax1.text(139-ii, .29, f"P1-2 = {prob_12*100:.1f} %", color='black')
                ax1.text(139-ii, .27, f"P3-7 = {prob_37*100:.1f} %", color='black')
                ax1.text(139-ii, .25, f"P8-14 = {prob_wk2*100:.1f} %", color='black')
                ax1.text(139-ii, .23, f"P15-21 = {prob_wk3*100:.1f} %", color='black')
                ax1.set_ylim((0, 0.40))
                ax1.set_ylabel('probability density')
                ax1.set_xlabel("Days from forecastday")
                ax2 = ax1.twinx()
                color = 'tab:blue'
                sns.scatterplot(data=DF, x='days_from_then', y='mean_DD', ax=ax2)
                ax2.scatter(x=[mu_0], y=[mean_station.iloc[ii-1][f"{year}"]], c='r')
                ax2.set_ylabel('DD25', color=color)
                ax2.tick_params(axis='y', labelcolor=color)
                ax2.grid(visible=None)
                plt.title(f"{locality} ({river}), prediction on {forecastdate}")
                plt.xlim((110-ii, 155-ii))
                loc = locality.upper().replace(' ', '_')
                outdir = outfolder / f"{river.replace(' ', '_')}"
                outdir.mkdir(parents=True, exist_ok=True)
                if not for_ffmpeg:
                    outfn = (outdir / 
                            f"{loc}_DD25_{year}_{forecastdate}.png")
                else:
                    outfn = (outdir /
                            f"{loc}_DD25_{year}_{icount:02d}.png")
                    icount += 1 
                fig.savefig(outfn, bbox_inches='tight')
            resultrecord = {
                "location": locality,
                "river": river,
                "forecastdate": forecastdate,
                "most likely breakup in (days)": mostlikely,
                "forecasted date": forecasteddate,
                "average breakup date": item.expected_2025,
                "probability of breakup within ± 3 days around forecasted": plusminus3daysprob,
                "probability of breakup within 1 or 2 days": prob_12, 
                "probability of breakup within 3-7 days": prob_37, 
                "probability of breakup within week 2 from now": prob_wk2, 
                "probability of breakup within week 3 from now": prob_wk3
            }
            try:
                results[forecastdate].append(resultrecord)
            except KeyError:
                results[forecastdate] = [resultrecord]

    for forecastdate in results:
        outdf = pd.DataFrame.from_records(results[forecastdate])
        outdf.sort_values(['river', "average breakup date"], inplace=True)
        outfn = f"daily_report_{forecastdate}.csv"
        with open(outfolder / outfn, 'w') as dst:
            outdf.to_csv(dst, float_format='%.2f', index=False)
