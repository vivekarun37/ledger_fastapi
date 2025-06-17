from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from bson import ObjectId
from pymongo.errors import PyMongoError
import json
from fastapi import HTTPException
from jitfarm_api.utils import log_error

class ProfitLossService:
    def __init__(self, db_client):
        self.db = db_client
        self.db_transactions = db_client.transactions

    async def get_profit_loss(
        self,
        client_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Optional[Exception]]:
        try:
            # Set default date range to last 3 months if not specified
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=90)

            # Build the query
            query = {
                "client_id": client_id,
                "date": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            }

            # Get all transactions for the period
            transactions = []
            async for transaction in self.db_transactions.find(query):
                transaction["_id"] = str(transaction["_id"])
                transactions.append(transaction)

            # Group transactions by type (income/expense) and date
            income_by_period = {}
            expense_by_period = {}

            for transaction in transactions:
                date = datetime.fromisoformat(transaction["date"])
                period_key = self._get_period_key(date, group_by)
                amount = float(transaction["amount"])

                if transaction["transaction_type"] == "income":
                    if period_key not in income_by_period:
                        income_by_period[period_key] = 0
                    income_by_period[period_key] += amount
                else:  # expense
                    if period_key not in expense_by_period:
                        expense_by_period[period_key] = 0
                    expense_by_period[period_key] += amount

            # Calculate profit/loss for each period
            profit_loss_by_period = {}
            all_periods = sorted(set(list(income_by_period.keys()) + list(expense_by_period.keys())))

            for period in all_periods:
                income = income_by_period.get(period, 0)
                expense = expense_by_period.get(period, 0)
                profit_loss_by_period[period] = income - expense

            # Calculate totals
            total_income = sum(income_by_period.values())
            total_expense = sum(expense_by_period.values())
            total_profit_loss = total_income - total_expense

            # Get detailed breakdown by category
            category_breakdown = await self._get_category_breakdown(transactions)

            return {
                "status": "success",
                "data": {
                    "period": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                        "group_by": group_by
                    },
                    "income": {
                        "by_period": income_by_period,
                        "total": total_income
                    },
                    "expense": {
                        "by_period": expense_by_period,
                        "total": total_expense
                    },
                    "profit_loss": {
                        "by_period": profit_loss_by_period,
                        "total": total_profit_loss
                    },
                    "category_breakdown": category_breakdown
                }
            }, None

        except PyMongoError as e:
            error_msg = f"Database error while retrieving P&L data: {str(e)}"
            return {"status": "error", "message": error_msg}, e
        except Exception as e:
            error_msg = f"Unexpected error retrieving P&L data: {str(e)}"
            return {"status": "error", "message": error_msg}, e

    def _get_period_key(self, date: datetime, group_by: Optional[str] = None) -> str:
        if group_by == "month":
            return date.strftime("%Y-%m")
        elif group_by == "quarter":
            quarter = (date.month - 1) // 3 + 1
            return f"{date.year}-Q{quarter}"
        elif group_by == "year":
            return str(date.year)
        else:
            return date.strftime("%Y-%m")

    async def _get_category_breakdown(self, transactions: List[Dict]) -> Dict:
        income_categories = {}
        expense_categories = {}

        for transaction in transactions:
            category = transaction.get("category", "Uncategorized")
            amount = float(transaction["amount"])

            if transaction["transaction_type"] == "income":
                if category not in income_categories:
                    income_categories[category] = 0
                income_categories[category] += amount
            else:  # expense
                if category not in expense_categories:
                    expense_categories[category] = 0
                expense_categories[category] += amount

        return {
            "income": income_categories,
            "expense": expense_categories
        } 