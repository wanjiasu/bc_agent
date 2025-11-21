#!/usr/bin/env python3
"""
API-Football 工具函数集合
提供足球数据API的各种查询功能
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Union, Optional
from langchain_core.tools import tool

# 加载环境变量
load_dotenv()

class APIFootballClient:
    """API-Football客户端类"""
    
    def __init__(self):
        """初始化API客户端"""
        self.api_key = os.getenv('API_FOOTBALL_KEY')
        if not self.api_key:
            raise ValueError("请在.env文件中设置API_FOOTBALL_KEY")
        
        # API-Football的基础URL和请求头
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'v3.football.api-sports.io'
        }
    
    def _make_request(self, endpoint: str, params: dict) -> Optional[dict]:
        """
        发送API请求的通用方法
        
        Args:
            endpoint (str): API端点
            params (dict): 请求参数
            
        Returns:
            dict: API响应数据，失败时返回None
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return None

# 创建全局客户端实例
_client = APIFootballClient()

@tool
def get_fixture_basic_info(fixture_id: int) -> Dict:
    """
    通过fixture_id获取fixture的基本信息包括时间、时区、日期、场地、联赛id、主队id、主队名、客队id、客队名等以便于后续其他工具的参数调用。
    
    Args:
        fixture_id (int): 比赛fixture的唯一标识符
        
    Returns:
        dict: 包含比赛基本信息的字典，包括以下字段：
            - fixture_id (int): 比赛fixture的唯一标识符
            - timezone (str): 比赛时区
            - fixture_date (str): 比赛日期时间
            - venue_name (str): 比赛场地名称
            - venue_city (str): 比赛场地城市
            - league_id (int): 联赛id
            - league_name (str): 联赛名称
            - league_country (str): 联赛所属国家
            - league_season (int): 联赛赛季
            - league_round (str): 联赛轮次
            - home_id (int): 主队id
            - home_name (str): 主队名称
            - away_id (int): 客队id
            - away_name (str): 客队名称
    """
    params = {'id': fixture_id}
    data = _client._make_request('/fixtures', params)
    
    if not data or 'response' not in data or not data['response']:
        return {}
    
    fixture = data['response'][0]
    
    return {
        'fixture_id': fixture['fixture']['id'],
        'timezone': fixture['fixture']['timezone'],
        'fixture_date': fixture['fixture']['date'],
        'venue_name': fixture['fixture']['venue']['name'] if fixture['fixture']['venue'] else None,
        'venue_city': fixture['fixture']['venue']['city'] if fixture['fixture']['venue'] else None,
        'league_id': fixture['league']['id'],
        'league_name': fixture['league']['name'],
        'league_country': fixture['league']['country'],
        'league_season': fixture['league']['season'],
        'league_round': fixture['league']['round'],
        'home_id': fixture['teams']['home']['id'],
        'home_name': fixture['teams']['home']['name'],
        'away_id': fixture['teams']['away']['id'],
        'away_name': fixture['teams']['away']['name'],
    }

@tool
def get_standing_home_info(league_id: int, season: int, home_team_id: int) -> Dict:
    """
    通过联赛id、赛季和主队id获取主队在该赛季的standing信息。
    
    Args:
        league_id (int): 联赛id
        season (int): 赛季年份
        home_team_id (int): 主队id
        
    Returns:
        dict: 包含主队积分榜信息的字典，包括以下字段：
            - league_id (int): 联赛id
            - league_name (str): 联赛名称
            - league_country (str): 联赛所属国家
            - league_season (int): 赛季
            - team_id (int): 球队id
            - team_name (str): 球队名称
            - rank (int): 排名
            - points (int): 积分
            - goalsDiff (int): 净胜球
            - group (str): 所在小组
            - form (str): 近期状态
            - status (str): 排名变化状态
            - description (str): 当前排名说明
            - all_played (int): 总比赛场次
            - all_win (int): 总胜场
            - all_draw (int): 总平局
            - all_lose (int): 总败场
            - all_goals_for (int): 总进球
            - all_goals_against (int): 总失球
            - home_played (int): 主场比赛场次
            - home_win (int): 主场胜场
            - home_draw (int): 主场平局
            - home_lose (int): 主场败场
            - home_goals_for (int): 主场进球
            - home_goals_against (int): 主场失球
            - away_played (int): 客场比赛场次
            - away_win (int): 客场胜场
            - away_draw (int): 客场平局
            - away_lose (int): 客场败场
            - away_goals_for (int): 客场进球
            - away_goals_against (int): 客场失球
    """
    params = {
        'league': league_id,
        'season': season,
        'team': home_team_id
    }
    
    data = _client._make_request('/standings', params)
    
    if not data or 'response' not in data or not data['response']:
        return {}
    
    # 查找指定球队的积分榜信息
    for league_standing in data['response']:
        league_info = league_standing['league']
        
        for standing_group in league_standing['league']['standings']:
            for team_standing in standing_group:
                if team_standing['team']['id'] == home_team_id:
                    return {
                        'league_id': league_info['id'],
                        'league_name': league_info['name'],
                        'league_country': league_info['country'],
                        'league_season': league_info['season'],
                        'team_id': team_standing['team']['id'],
                        'team_name': team_standing['team']['name'],
                        'rank': team_standing['rank'],
                        'points': team_standing['points'],
                        'goalsDiff': team_standing['goalsDiff'],
                        'group': team_standing['group'],
                        'form': team_standing['form'],
                        'status': team_standing['status'],
                        'description': team_standing['description'],
                        'all_played': team_standing['all']['played'],
                        'all_win': team_standing['all']['win'],
                        'all_draw': team_standing['all']['draw'],
                        'all_lose': team_standing['all']['lose'],
                        'all_goals_for': team_standing['all']['goals']['for'],
                        'all_goals_against': team_standing['all']['goals']['against'],
                        'home_played': team_standing['home']['played'],
                        'home_win': team_standing['home']['win'],
                        'home_draw': team_standing['home']['draw'],
                        'home_lose': team_standing['home']['lose'],
                        'home_goals_for': team_standing['home']['goals']['for'],
                        'home_goals_against': team_standing['home']['goals']['against'],
                        'away_played': team_standing['away']['played'],
                        'away_win': team_standing['away']['win'],
                        'away_draw': team_standing['away']['draw'],
                        'away_lose': team_standing['away']['lose'],
                        'away_goals_for': team_standing['away']['goals']['for'],
                        'away_goals_against': team_standing['away']['goals']['against'],
                    }
    
    return {}

@tool
def get_standing_away_info(league_id: int, season: int, away_team_id: int) -> Dict:
    """
    通过联赛id、赛季和客队id获取客队在该赛季的standing信息。
    
    Args:
        league_id (int): 联赛id
        season (int): 赛季年份
        away_team_id (int): 客队id
        
    Returns:
        dict: 包含客队积分榜信息的字典，包含以下字段：
            - league_id (int): 联赛ID
            - league_name (str): 联赛名称
            - league_country (str): 联赛所属国家
            - league_season (int): 赛季年份
            - team_id (int): 球队ID
            - team_name (str): 球队名称
            - rank (int): 排名
            - points (int): 积分
            - goalsDiff (int): 净胜球
            - group (str): 分组信息
            - form (str): 近期状态
            - status (str): 球队状态
            - description (str): 排名描述
            - all_played (int): 总比赛场次
            - all_win (int): 总胜场
            - all_draw (int): 总平场
            - all_lose (int): 总负场
            - all_goals_for (int): 总进球数
            - all_goals_against (int): 总失球数
            - home_played (int): 主场比赛场次
            - home_win (int): 主场胜场
            - home_draw (int): 主场平场
            - home_lose (int): 主场负场
            - home_goals_for (int): 主场进球数
            - home_goals_against (int): 主场失球数
            - away_played (int): 客场比赛场次
            - away_win (int): 客场胜场
            - away_draw (int): 客场平场
            - away_lose (int): 客场负场
            - away_goals_for (int): 客场进球数
            - away_goals_against (int): 客场失球数
    """
    params = {
        'league': league_id,
        'season': season,
        'team': away_team_id
    }
    
    data = _client._make_request('/standings', params)
    
    if not data or 'response' not in data or not data['response']:
        return {}
    
    # 查找指定球队的积分榜信息
    for league_standing in data['response']:
        league_info = league_standing['league']
        
        for standing_group in league_standing['league']['standings']:
            for team_standing in standing_group:
                if team_standing['team']['id'] == away_team_id:
                    return {
                        'league_id': league_info['id'],
                        'league_name': league_info['name'],
                        'league_country': league_info['country'],
                        'league_season': league_info['season'],
                        'team_id': team_standing['team']['id'],
                        'team_name': team_standing['team']['name'],
                        'rank': team_standing['rank'],
                        'points': team_standing['points'],
                        'goalsDiff': team_standing['goalsDiff'],
                        'group': team_standing['group'],
                        'form': team_standing['form'],
                        'status': team_standing['status'],
                        'description': team_standing['description'],
                        'all_played': team_standing['all']['played'],
                        'all_win': team_standing['all']['win'],
                        'all_draw': team_standing['all']['draw'],
                        'all_lose': team_standing['all']['lose'],
                        'all_goals_for': team_standing['all']['goals']['for'],
                        'all_goals_against': team_standing['all']['goals']['against'],
                        'home_played': team_standing['home']['played'],
                        'home_win': team_standing['home']['win'],
                        'home_draw': team_standing['home']['draw'],
                        'home_lose': team_standing['home']['lose'],
                        'home_goals_for': team_standing['home']['goals']['for'],
                        'home_goals_against': team_standing['home']['goals']['against'],
                        'away_played': team_standing['away']['played'],
                        'away_win': team_standing['away']['win'],
                        'away_draw': team_standing['away']['draw'],
                        'away_lose': team_standing['away']['lose'],
                        'away_goals_for': team_standing['away']['goals']['for'],
                        'away_goals_against': team_standing['away']['goals']['against'],
                    }
    
    return {}

@tool
def get_fixture_head2head(home_id: int, away_id: int, last: int = 10) -> List[Dict]:
    """
    通过主队id和客队id获取最近比赛的head-to-head信息。
    
    Args:
        home_id (int): 主队id
        away_id (int): 客队id
        last (int, optional): 最近比赛场次，默认10场
        
    Returns:
        list: 包含历史对战记录的列表，每个元素包含以下字段：
            - home_team_id (int): 主队id
            - away_team_id (int): 客队id
            - fixture_date (str): 比赛日期
            - home_team_winner (bool): 主队是否获胜
            - away_team_winner (bool): 客队是否获胜
            - goals_home (int): 主队进球数
            - goals_away (int): 客队进球数
    """
    params = {
        'h2h': f'{home_id}-{away_id}',
        'last': last,
        'timezone': 'UTC'
    }
    
    data = _client._make_request('/fixtures/headtohead', params)
    
    if not data or 'response' not in data:
        return []
    
    extracted_matches = []
    
    for fixture in data['response']:
        try:
            match_info = {
                'home_team_id': fixture['teams']['home']['id'],
                'away_team_id': fixture['teams']['away']['id'],
                'fixture_date': fixture['fixture']['date'],
                'home_team_winner': fixture['teams']['home']['winner'],
                'away_team_winner': fixture['teams']['away']['winner'],
                'goals_home': fixture['goals']['home'],
                'goals_away': fixture['goals']['away']
            }
            extracted_matches.append(match_info)
        except KeyError:
            continue
    
    return extracted_matches

@tool
def get_home_last_10(home_id: int) -> List[Dict]:
    """
    通过主队id获取最近10场比赛的信息。
    
    Args:
        home_id (int): 主队id
        
    Returns:
        list: 包含最近10场比赛信息的列表，每个元素包含以下字段：
            - fixture_id (int): 比赛ID
            - fixture_date (str): 比赛日期
            - status (str): 比赛状态
            - home_team_id (int): 主队ID
            - home_team_name (str): 主队名称
            - away_team_id (int): 客队ID
            - away_team_name (str): 客队名称
            - home_team_winner (bool): 主队是否获胜
            - away_team_winner (bool): 客队是否获胜
            - goals_home (int): 主队进球数
            - goals_away (int): 客队进球数
            - league_id (int): 联赛ID
            - league_name (str): 联赛名称
            - season (int): 赛季
    """
    params = {
        'team': home_id,
        'last': 10,
        'timezone': 'UTC'
    }
    
    data = _client._make_request('/fixtures', params)
    
    if not data or 'response' not in data:
        return []
    
    extracted_fixtures = []
    
    for fixture in data['response']:
        try:
            fixture_info = {
                'fixture_id': fixture['fixture']['id'],
                'fixture_date': fixture['fixture']['date'],
                'status': fixture['fixture']['status']['short'],
                'home_team_id': fixture['teams']['home']['id'],
                'home_team_name': fixture['teams']['home']['name'],
                'away_team_id': fixture['teams']['away']['id'],
                'away_team_name': fixture['teams']['away']['name'],
                'home_team_winner': fixture['teams']['home']['winner'],
                'away_team_winner': fixture['teams']['away']['winner'],
                'goals_home': fixture['goals']['home'],
                'goals_away': fixture['goals']['away'],
                'league_id': fixture['league']['id'],
                'league_name': fixture['league']['name'],
                'season': fixture['league']['season']
            }
            extracted_fixtures.append(fixture_info)
        except KeyError:
            continue
    
    return extracted_fixtures

@tool
def get_away_last_10(away_id: int) -> List[Dict]:
    """
    通过客队id获取最近10场比赛的信息。
    
    Args:
        away_id (int): 客队id
        
    Returns:
        list: 包含最近10场比赛信息的列表，每个元素包含以下字段：
            - fixture_id (int): 比赛ID
            - fixture_date (str): 比赛日期
            - status (str): 比赛状态
            - home_team_id (int): 主队ID
            - home_team_name (str): 主队名称
            - away_team_id (int): 客队ID
            - away_team_name (str): 客队名称
            - home_team_winner (bool): 主队是否获胜
            - away_team_winner (bool): 客队是否获胜
            - goals_home (int): 主队进球数
            - goals_away (int): 客队进球数
            - league_id (int): 联赛ID
            - league_name (str): 联赛名称
            - season (int): 赛季
    """
    params = {
        'team': away_id,
        'last': 10,
        'timezone': 'UTC'
    }
    
    data = _client._make_request('/fixtures', params)
    
    if not data or 'response' not in data:
        return []
    
    extracted_fixtures = []
    
    for fixture in data['response']:
        try:
            fixture_info = {
                'fixture_id': fixture['fixture']['id'],
                'fixture_date': fixture['fixture']['date'],
                'status': fixture['fixture']['status']['short'],
                'home_team_id': fixture['teams']['home']['id'],
                'home_team_name': fixture['teams']['home']['name'],
                'away_team_id': fixture['teams']['away']['id'],
                'away_team_name': fixture['teams']['away']['name'],
                'home_team_winner': fixture['teams']['home']['winner'],
                'away_team_winner': fixture['teams']['away']['winner'],
                'goals_home': fixture['goals']['home'],
                'goals_away': fixture['goals']['away'],
                'league_id': fixture['league']['id'],
                'league_name': fixture['league']['name'],
                'season': fixture['league']['season']
            }
            extracted_fixtures.append(fixture_info)
        except KeyError:
            continue
    
    return extracted_fixtures

@tool
def get_injuries(fixture_id: int) -> List[Dict]:
    """
    通过fixture_id获取比赛相关的伤病信息。
    
    Args:
        fixture_id (int): 比赛id
        
    Returns:
        list: 包含伤病信息的列表，每个元素包含以下字段：
            - player_id (int): 球员ID
            - player_name (str): 球员姓名
            - player_photo (str): 球员照片链接
            - team_id (int): 球队ID
            - team_name (str): 球队名称
            - team_logo (str): 球队队徽链接
            - injury_type (str): 伤病类型
            - injury_reason (str): 伤病原因
            - fixture_id (int): 比赛ID
            - fixture_date (str): 比赛日期
            - league_id (int): 联赛ID
            - league_name (str): 联赛名称
            - league_country (str): 联赛所属国家
            - league_logo (str): 联赛标志链接
            - season (int): 赛季
    """
    params = {
        'fixture': fixture_id,
        'timezone': 'UTC'
    }
    
    data = _client._make_request('/injuries', params)
    
    if not data or 'response' not in data:
        return []
    
    extracted_injuries = []
    
    for injury in data['response']:
        try:
            injury_info = {
                'player_id': injury['player']['id'],
                'player_name': injury['player']['name'],
                'player_photo': injury['player']['photo'],
                'team_id': injury['team']['id'],
                'team_name': injury['team']['name'],
                'team_logo': injury['team']['logo'],
                'injury_type': injury['player']['type'],
                'injury_reason': injury['player']['reason'],
                'fixture_id': injury['fixture']['id'],
                'fixture_date': injury['fixture']['date'],
                'league_id': injury['league']['id'],
                'league_name': injury['league']['name'],
                'league_country': injury['league']['country'],
                'league_logo': injury['league']['logo'],
                'season': injury['league']['season']
            }
            extracted_injuries.append(injury_info)
        except KeyError:
            continue
    
    return extracted_injuries

@tool
def get_fixture_odds(fixture_id: int) -> Dict:
    """
    通过 fixture_id 获取三家博彩公司（William Hill、Ladbrokes、Bet365）的欧赔。

    Args:
        fixture_id (int): 比赛ID

    Returns:
        dict: 结构为：
            {
              "fixture_id": <int>,
              "odds": {
                "William Hill": {"home": <float>, "draw": <float>, "away": <float>} | None,
                "Ladbrokes": {"home": <float>, "draw": <float>, "away": <float>} | None,
                "Bet365": {"home": <float>, "draw": <float>, "away": <float>} | None
              }
            }
    """
    data = _client._make_request('/odds', {'fixture': fixture_id})
    if not data or 'response' not in data or not data['response']:
        return {
            'fixture_id': fixture_id,
            'odds': {
                'William Hill': None,
                'Ladbrokes': None,
                'Bet365': None,
            }
        }

    try:
        base = data['response'][0]
        bookmakers = base.get('bookmakers', [])
        # 优先使用响应中的 fixture.id
        fx_id = base.get('fixture', {}).get('id', fixture_id)
        allowed = {'William Hill', 'Ladbrokes', 'Bet365'}
        result_odds: Dict[str, Dict[str, float] | None] = {name: None for name in allowed}

        def norm_key(v):
            if v is None:
                return None
            s = str(v).strip().lower()
            if s in {'home', '1'}:
                return 'home'
            if s in {'draw', 'x'}:
                return 'draw'
            if s in {'away', '2'}:
                return 'away'
            return None

        for bm in bookmakers:
            name = bm.get('name')
            if name not in allowed:
                continue
            bets = bm.get('bets', [])
            target = None
            for bet in bets:
                if bet.get('name') == 'Match Winner' or bet.get('id') == 1:
                    target = bet
                    break
            if not target:
                continue

            values = target.get('values', [])
            odds_map: Dict[str, float] = {}
            for item in values:
                key = norm_key(item.get('value'))
                odd = item.get('odd')
                if key is None or odd is None:
                    continue
                try:
                    odds_map[key] = float(str(odd))
                except ValueError:
                    continue

            if odds_map:
                result_odds[name] = odds_map

        return {
            'fixture_id': fx_id,
            'odds': result_odds
        }
    except Exception:
        # 出错时兜底返回空结构
        return {
            'fixture_id': fixture_id,
            'odds': {
                'William Hill': None,
                'Ladbrokes': None,
                'Bet365': None,
            }
        }