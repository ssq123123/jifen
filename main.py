from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import re

# 定义玩家的位置和初始分数
PLAYERS = {
    "东": {"score": 100, "dark_kang_count": 0, "zhi_kang_count": 0},
    "南": {"score": 100, "dark_kang_count": 0, "zhi_kang_count": 0},
    "西": {"score": 100, "dark_kang_count": 0, "zhi_kang_count": 0},
    "北": {"score": 100, "dark_kang_count": 0, "zhi_kang_count": 0},
}

# 当前玩家位置
current_player = None

@register("mahjong", "-developer", "麻将计分插件", "1.0.0", "https://astrbot.app")
class MahjongPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # 注册指令，确定位置
    @filter.command("开始")
    async def set_position(self, event: AstrMessageEvent, position: str):
        global current_player
        if position in PLAYERS:
            current_player = position
            # 根据当前玩家位置确定其他玩家位置
            players_order = list(PLAYERS.keys())
            current_index = players_order.index(current_player)
            up_index = (current_index - 1) % 4
            down_index = (current_index + 1) % 4
            opposite_index = (current_index + 2) % 4
            up_player = players_order[up_index]
            down_player = players_order[down_index]
            opposite_player = players_order[opposite_index]

            response = f"🎲【牌桌定位完成】\n🗺️ 方位图鉴：\n[👑主人] {current_player} ➜ 当前分数：💰{PLAYERS[current_player]['score']}\n"
            response += f"[🔼上家] {up_player} ➜ 当前分数：💰{PLAYERS[up_player]['score']}\n"
            response += f"[⏹对家] {opposite_player} ➜ 当前分数：💰{PLAYERS[opposite_player]['score']}\n"
            response += f"[🔽下家] {down_player} ➜ 当前分数：💰{PLAYERS[down_player]['score']}\n\n"
            response += "🪄小精灵：牌局已初始化完成，祝主人旗开得胜！✨"
            yield event.plain_result(response)
        else:
            yield event.plain_result("请选择有效的位置：东/南/西/北")

    # 胡牌场景
    @filter.command("自摸")
    async def hu_zi_mo(self, event: AstrMessageEvent, player: str, score: int):
        if player in PLAYERS:
            # 计算加分
            total_add = (1 + score) * 3
            PLAYERS[player]["score"] += total_add

            # 其他玩家减分
            for p in PLAYERS:
                if p != player:
                    PLAYERS[p]["score"] -= (score * 3) // 3  # 平均减分

            response = f"【自摸捷报】\n🏆 {player}自摸中{score}码（1+{score}）×3=+{total_add}分\n\n"
            response += "💰 分数变动：\n"
            for p in PLAYERS:
                if p == player:
                    response += f"{p} ➕{total_add}（现💰{PLAYERS[p]['score']}）"
                else:
                    subtract = (score * 3) // 3
                    response += f"{p} ➖{subtract}（现💰{PLAYERS[p]['score']}）"
                response += "\n"

            yield event.plain_result(response)
        else:
            yield event.plain_result("请选择有效的位置：东/南/西/北")

    # 直杠场景
    @filter.command("杠")
    async def zhi_kang(self, event: AstrMessageEvent, player: str, target: str):
        if player in PLAYERS and target in PLAYERS:
            PLAYERS[player]["score"] += 3
            PLAYERS[target]["score"] -= 3

            PLAYERS[player]["zhi_kang_count"] += 1

            response = f"【直杠交锋】\n🔥 {player}直杠{target}\n\n"
            response += f"💸 即时结算：\n{player} ➕3（现💰{PLAYERS[player]['score']}）\n"
            response += f"{target} ➖3（现💰{PLAYERS[target]['score']}）\n\n"
            response += f"📌 历史记录：{player}已累计直杠{PLAYERS[player]['zhi_kang_count']}次"

            yield event.plain_result(response)
        else:
            yield event.plain_result("请选择有效的位置：东/南/西/北")

    # 暗杠场景
    @filter.command("暗杠")
    async def dark_kang(self, event: AstrMessageEvent, player: str):
        if player in PLAYERS:
            PLAYERS[player]["score"] += 6
            PLAYERS[player]["dark_kang_count"] += 1

            for p in PLAYERS:
                if p != player:
                    PLAYERS[p]["score"] -= 2

            response = f"【暗藏玄机】\n🌑 {player}发动暗杠\n\n"
            response += f"📉 全桌结算：\n{player} ➕6（现💰{PLAYERS[player]['score']}）\n"
            for p in PLAYERS:
                if p != player:
                    response += f"{p} ➖2（现💰{PLAYERS[p]['score']}）\n"
            response += f"⚠️ 暗杠预警：{player}已累计暗杠{PLAYERS[player]['dark_kang_count']}次"

            yield event.plain_result(response)
        else:
            yield event.plain_result("请选择有效的位置：东/南/西/北")

    # 补杠场景
    @filter.command("补杠")
    async def bu_kang(self, event: AstrMessageEvent, player: str):
        if player in PLAYERS:
            PLAYERS[player]["score"] += 3

            for p in PLAYERS:
                if p != player:
                    PLAYERS[p]["score"] -= 1

            response = f"【补杠风云】\n🛠️ {player}完成补杠\n\n"
            response += f"📌 全局影响：\n{player} ➕3（现💰{PLAYERS[player]['score']}）\n"
            for p in PLAYERS:
                if p != player:
                    response += f"{p} ➖1（现💰{PLAYERS[p]['score']}）\n"
            response += f"📆 本局已累计补杠：{PLAYERS[player]['zhi_kang_count'] + PLAYERS[player]['dark_kang_count'] + 1}次"

            yield event.plain_result(response)
        else:
            yield event.plain_result("请选择有效的位置：东/南/西/北")

    # 补杠被抢场景
    @filter.command("抢杠")
    async def qiang_kang(self, event: AstrMessageEvent, player: str, target: str, score: int):
        if player in PLAYERS and target in PLAYERS:
            total_add = score * 3
            PLAYERS[target]["score"] -= total_add
            PLAYERS[player]["score"] += total_add

            response = f"【惊天逆转】\n💥 {player}抢杠{target}！中{score}码\n\n"
            response += f"🔄 分数重算：\n{target} ➖{total_add}（现💰{PLAYERS[target]['score']}）\n"
            response += f"{player} ➕{total_add}（现💰{PLAYERS[player]['score']}）\n\n"
            response += "❗ 特殊提示：补杠有风险，杠牌需谨慎！"

            yield event.plain_result(response)
        else:
            yield event.plain_result("请选择有效的位置：东/南/西/北")

    # 直杠杠开场景
    @filter.command("杠开")
    async def zhi_kang_kai(self, event: AstrMessageEvent, player: str, target: str, score: int):
        if player in PLAYERS and target in PLAYERS:
            total_add = score * 3 + 3  # 包括自摸加分
            PLAYERS[player]["score"] += total_add
            PLAYERS[target]["score"] -= total_add

            PLAYERS[player]["zhi_kang_count"] += 1

            response = f"【杠上开花】\n🌸 {player}直杠{target}后杠开！中{score}码\n\n"
            response += f"💥 超级结算：\n{player} ➕{total_add}（现💰{PLAYERS[player]['score']}）\n"
            response += f"{target} ➖{total_add}（现💰{PLAYERS[target]['score']}）\n\n"
            response += f"🏅 成就解锁：{player}达成「杠开大师」称号"

            yield event.plain_result(response)
        else:
            yield event.plain_result("请选择有效的位置：东/南/西/北")