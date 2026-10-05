import requests
from typing import List, Dict, Any

class OddsAPIService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4/sports"

    def fetch_all_active_sports(self) -> List[Dict[str, Any]]:
        """Fetches all currently active sports and leagues directly from The Odds API."""
        url = f"{self.base_url}?apiKey={self.api_key}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []

    @staticmethod
    def get_global_league_catalog() -> Dict[str, List[Dict[str, str]]]:
        """Categorized global domestic leagues, international tournaments, and UEFA competitions."""
        return {
            "Football": [
                {"key": "soccer_uefa_champs_league", "title": "UEFA Champions League", "category": "UEFA", "region": "Europe"},
                {"key": "soccer_uefa_europa_league", "title": "UEFA Europa League", "category": "UEFA", "region": "Europe"},
                {"key": "soccer_uefa_europa_conference_league", "title": "UEFA Conference League", "category": "UEFA", "region": "Europe"},
                {"key": "soccer_uefa_nations_league", "title": "UEFA Nations League", "category": "International", "region": "Europe"},
                {"key": "soccer_epl", "title": "English Premier League", "category": "Domestic", "region": "England"},
                {"key": "soccer_efl_champ", "title": "EFL Championship", "category": "Domestic", "region": "England"},
                {"key": "soccer_spain_la_liga", "title": "Spanish La Liga", "category": "Domestic", "region": "Spain"},
                {"key": "soccer_spain_segunda_division", "title": "Spanish Segunda Division", "category": "Domestic", "region": "Spain"},
                {"key": "soccer_italy_serie_a", "title": "Italian Serie A", "category": "Domestic", "region": "Italy"},
                {"key": "soccer_italy_serie_b", "title": "Italian Serie B", "category": "Domestic", "region": "Italy"},
                {"key": "soccer_germany_bundesliga", "title": "German Bundesliga", "category": "Domestic", "region": "Germany"},
                {"key": "soccer_germany_bundesliga2", "title": "German 2. Bundesliga", "category": "Domestic", "region": "Germany"},
                {"key": "soccer_france_ligue_one", "title": "French Ligue 1", "category": "Domestic", "region": "France"},
                {"key": "soccer_france_ligue_two", "title": "French Ligue 2", "category": "Domestic", "region": "France"},
                {"key": "soccer_netherlands_eredivisie", "title": "Dutch Eredivisie", "category": "Domestic", "region": "Netherlands"},
                {"key": "soccer_portugal_primeira_liga", "title": "Portuguese Primeira Liga", "category": "Domestic", "region": "Portugal"},
                {"key": "soccer_turkey_super_league", "title": "Turkish Super Lig", "category": "Domestic", "region": "Turkiye"},
                {"key": "soccer_belgium_first_div", "title": "Belgian Pro League", "category": "Domestic", "region": "Belgium"},
                {"key": "soccer_scotland_premiership", "title": "Scottish Premiership", "category": "Domestic", "region": "Scotland"},
                {"key": "soccer_greece_super_league", "title": "Greek Super League", "category": "Domestic", "region": "Greece"},
                {"key": "soccer_switzerland_superleague", "title": "Swiss Super League", "category": "Domestic", "region": "Switzerland"},
                {"key": "soccer_austria_bundesliga", "title": "Austrian Bundesliga", "category": "Domestic", "region": "Austria"},
                {"key": "soccer_denmark_superliga", "title": "Danish Superliga", "category": "Domestic", "region": "Denmark"},
                {"key": "soccer_norway_eliteserien", "title": "Norwegian Eliteserien", "category": "Domestic", "region": "Norway"},
                {"key": "soccer_sweden_allsvenskan", "title": "Swedish Allsvenskan", "category": "Domestic", "region": "Sweden"},
                {"key": "soccer_poland_ekstraklasa", "title": "Polish Ekstraklasa", "category": "Domestic", "region": "Poland"},
                {"key": "soccer_usa_mls", "title": "Major League Soccer (MLS)", "category": "Domestic", "region": "USA/Canada"},
                {"key": "soccer_argentina_primera_division", "title": "Argentine Primera Division", "category": "Domestic", "region": "Argentina"},
                {"key": "soccer_brazil_campeonato", "title": "Brazilian Serie A", "category": "Domestic", "region": "Brazil"},
                {"key": "soccer_mexico_ligamx", "title": "Mexican Liga MX", "category": "Domestic", "region": "Mexico"},
                {"key": "soccer_conmebol_copa_libertadores", "title": "Copa Libertadores", "category": "Continental", "region": "South America"},
                {"key": "soccer_concacaf_champions_league", "title": "CONCACAF Champions Cup", "category": "Continental", "region": "North America"},
                {"key": "soccer_japan_j_league", "title": "Japanese J1 League", "category": "Domestic", "region": "Japan"},
                {"key": "soccer_korea_kleague1", "title": "K League 1", "category": "Domestic", "region": "South Korea"},
                {"key": "soccer_australia_aleague", "title": "Australian A-League", "category": "Domestic", "region": "Australia"},
                {"key": "soccer_saudi_pro_league", "title": "Saudi Pro League", "category": "Domestic", "region": "Saudi Arabia"},
                {"key": "soccer_fifa_world_cup", "title": "FIFA World Cup", "category": "International", "region": "Global"},
                {"key": "soccer_conmebol_copa_america", "title": "Copa America", "category": "International", "region": "Americas"}
            ],
            "Basketball": [
                {"key": "basketball_euroleague", "title": "EuroLeague Basketball", "category": "UEFA", "region": "Europe"},
                {"key": "basketball_eurocup", "title": "EuroCup", "category": "UEFA", "region": "Europe"},
                {"key": "basketball_spain_acb", "title": "Liga ACB", "category": "Domestic", "region": "Spain"},
                {"key": "basketball_germany_bbl", "title": "Basketball Bundesliga (BBL)", "category": "Domestic", "region": "Germany"},
                {"key": "basketball_italy_lega_a", "title": "Lega Basket Serie A", "category": "Domestic", "region": "Italy"},
                {"key": "basketball_turkey_bsl", "title": "Basketbol Super Ligi", "category": "Domestic", "region": "Turkiye"},
                {"key": "basketball_france_lnb", "title": "LNB Pro A", "category": "Domestic", "region": "France"},
                {"key": "basketball_greece_basket_league", "title": "Greek Basket League", "category": "Domestic", "region": "Greece"},
                {"key": "basketball_brazil_nbb", "title": "Novo Basquete Brasil (NBB)", "category": "Domestic", "region": "Brazil"},
                {"key": "basketball_argentina_liga_nacional", "title": "Liga Nacional de Basquet", "category": "Domestic", "region": "Argentina"},
                {"key": "basketball_australia_nbl", "title": "Australian NBL", "category": "Domestic", "region": "Australia"},
                {"key": "basketball_china_cba", "title": "Chinese Basketball Association (CBA)", "category": "Domestic", "region": "China"},
                {"key": "basketball_japan_bleague", "title": "Japanese B.League", "category": "Domestic", "region": "Japan"},
                {"key": "basketball_korea_kbl", "title": "Korean Basketball League (KBL)", "category": "Domestic", "region": "South Korea"},
                {"key": "basketball_fiba_world_cup", "title": "FIBA World Cup", "category": "International", "region": "Global"}
            ]
        }

    def get_fixtures_and_odds(self, sport_key: str, regions: str = "eu,us", markets: str = "h2h,totals") -> List[Dict[str, Any]]:
        """Fetches pre-match odds for a specified domestic league or international tournament."""
        url = f"{self.base_url}/{sport_key}/odds/?apiKey={self.api_key}&regions={regions}&markets={markets}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass
        return []