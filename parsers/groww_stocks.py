import io
import openpyxl
from datetime import datetime


def parse(file_bytes: bytes) -> list[dict]:
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    ws = wb.active
    result = []
    for row in ws.iter_rows(min_row=7, values_only=True):  # row 6 is header
        if not any(row):
            continue
        try:
            name     = str(row[0]).strip()   # Col A: Stock name
            txn_type = str(row[3]).strip()   # Col D: Type (BUY/SELL)
            units    = float(row[4])         # Col E: Quantity
            amount   = float(row[5])         # Col F: Value (units * price)
            date_val = row[8]                # Col I: Execution date and time
            status   = str(row[9]).strip() if row[9] else ''  # Col J: Order status

            if status.lower() != 'executed':
                continue

            # Parse date — stored as text "DD-MM-YYYY HH:MM AM/PM"
            if isinstance(date_val, datetime):
                date = date_val.strftime('%Y-%m-%d')
            else:
                date = datetime.strptime(str(date_val).strip(), '%d-%m-%Y %I:%M %p').strftime('%Y-%m-%d')

            txn_type = 'Buy' if txn_type.upper() == 'BUY' else 'Sell'
            price    = round(amount / units, 6)

            result.append({
                'name': name,
                'date': date,
                'type': txn_type,
                'units': units,
                'price': price,
                'amount': amount,
            })
        except Exception:
            continue  # skip malformed rows silently

    return result
