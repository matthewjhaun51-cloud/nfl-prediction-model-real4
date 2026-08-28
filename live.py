import requests
URL='https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds'
def get_live_odds(key):
    r=requests.get(URL,params={'apiKey':key,'regions':'us','markets':'spreads,totals','oddsFormat':'american'},timeout=30); r.raise_for_status(); return r.json()
def flatten_odds(raw):
    out=[]
    for g in raw:
        spreads=[]; totals=[]
        for b in g.get('bookmakers',[]):
            for m in b.get('markets',[]):
                if m['key']=='spreads': spreads += m.get('outcomes',[])
                elif m['key']=='totals': totals += m.get('outcomes',[])
        h=g['home_team']; out.append({'game_id':g.get('id'),'home_team':h,'away_team':g['away_team'],'home_spread':next((x.get('point') for x in spreads if x.get('name')==h),None),'total':next((x.get('point') for x in totals),None)})
    return out
