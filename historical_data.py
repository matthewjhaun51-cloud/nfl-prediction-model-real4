from pathlib import Path
import pandas as pd
from sportsdata_client import player_stats_week, team_stats_week, SportsDataError

def backfill(seasons, weeks, key, progress=None):
    out=Path('data/historical')
    out.mkdir(parents=True, exist_ok=True)
    results=[]
    for season in seasons:
        status={'season':season,'success':0,'skipped':0,'errors':[]}
        blocked=False
        for week in weeks:
            pf=out/f'player_{season}_{week}.parquet'
            tf=out/f'team_{season}_{week}.parquet'
            if pf.exists() and tf.exists():
                status['success']+=1
                if progress: progress(season,week,'cached',None)
                continue
            if blocked:
                status['skipped']+=1
                if progress: progress(season,week,'skipped','season access denied')
                continue
            try:
                players=pd.DataFrame(player_stats_week(season,week,key))
                teams=pd.DataFrame(team_stats_week(season,week,key))
                players.to_parquet(pf,index=False)
                teams.to_parquet(tf,index=False)
                status['success']+=1
                if progress: progress(season,week,'success',None)
            except SportsDataError as e:
                if e.status_code in (401,403):
                    blocked=True
                    status['skipped']+=1
                    status['errors'].append(f'Week {week}: HTTP {e.status_code} - historical access denied')
                    if progress: progress(season,week,'blocked',f'HTTP {e.status_code}')
                    continue
                raise
        results.append(status)
    return results

def load_history():
    p=list(Path('data/historical').glob('player_*.parquet'))
    t=list(Path('data/historical').glob('team_*.parquet'))
    players=pd.concat([pd.read_parquet(x) for x in p],ignore_index=True) if p else pd.DataFrame()
    teams=pd.concat([pd.read_parquet(x) for x in t],ignore_index=True) if t else pd.DataFrame()
    return players,teams
