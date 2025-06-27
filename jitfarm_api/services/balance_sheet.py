from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from jitfarm_api.models.farmModel import COAccount
from jitfarm_api.models.ledgerModel import LedgerEntry
from fastapi import HTTPException
from bson import ObjectId

class BalanceSheetService:
    def __init__(self, db_client):
        self.db = db_client
        self.db_accounts = db_client.accounts
        self.db_ledger = db_client.ledger

    async def get_balance_sheet(
        self,
        client_id: str,
        based_on: str = "until_date",  # or "fiscal_year"
        to_date: Optional[datetime] = None,
        count: int = 1,
        from_year: Optional[int] = None,
        to_year: Optional[int] = None,
        periodicity: str = "monthly",  # or "quarterly", "half-yearly", "yearly"
        consolidate: bool = False,
        hide_group_amounts: bool = False,
    ) -> Dict[str, Any]:
        # 1. Get all accounts for the client
        accounts = []
        async for acc in self.db_accounts.find({"client_id": client_id, "is_active": True}):
            acc["_id"] = str(acc["_id"])
            accounts.append(acc)

        # 2. Group accounts by type
        account_types = {"Asset": [], "Liability": [], "Equity": []}
        for acc in accounts:
            acc_type = acc.get("account_type", "Other")
            if acc_type in account_types:
                account_types[acc_type].append(acc)

        # 3. Determine periods
        periods = []
        if based_on == "until_date":
            if not to_date:
                to_date = datetime.utcnow()
            for i in range(count):
                if periodicity == "monthly":
                    period_end = to_date - timedelta(days=30*i)
                    periods.append(period_end.replace(day=1))
                elif periodicity == "quarterly":
                    period_end = to_date - timedelta(days=90*i)
                    periods.append(period_end.replace(day=1))
                elif periodicity == "half-yearly":
                    period_end = to_date - timedelta(days=182*i)
                    periods.append(period_end.replace(day=1))
                elif periodicity == "yearly":
                    period_end = to_date.replace(year=to_date.year-i, month=1, day=1)
                    periods.append(period_end)
            periods = sorted(periods)
        elif based_on == "fiscal_year":
            if not from_year or not to_year:
                raise HTTPException(status_code=400, detail="from_year and to_year required for fiscal_year mode")
            for y in range(from_year, to_year+1):
                periods.append(datetime(y, 1, 1))

        # 4. For each period, calculate balances
        result = {"Asset": {}, "Liability": {}, "Equity": {}}
        for period in periods:
            period_label = period.strftime("%Y-%m") if periodicity != "yearly" else str(period.year)
            for acc_type, accs in account_types.items():
                total = 0
                rows = []
                for acc in accs:
                    # Sum debits and credits up to this period
                    ledger_query = {
                        "client_id": client_id,
                        "coa_id": acc["_id"],
                        "transaction_date": {"$lte": period.isoformat()}
                    }
                    debit = 0
                    credit = 0
                    async for entry in self.db_ledger.find(ledger_query):
                        debit += float(entry.get("debit_amount", 0))
                        credit += float(entry.get("credit_amount", 0))
                    balance = debit - credit if acc_type == "Asset" else credit - debit
                    if not hide_group_amounts or not acc.get("is_group", False):
                        rows.append({"account": acc["account_name"], "balance": balance})
                    total += balance
                if consolidate:
                    result[acc_type][period_label] = total
                else:
                    result[acc_type][period_label] = rows
        return {
            "status": "success",
            "data": {
                "periods": [p.strftime("%Y-%m") if periodicity != "yearly" else str(p.year) for p in periods],
                "balance_sheet": result
            }
        } 