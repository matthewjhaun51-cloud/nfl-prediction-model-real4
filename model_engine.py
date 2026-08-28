import numpy as np,pandas as pd
def num(s):return pd.to_numeric(s,errors='coerce').fillna(0)
def build_team_ratings(d,season,week):
 if d.empty:return {}
 d=d[(d.Season<season)|((d.Season==season)&(d.Week<week))].copy()
 if d.empty:return {}
 for c in ['PointDifferential','OffensiveYardsPerPlay','Turnovers','OpponentTurnovers','PassingYards','RushingYards']:
  if c not in d:d[c]=0
  d[c]=num(d[c])
 d['w']=d.groupby('Team').cumcount()+1
 def f(g):
  w=np.sqrt(g.w);return {'margin':np.average(g.PointDifferential,weights=w),'ypp':np.average(g.OffensiveYardsPerPlay,weights=w),'turnover':np.average(g.Turnovers-g.OpponentTurnovers,weights=w),'pass':np.average(g.PassingYards,weights=w),'rush':np.average(g.RushingYards,weights=w)}
 return {t:f(g) for t,g in d.groupby('Team')}
def sigmoid(x):return 1/(1+np.exp(-np.clip(x,-20,20)))
def predict_game(home,away,line,total,r,adj):
 h=r.get(home,{});a=r.get(away,{});m=3+.55*(h.get('margin',0)-a.get('margin',0))+.9*(h.get('ypp',0)-a.get('ypp',0))+.18*(h.get('turnover',0)-a.get('turnover',0))+.004*(h.get('pass',0)-a.get('pass',0));t=43+.012*(h.get('pass',0)+a.get('pass',0))+.01*(h.get('rush',0)+a.get('rush',0));m-=adj.get(home,0)*.12;m+=adj.get(away,0)*.12;t-=(adj.get(home,0)+adj.get(away,0))*.05;return m,t,float(sigmoid((m+line)*.22)),float(sigmoid((t-total)*.20))
def confidence(p):return 'Extremely Strong' if p>=.67 else 'Very Strong' if p>=.62 else 'Strong' if p>=.58 else 'Moderate' if p>=.55 else 'Small Edge' if p>=.52 else 'Very Weak/Pass'
