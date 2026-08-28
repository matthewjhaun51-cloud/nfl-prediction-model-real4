import pandas as pd
def num(d,c): return pd.to_numeric(d[c],errors='coerce').fillna(0) if c in d else pd.Series(0,index=d.index)
def build_player_impact(d,season,week):
 if d.empty:return pd.DataFrame()
 d=d[(d.Season<season)|((d.Season==season)&(d.Week<week))].copy();
 if d.empty:return pd.DataFrame()
 d['usage']=num(d,'PassingAttempts')+num(d,'RushingAttempts')+num(d,'Targets')
 d['production']=num(d,'PassingYards')/20+num(d,'PassingTouchdowns')*6-num(d,'PassingInterceptions')*5+num(d,'RushingYards')/10+num(d,'ReceivingYards')/10+num(d,'RushingTouchdowns')*6+num(d,'ReceivingTouchdowns')*6
 d['impact_raw']=d.production+.25*d.usage
 keys=[x for x in ['PlayerID','Team','Position'] if x in d]
 g=d.groupby(keys).agg(impact_raw=('impact_raw','sum'),games=('impact_raw','size'),usage=('usage','mean')).reset_index();g['impact']=g.impact_raw/g.games*(g.games/(g.games+5));return g
def team_player_adjustment(impact,injuries,depth=None):
 if impact.empty:return {}
 out={}
 for x in injuries or []:
  h=impact[impact.PlayerID==x.get('PlayerID')] if 'PlayerID' in impact else pd.DataFrame()
  if h.empty:continue
  status=str(x.get('Status') or x.get('InjuryStatus') or '').lower();factor=1 if any(z in status for z in ['out','ir','inactive']) else .5 if any(z in status for z in ['questionable','doubtful','limited']) else 0
  if factor:out[h.iloc[0].Team]=out.get(h.iloc[0].Team,0)+float(h.iloc[0].impact)*factor
 return out
