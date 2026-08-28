from pathlib import Path
import pandas as pd
from sportsdata_client import player_stats_week,team_stats_week
def backfill(seasons,weeks,key,progress=None):
 out=Path('data/historical');out.mkdir(parents=True,exist_ok=True)
 for season in seasons:
  for week in weeks:
   pf=out/f'player_{season}_{week}.parquet';tf=out/f'team_{season}_{week}.parquet'
   if not pf.exists():pd.DataFrame(player_stats_week(season,week,key)).to_parquet(pf,index=False)
   if not tf.exists():pd.DataFrame(team_stats_week(season,week,key)).to_parquet(tf,index=False)
   if progress:progress(season,week)
def load_history():
 p=list(Path('data/historical').glob('player_*.parquet'));t=list(Path('data/historical').glob('team_*.parquet'))
 return ((pd.concat([pd.read_parquet(x) for x in p],ignore_index=True) if p else pd.DataFrame()),(pd.concat([pd.read_parquet(x) for x in t],ignore_index=True) if t else pd.DataFrame()))
