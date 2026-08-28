import os,streamlit as st,pandas as pd
from sportsdata_client import injuries,depth_charts_active,schedules
from historical_data import backfill,load_history
from model_engine import build_team_ratings,predict_game,confidence
from live import get_live_odds,flatten_odds
from player_impact import build_player_impact,team_player_adjustment
st.set_page_config(page_title='NFL Quant Model',page_icon='🏈',layout='wide');st.title('🏈 NFL Quant Prediction Model')
with st.sidebar:
 season=st.number_input('Season',2026,2035,2026);week=st.selectbox('Week',range(1,19),index=0);sports_key=st.text_input('SportsDataIO API key',value=st.secrets.get('SPORTSDATA_API_KEY',os.getenv('SPORTSDATA_API_KEY','')),type='password');odds_key=st.text_input('The Odds API key',value=st.secrets.get('ODDS_API_KEY',os.getenv('ODDS_API_KEY','')),type='password');seasons=st.multiselect('Historical seasons to build',list(range(2018,2026)),default=[2025])
if st.button('⬇️ Build/Update REAL historical data',use_container_width=True):
 if not sports_key:st.error('SportsDataIO key required.');st.stop()
 bar=st.progress(0);state={'n':0};total=max(1,len(seasons)*18)
 def prog(s,w):state['n']+=1;bar.progress(min(state['n']/total,1.0))
 with st.spinner('Downloading real team and player game data...'):backfill(seasons,range(1,19),sports_key,prog)
 st.success('Historical data cache updated. No synthetic player/team statistics were generated.')
refresh=st.button('🔄 REFRESH — RUN LIVE PREDICTIONS',type='primary',use_container_width=True)
if refresh:
 if not sports_key or not odds_key:st.error('Both API keys are required.');st.stop()
 try:
  inj=injuries(season,week,sports_key);players,teams=load_history()
  if players.empty or teams.empty:st.error('REAL HISTORICAL DATA REQUIRED — build historical data first.');st.stop()
  sched=pd.DataFrame(schedules(season,sports_key));
  if sched.empty:st.error(f'No schedule returned for {season}.');st.stop()
  def col(names):return next((x for x in names if x in sched.columns),None)
  wc,hc,ac=col(['Week','WeekID','WeekNumber']),col(['HomeTeam','HomeTeamName','HomeTeamKey']),col(['AwayTeam','AwayTeamName','AwayTeamKey'])
  if not all([wc,hc,ac]):st.error(f'Could not identify schedule fields: {list(sched.columns)}');st.stop()
  sched['_week']=pd.to_numeric(sched[wc],errors='coerce');wk=sched[sched['_week']==int(week)]
  if wk.empty:st.error(f'No scheduled games found for {season} Week {week}.');st.stop()
  def norm(x):return ''.join(c.lower() for c in str(x) if c.isalnum())
  pairs={(norm(r[ac]),norm(r[hc])) for _,r in wk.iterrows()};games=[g for g in flatten_odds(get_live_odds(odds_key)) if (norm(g['away_team']),norm(g['home_team'])) in pairs]
  if not games:st.error(f'No sportsbook games matched {season} Week {week}.');st.stop()
  ratings=build_team_ratings(teams,season,week);impact=build_player_impact(players,season,week);adj=team_player_adjustment(impact,inj)
  rows=[]
  for g in games:
   if g['home_spread'] is None or g['total'] is None:continue
   m,t,ps,po=predict_game(g['home_team'],g['away_team'],g['home_spread'],g['total'],ratings,adj);sr='BET' if ps>=.58 else 'LEAN' if ps>=.55 else 'PASS';tr='BET' if po>=.58 else 'LEAN' if po>=.55 else 'PASS'
   bet='—' if sr=='PASS' else (f"{g['home_team']} {g['home_spread']:+g}" if m>-g['home_spread'] else f"{g['away_team']} {-g['home_spread']:+g}");tbet='—' if tr=='PASS' else (f"Over {g['total']:g}" if t>g['total'] else f"Under {g['total']:g}")
   rows += [dict(game_id=g['game_id'],away_team=g['away_team'],home_team=g['home_team'],market='Spread',market_line=g['home_spread'],model_projection=-m,edge=(-m)-g['home_spread'],probability=ps,confidence=confidence(ps),recommendation=sr,exact_bet=bet),dict(game_id=g['game_id'],away_team=g['away_team'],home_team=g['home_team'],market='Total',market_line=g['total'],model_projection=t,edge=t-g['total'],probability=po,confidence=confidence(po),recommendation=tr,exact_bet=tbet)]
  df=pd.DataFrame(rows);st.success(f'Live refresh complete: {len(inj)} injury records loaded; {len(impact)} historical player records used; {len(games)} Week {week} games matched.');st.dataframe(df,use_container_width=True,hide_index=True,column_config={'probability':st.column_config.NumberColumn('Probability',format='%.1f%%'),'exact_bet':st.column_config.TextColumn('Exact Bet to Take')})
 except Exception as e:st.error(f'Live prediction refresh failed: {e}')
st.divider();st.subheader('Data status');p,t=load_history();c1,c2=st.columns(2);c1.metric('Historical player-game rows',len(p));c2.metric('Historical team-game rows',len(t))
