"""基金数据同步服务 —— 天天基金 + AKShare 双源"""
import json
import logging
import re
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.models.fund import Fund, FundNavHistory
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# 天天基金 API 端点
FUND_ESTIMATE_URL = "http://fundgz.1234567.com.cn/js/{code}.js"
FUND_DETAIL_URL = "http://fund.eastmoney.com/pingzhongdata/{code}.js"
FUND_NAV_HIST_URL = "https://api.fund.eastmoney.com/f10/lsjz"


class FundDataSyncService:
    """基金数据同步"""

    def __init__(self, db: Session):
        self.db = db

    # ----------------------------------------------------------------
    # 基金基本信息
    # ----------------------------------------------------------------

    def sync_fund_info(self, code: str) -> Fund | None:
        """拉取并缓存基金基本信息"""
        import httpx

        fund = self.db.query(Fund).filter_by(code=code).first()
        if fund is None:
            fund = Fund(code=code)
            self.db.add(fund)

        try:
            resp = httpx.get(
                FUND_DETAIL_URL.format(code=code),
                timeout=settings.fund_api_timeout,
            )
            resp.raise_for_status()
            text = resp.text

            # 从 JS 变量中提取基金名称
            name_match = re.search(r'fS_name\s*=\s*"(.+?)"', text)
            if name_match:
                fund.name = name_match.group(1)

            code_match = re.search(r'fS_code\s*=\s*"(.+?)"', text)
            if code_match:
                fund.code = code_match.group(1)

            fund_type_match = re.search(r'fFtype\s*=\s*"(.+?)"', text)
            if fund_type_match:
                fund.fund_type = fund_type_match.group(1)

            fund.last_sync_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.commit()
            logger.info(f"基金信息同步成功: {fund.name} ({code})")
            return fund
        except Exception as e:
            logger.warning(f"基金信息同步失败 {code}: {e}")
            return fund  # 返回已有缓存

    # ----------------------------------------------------------------
    # 实时估值
    # ----------------------------------------------------------------

    def sync_fund_estimate(self, code: str) -> dict:
        """拉取盘中实时估值"""
        import httpx

        result = {"nav": None, "estimate_nav": None, "daily_change": 0.0}
        fund = self.db.query(Fund).filter_by(code=code).first()
        if not fund:
            return result

        try:
            resp = httpx.get(
                FUND_ESTIMATE_URL.format(code=code),
                timeout=settings.fund_api_timeout,
            )
            resp.raise_for_status()
            # 响应格式: jsonpgz({...});
            json_str = re.search(r"jsonpgz\((.+?)\);", resp.text)
            if json_str:
                data = json.loads(json_str.group(1))
                fund.estimate_nav = float(data.get("gsz", 0) or 0)
                fund.estimate_time = data.get("gztime", "")
                fund.daily_change = float(data.get("gszzl", 0) or 0)
                self.db.commit()
                result = {
                    "nav": float(data.get("dwjz", 0) or 0),
                    "estimate_nav": fund.estimate_nav,
                    "daily_change": fund.daily_change,
                }
        except Exception as e:
            logger.warning(f"基金估值同步失败 {code}: {e}")
        return result

    # ----------------------------------------------------------------
    # 历史净值 (最新一条)
    # ----------------------------------------------------------------

    def sync_latest_nav(self, code: str) -> dict:
        """拉取最新单位净值（收盘后）"""
        import httpx

        result = {"nav": None, "nav_date": None, "acc_nav": None, "daily_change": 0.0}
        fund = self.db.query(Fund).filter_by(code=code).first()
        if not fund:
            logger.warning(f"基金 {code} 未录入，跳过净值同步")
            return result

        try:
            # 天天基金 API: 历史净值分页
            params = {
                "callback": "jQuery",
                "fundCode": code,
                "pageIndex": 1,
                "pageSize": 1,
                "startDate": "",
                "endDate": "",
            }
            headers = {"Referer": "http://fund.eastmoney.com/"}
            resp = httpx.get(
                FUND_NAV_HIST_URL,
                params=params,
                headers=headers,
                timeout=settings.fund_api_timeout,
            )
            resp.raise_for_status()
            text = resp.text

            # 解析 JSONP
            json_match = re.search(r"jQuery\((.+)\)", text)
            if not json_match:
                return result
            data = json.loads(json_match.group(1))
            records = data.get("Data", {}).get("LSJZList", [])
            if not records:
                return result

            latest = records[0]
            nav_date = latest.get("FSRQ", "")
            unit_nav = float(latest.get("DWJZ", 0) or 0)
            acc_nav_val = float(latest.get("LJJZ", 0) or 0)
            change_pct = latest.get("JZZZL", "0")
            change_pct = float(change_pct) if change_pct else 0.0

            # 更新基金表
            fund.nav = unit_nav
            fund.nav_date = nav_date
            fund.acc_nav = acc_nav_val
            fund.daily_change = change_pct
            fund.last_sync_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 写入净值历史
            existing = (
                self.db.query(FundNavHistory)
                .filter_by(fund_code=code, nav_date=nav_date)
                .first()
            )
            if not existing:
                self.db.add(
                    FundNavHistory(
                        fund_code=code,
                        nav_date=nav_date,
                        unit_nav=unit_nav,
                        acc_nav=acc_nav_val,
                        daily_change=change_pct,
                    )
                )

            self.db.commit()
            result = {
                "nav": unit_nav,
                "nav_date": nav_date,
                "acc_nav": acc_nav_val,
                "daily_change": change_pct,
            }
            logger.info(f"净值同步成功: {fund.name}({code}) {nav_date} NAV={unit_nav}")
        except Exception as e:
            logger.warning(f"净值同步失败 {code}: {e}")
        return result

    # ----------------------------------------------------------------
    # 批量同步
    # ----------------------------------------------------------------

    def sync_all_held_funds(self, today: date) -> dict:
        """同步所有持仓基金的净值，返回摘要"""
        from app.models.holding import FundHolding

        holdings = (
            self.db.query(FundHolding)
            .filter(FundHolding.status.in_(["holding", "partial_redeem"]))
            .all()
        )
        codes = list(set(h.fund_code for h in holdings))

        # 也同步 active 基金（即使暂未持仓）
        active_funds = self.db.query(Fund).filter_by(is_active=1).all()
        for f in active_funds:
            if f.code not in codes:
                codes.append(f.code)

        summary = {"total": len(codes), "success": 0, "failed": 0}
        for code in codes:
            result = self.sync_latest_nav(code)
            if result["nav"] is not None:
                summary["success"] += 1
            else:
                summary["failed"] += 1

        logger.info(f"批量净值同步完成: {summary}")
        return summary

    # ----------------------------------------------------------------
    # 净值已是否公布
    # ----------------------------------------------------------------

    def is_nav_published(self, code: str, target_date: date) -> bool:
        """检查指定日期净值是否已公布"""
        fund = self.db.query(Fund).filter_by(code=code).first()
        if not fund:
            return False
        return fund.nav_date == target_date.isoformat()
