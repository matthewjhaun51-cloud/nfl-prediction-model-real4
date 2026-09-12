import requests
BASE='https://api.sportsdata.io/v3/nfl'

class SportsDataError(Exception):
    def __init__(self, message, status_code=None, url=None):
        super().__init__(message)
        self.status_code = status_code
        self.url = url

def get(path, key):
    if not key:
        raise SportsDataError('SPORTSDATA_API_KEY is missing.')
    url=f'{BASE}/{path}'
    r=requests.get(url, headers={'Ocp-Apim-Subscription-Key':key}, timeout=30)
    if r.status_code >= 400:
        raise SportsDataError(f'HTTP {r.status_code}: {r.text[:500]}', r.status_code, url)
    return r.json()

def injuries(season, week, key):
    return get(f'stats/json/Injuries/{season}/{week}', key)

def player_stats_week(season, week, key):
    return get(f'stats/json/PlayerGameStatsByWeekFinal/{season}/{week}', key)

def team_stats_week(season, week, key):
    return get(f'scores/json/TeamGameStats/{season}/{week}', key)

def schedules(season, key):
    return get(f'scores/json/Schedules/{season}', key)

def depth_charts_active(key):
    return get('scores/json/DepthCharts', key)
