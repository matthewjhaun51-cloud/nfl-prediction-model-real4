import requests
BASE='https://api.sportsdata.io/v3/nfl'
class SportsDataError(Exception): pass
def get(path,key):
 if not key: raise SportsDataError('SPORTSDATA_API_KEY is missing.')
 r=requests.get(f'{BASE}/{path}',headers={'Ocp-Apim-Subscription-Key':key},timeout=30); r.raise_for_status(); return r.json()
def injuries(season,week,key): return get(f'stats/json/Injuries/{season}/{week}',key)
def player_stats_week(season,week,key): return get(f'stats/json/PlayerGameStatsByWeekFinal/{season}/{week}',key)
def team_stats_week(season,week,key): return get(f'scores/json/TeamGameStats/{season}/{week}',key)
def schedules(season,key): return get(f'scores/json/Schedules/{season}',key)
def depth_charts_active(key): return get('scores/json/DepthCharts',key)
