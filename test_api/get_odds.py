#!/usr/bin/env python3
"""
API-Football 赛前赔率获取脚本（Pre-Match Odds）
仅保留欧赔（Match Winner）且限定书商：William Hill、Ladbrokes、Bet365。
按 fixture_id 获取赔率数据，并将精简后的响应保存为 JSON 文件。
"""

import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class APIFootballClient:
    """API-Football客户端类"""

    def __init__(self):
        self.api_key = os.getenv("API_FOOTBALL_KEY")
        if not self.api_key:
            raise ValueError("请在 .env 文件或环境变量中设置 API_FOOTBALL_KEY")

        # API-Football 基础配置
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "v3.football.api-sports.io",
        }

    def get_odds_by_fixture(self, fixture_id: int) -> dict | None:
        """根据 fixture_id 获取赛前赔率数据。

        Args:
            fixture_id: 比赛 ID

        Returns:
            dict | None: API 完整响应（成功时），否则 None
        """
        url = f"{self.base_url}/odds"
        params = {"fixture": int(fixture_id)}

        print(f"请求URL: {url}")
        print(f"请求参数: {params}")

        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=30)
            print(f"HTTP状态码: {resp.status_code}")
            resp.raise_for_status()

            data = resp.json()
            # 简要统计
            resp_items = data.get("response", [])
            print(f"响应条目数: {len(resp_items)}")
            return data

        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            try:
                print(f"错误响应: {resp.text}")
            except Exception:
                pass
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            try:
                print(f"原始文本: {resp.text[:500]}")
            except Exception:
                pass
            return None

    @staticmethod
    def extract_match_winner_by_bookmakers(
        data: dict,
        allowed_bookmakers: set[str] | None = None,
    ) -> dict | None:
        """从原始赔率响应中提取指定书商的欧赔（Match Winner）。

        Args:
            data: 原始 API 响应（包含顶层 keys: get/parameters/response 等）
            allowed_bookmakers: 允许的书商名称集合；默认 {"William Hill", "Ladbrokes", "Bet365"}

        Returns:
            dict | None: 精简后的响应，仅包含指定书商的 Match Winner；无数据返回 None
        """
        if not data or not isinstance(data, dict):
            print("提取失败：输入数据为空或格式不正确")
            return None

        allowed = allowed_bookmakers or {"William Hill", "Ladbrokes", "Bet365"}

        resp_items = data.get("response", [])
        if not resp_items:
            print("响应中无 'response' 项或为空")
            return None

        # API 通常返回数组，这里只取第一项（单个 fixture 的赔率）
        base = resp_items[0]
        bookmakers = base.get("bookmakers", [])

        filtered_bookmakers = []
        for bm in bookmakers:
            name = bm.get("name")
            if name not in allowed:
                continue

            bets = bm.get("bets", [])
            match_winner_bet = None
            for bet in bets:
                # bet id=1 通常是 "Match Winner"
                if bet.get("name") == "Match Winner" or bet.get("id") == 1:
                    match_winner_bet = {
                        "id": bet.get("id"),
                        "name": bet.get("name"),
                        "values": bet.get("values", []),
                    }
                    break

            if match_winner_bet:
                filtered_bookmakers.append(
                    {
                        "id": bm.get("id"),
                        "name": name,
                        "bets": [match_winner_bet],
                    }
                )

        result = {
            "league": base.get("league"),
            "fixture": base.get("fixture"),
            "update": base.get("update"),
            "bookmakers": filtered_bookmakers,
        }

        print(
            f"已提取书商数量: {len(filtered_bookmakers)} / 总书商: {len(bookmakers)}"
        )
        if not filtered_bookmakers:
            print("未找到指定书商的 Match Winner 欧赔")
        return result

    @staticmethod
    def format_compact_match_winner(
        filtered: dict,
        allowed_bookmakers: set[str] | None = None,
    ) -> dict | None:
        """将提取后的数据整理为精简结果：fixture_id + 三家书商欧赔。

        结构示例：
        {
          "fixture_id": 1439870,
          "odds": {
            "William Hill": {"home": 3.30, "draw": 2.80, "away": 2.15},
            "Ladbrokes": {"home": 3.45, "draw": 2.95, "away": 2.10},
            "Bet365": null
          }
        }

        Returns:
            dict | None: 精简结构；若输入不合法返回 None
        """
        if not filtered or not isinstance(filtered, dict):
            print("整理失败：输入数据为空或格式不正确")
            return None

        allowed = allowed_bookmakers or {"William Hill", "Ladbrokes", "Bet365"}
        fixture = filtered.get("fixture", {})
        fixture_id = fixture.get("id")
        if fixture_id is None:
            print("整理失败：缺少 fixture.id")
            return None

        bm_list = filtered.get("bookmakers", [])

        # 初始化三家书商为 None
        compact_odds: dict[str, dict | None] = {name: None for name in allowed}

        def normalize_outcome_key(v: str | None) -> str | None:
            if v is None:
                return None
            v_clean = str(v).strip().lower()
            if v_clean in {"home", "1"}:
                return "home"
            if v_clean in {"draw", "x"}:
                return "draw"
            if v_clean in {"away", "2"}:
                return "away"
            return None

        for bm in bm_list:
            name = bm.get("name")
            if name not in allowed:
                continue
            bets = bm.get("bets", [])
            target = None
            for bet in bets:
                if bet.get("name") == "Match Winner" or bet.get("id") == 1:
                    target = bet
                    break
            if not target:
                continue

            values = target.get("values", [])
            odds_map: dict[str, float] = {}
            for item in values:
                key = normalize_outcome_key(item.get("value"))
                odd_str = item.get("odd")
                if key is None or odd_str is None:
                    continue
                try:
                    odds_map[key] = float(str(odd_str))
                except ValueError:
                    continue

            # 仅当至少有一个有效项时才记录
            if odds_map:
                compact_odds[name] = odds_map

        result = {
            "fixture_id": fixture_id,
            "odds": compact_odds,
        }

        present = sum(1 for v in compact_odds.values() if v is not None)
        print(f"精简结果包含书商: {present}/{len(allowed)}")
        return result

    @staticmethod
    def save_json(data: dict, output_dir: str, filename: str | None = None) -> str | None:
        """将数据保存为 JSON 文件。

        Args:
            data: 要保存的字典数据
            output_dir: 输出目录
            filename: 文件名；未提供则自动生成

        Returns:
            文件路径或 None
        """
        if not data:
            print("没有数据可保存")
            return None

        os.makedirs(output_dir, exist_ok=True)
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"odds_{timestamp}.json"

        path = os.path.join(output_dir, filename)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"数据已保存到: {path}")
            return path
        except Exception as e:
            print(f"保存文件失败: {e}")
            return None


def main():
    """主函数：获取指定 fixture 的赔率并保存。"""
    fixture_id = 1439870  # 默认使用参考 JSON 的 fixture
    print(f"🔍 开始获取 fixture_id={fixture_id} 的赛前赔率（仅 Match Winner 欧赔）...")

    try:
        client = APIFootballClient()
        odds_data = client.get_odds_by_fixture(fixture_id)

        if odds_data is None:
            print("❌ 获取赔率数据失败或无数据")
            return

        # 仅保留欧赔（Match Winner）且限定书商
        filtered = APIFootballClient.extract_match_winner_by_bookmakers(
            odds_data, {"William Hill", "Ladbrokes", "Bet365"}
        )

        if not filtered:
            print("❌ 未能提取到指定书商的 Match Winner 欧赔")
            return

        output_dir = "/Users/kuriball/Documents/MyProjects/agent/bc_agent/test_api/test_output"
        filename = f"odds_fixture_{fixture_id}_match_winner_eu.json"
        saved = client.save_json(filtered, output_dir, filename)

        if saved:
            print("✅ 精简欧赔（Match Winner）数据保存完成")
        else:
            print("❌ 欧赔数据保存失败")

        # 生成并保存精简整理结果
        compact = APIFootballClient.format_compact_match_winner(
            filtered, {"William Hill", "Ladbrokes", "Bet365"}
        )
        if compact:
            filename_compact = (
                f"odds_fixture_{fixture_id}_match_winner_eu_compact.json"
            )
            saved_compact = client.save_json(compact, output_dir, filename_compact)
            if saved_compact:
                print("✅ 精简整理（fixture_id + 三家欧赔）保存完成")
            else:
                print("❌ 精简整理结果保存失败")

    except Exception as e:
        print(f"❌ 程序执行出错: {e}")


if __name__ == "__main__":
    main()