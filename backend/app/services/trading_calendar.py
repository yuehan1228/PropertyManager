"""交易日历服务 —— 判读 A 股交易日、节假日顺延"""
import logging
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.calendar import TradingCalendar

logger = logging.getLogger(__name__)


class TradingCalendarService:
    """交易日历核心服务"""

    def __init__(self, db: Session):
        self.db = db

    # ----------------------------------------------------------------
    # 查询
    # ----------------------------------------------------------------

    def is_trading_day(self, d: date) -> bool:
        """查询某日是否为 A 股交易日"""
        d_str = d.isoformat()
        row = self.db.query(TradingCalendar).filter_by(date=d_str).first()
        if row:
            return row.is_trade == 1

        # 缓存未命中 → 本地推算 + 写入缓存
        result = self._compute_trading_day(d)
        self._cache_result(d, result)
        return result

    def get_next_trading_day(self, from_date: date, offset: int = 1) -> date:
        """获取 from_date 之后的第 N 个交易日"""
        d = from_date
        count = 0
        while count < offset:
            d += timedelta(days=1)
            if self.is_trading_day(d):
                count += 1
        return d

    def get_previous_trading_day(self, from_date: date) -> date:
        """获取 from_date 之前的最近交易日"""
        d = from_date - timedelta(days=1)
        while not self.is_trading_day(d):
            d -= timedelta(days=1)
        return d

    # ----------------------------------------------------------------
    # 远程同步
    # ----------------------------------------------------------------

    def sync_calendar_from_remote(self, year: int) -> int:
        """从 AKShare 拉取全年交易日历并写入缓存，返回写入条数"""
        try:
            import akshare as ak
            df = ak.tool_trade_date_hist_sina()
        except Exception:
            logger.warning("AKShare 交易日历拉取失败，使用本地推算")
            return self._build_fallback_calendar(year)

        if df is None or df.empty:
            return self._build_fallback_calendar(year)

        trade_dates = set()
        for _, row in df.iterrows():
            try:
                d_val = row["trade_date"]
                if isinstance(d_val, date):
                    trade_dates.add(d_val)
                else:
                    trade_dates.add(date.fromisoformat(str(d_val)[:10]))
            except (ValueError, KeyError):
                continue

        count = 0
        for d in self._date_range(year):
            d_str = d.isoformat()
            is_trade = 1 if d in trade_dates else 0
            holiday = None if is_trade or d.weekday() < 5 else "周末"
            self.db.merge(
                TradingCalendar(
                    date=d_str,
                    is_trade=is_trade,
                    week_day=d.weekday(),
                    holiday=holiday,
                    year=year,
                )
            )
            count += 1

        self.db.commit()
        logger.info(f"交易日历同步完成：{year}年，{count}条")
        return count

    # ----------------------------------------------------------------
    # 内部实现
    # ----------------------------------------------------------------

    def _compute_trading_day(self, d: date) -> bool:
        """本地推算：非周末 + 未标记为非交易日"""
        if d.weekday() >= 5:
            return False
        # 如果缓存中没有但非周末，默认视为交易日
        return True

    def _cache_result(self, d: date, is_trade: bool):
        row = TradingCalendar(
            date=d.isoformat(),
            is_trade=1 if is_trade else 0,
            week_day=d.weekday(),
            holiday=None if is_trade else "周末",
            year=d.year,
        )
        self.db.add(row)
        self.db.commit()

    def _build_fallback_calendar(self, year: int) -> int:
        """无网络时纯周末推算"""
        count = 0
        for d in self._date_range(year):
            is_trade = d.weekday() < 5
            self.db.merge(
                TradingCalendar(
                    date=d.isoformat(),
                    is_trade=1 if is_trade else 0,
                    week_day=d.weekday(),
                    holiday=None if is_trade else "周末",
                    year=year,
                )
            )
            count += 1
        self.db.commit()
        return count

    @staticmethod
    def _date_range(year: int):
        d = date(year, 1, 1)
        end = date(year, 12, 31)
        while d <= end:
            yield d
            d += timedelta(days=1)
