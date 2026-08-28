import os,re
import pandas as pd
import streamlit as st
from sportsdata_client import injuries,schedules
from historical_data import backfill,load_history
from model_engine import build_team_ratings,predict_game,confidence
from live import get_live_odds,flatten_odds
from player_impact import build_player_impact,team_player_adjustment
st.set_page_config(page_title='NFL Quant Model',page_icon='🏈',layout='wide'); st.title('🏈 NFL Quant Prediction Model')
with st.sidebar:
    season=st.number_input('Season',2026,2035,2026); week=st.selectbox('Week',range(1,19),index=0)
    sports_key=st.text_input('SportsDataIO API key',value=st.secrets.get('SPORTSDATA_API_KEY',os.getenv('SPORTSDATA_API_KEY','')),type='password')
    odds_key=st.text_input('The Odds API key',value=st.secrets.get('ODDS_API_KEY',os.getenv('ODDS_API_KEY','')),type='password')
    seasons=st.multiselect('Historical seasons to build',list(range(2018,2026)),default=[2025])
if st.button('⬇️ Build/Update REAL historical data',use_container_width=True):
    if not sports_key: st.error('SportsDataIO key required.'); st.stop()
    bar=st.progress(0); state={'n':0}; total=max(1,len(seasons)*18)
    def prog(s,w): state['n']+=1; bar.progress(min(state['n']/total,1.0))
    with st.spinner('Downloading real team and player game data...'): backfill(seasons,range(1,19),sports_key,prog)
    st.success('Historical data cache updated. No synthetic player/team statistics were generated.')
def norm_team(name):
    s=re.sub(r'[^a-z0-9]','',str(name).lower()); aliases={'arizonacardinals':'ARI','atlantafalcons':'ATL','baltimoreravens':'BAL','buffalobills':'BUF','carolinapanthers':'CAR','chicagobears':'CHI','cincinnatibengals':'CIN','clevelandbrowns':'CLE','dallascowboys':'DAL','denverbroncos':'DEN','detroitlions':'DET','greenbaypackers':'GB','houstontexans':'HOU','indianapoliscolts':'IND','jacksonvillejaguars':'JAX','kansascitychiefs':'KC','lasvegasraiders':'LV','losangeleschargers':'LAC','losangelesrams':'LAR','miamidolphins':'MIA','minnesotavikings':'MIN','newenglandpatriots':'NE','neworleanssaints':'NO','newyorkgiants':'NYG','newyorkjets':'NYJ','philadelphiaeagles':'PHI','pittsburghsteelers':'PIT','sanfrancisco49ers':'SF','seattleseahawks':'SEA','tampabaybuccaneers':'TB','tennesseetitans':'TEN','washingtoncommanders':'WAS','ari':'ARI','atl':'ATL','bal':'BAL','buf':'BUF','car':'CAR','chi':'CHI','cin':'CIN','cle':'CLE','dal':'DAL','den':'DEN','det':'DET','gb':'GB','hou':'HOU','ind':'IND','jax':'JAX','kc':'KC','lv':'LV','lac':'LAC','lar':'LAR','mia':'MIA','min':'MIN','ne':'NE','no':'NO','nyg':'NYG','nyj':'NYJ','phi':'PHI','pit':'PIT','sf':'SF','sea':'SEA','tb':'TB','ten':'TEN','was':'WAS'}; return aliases.get(s,s)
def get_schedule_week(schedule,selected_week):
    df=pd.DataFrame(schedule if isinstance(schedule,list) else [])
    def first(names): return next((x for x in names if x in df.columns),None)
    wc,hc,ac=first(['Week','WeekID','WeekNumber']),first(['HomeTeam','HomeTeamName','HomeTeamKey']),first(['AwayTeam','AwayTeamName','AwayTeamKey'])
    if not all([wc,hc,ac]): return df,None,None,None
    df['_week_num']=pd.to_numeric(df[wc],errors='coerce')
    if df['_week_num'].isna().all(): df['_week_num']=df[wc].astype(str).str.extract(r'(\d+)')[0].astype(float)
    return df[df['_week_num']==int(selected_week)].copy(),hc,ac,wc
refresh=st.button('🔄 REFRESH — RUN LIVE PREDICTIONS',type='primary',use_container_width=True)
if refresh:
    if not sports_key or not odds_key: st.error('Both API keys are required.'); st.stop()
    try:
        inj=injuries(season,week,sports_key); players,teams=load_history()
        if players.empty or teams.empty: st.error('REAL HISTORICAL DATA REQUIRED — build historical data first.'); st.stop()
        wk,hc,ac,wc=get_schedule_week(schedules(season,sports_key),week)
        if hc is None: st.error(f'Could not identify schedule fields. Returned fields: {list(pd.DataFrame(schedules(season,sports_key)).columns)}'); st.stop()
        if wk.empty: st.error(f'No scheduled games found for {season} Week {week}.'); st.stop()
        schedule_pairs={(norm_team(r[ac]),norm_team(r[hc])):(r[ac],r[hc]) for _,r in wk.iterrows()}; odds_games=flatten_odds(get_live_odds(odds_key)); selected=[]; unmatched=[]
        for g in odds_games:
            if (norm_team(g['away_team']),norm_team(g['home_team'])) in schedule_pairs: selected.append(g)
        matched={(norm_team(g['away_team']),norm_team(g['home_team'])) for g in selected}
        for key,names in schedule_pairs.items():
            if key not in matched: unmatched.append(names)
        if not selected:
            st.error(f'No sportsbook games matched {season} Week {week}.'); st.info(f'Week {week} schedule games found: {len(wk)} | Sportsbook games returned: {len(odds_games)} | Matched: 0');
            if unmatched: st.write('Schedule games not found in sportsbook feed:',[f'{a} @ {h}' for a,h in unmatched])
            st.stop()
        if unmatched: st.warning(f'Week {week}: {len(selected)} sportsbook games matched; {len(unmatched)} scheduled games have no current sportsbook market and were excluded.'); st.write('No sportsbook market:',[f'{a} @ {h}' for a,h in unmatched])
        ratings=build_team_ratings(teams,season,week); impact=build_player_impact(players,season,week); adj=team_player_adjustment(impact,inj); rows=[]
        for g in selected:
            if g['home_spread'] is None or g['total'] is None: continue
            m,t,ps,po=predict_game(g['home_team'],g['away_team'],g['home_spread'],g['total'],ratings,adj); sr='BET' if ps>=.58 else 'LEAN' if ps>=.55 else 'PASS'; tr='BET' if po>=.58 else 'LEAN' if po>=.55 else 'PASS'
            bet='—' if sr=='PASS' else (f"{g['home_team']} {g['home_spread']:+g}" if m>-g['home_spread'] else f"{g['away_team']} {-g['home_spread']:+g}"); tbet='—' if tr=='PASS' else (f"Over {g['total']:g}" if t>g['total'] else f"Under {g['total']:g}")
            rows += [dict(game_id=g['game_id'],away_team=g['away_team'],home_team=g['home_team'],market='Spread',market_line=g['home_spread'],model_projection=m,edge=m-(-g['home_spread']),probability=ps,confidence=confidence(ps),recommendation=sr,exact_bet=bet),dict(game_id=g['game_id'],away_team=g['away_team'],home_team=g['home_team'],market='Total',market_line=g['total'],model_projection=t,edge=t-g['total'],probability=po,confidence=confidence(po),recommendation=tr,exact_bet=tbet)]
        df=pd.DataFrame(rows); st.success(f'Live refresh complete: {len(inj)} injury records loaded; {len(impact)} historical player records used; {len(selected)} Week {week} sportsbook games matched.'); st.dataframe(df,use_container_width=True,hide_index=True,column_config={'probability':st.column_config.NumberColumn('Probability',format='%.1f%%'),'edge':st.column_config.NumberColumn('Edge',format='%.2f'),'model_projection':st.column_config.NumberColumn('Model Projection',format='%.2f'),'exact_bet':st.column_config.TextColumn('Exact Bet to Take')})
    except Exception as e: st.error(f'Live prediction refresh failed: {e}')
st.divider(); st.subheader('Data status'); p,t=load_history(); c1,c2=st.columns(2); c1.metric('Historical player-game rows',len(p)); c2.metric('Historical team-game rows',len(t))
