import io
import openpyxl
from datetime import datetime


def parse(file_bytes: bytes) -> list[dict]:
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    ws = wb['Trades']
    result = []
    for row in ws.iter_rows(min_row=2, values_only=True):  # row 1 is header
        if not any(row):
            continue
        try:
            date_val = row[0]   # Col A: transaction date
            name     = str(row[2]).strip()   # Col C: name
            activity = str(row[4]).strip()   # Col E: Activity
            units    = float(row[6])         # Col G: Quantity
            price    = float(row[7])         # Col H: Price Per Share (in USD)

            # Normalize date — openpyxl may return datetime objects for Excel date cells
            if isinstance(date_val, datetime):
                date = date_val.strftime('%Y-%m-%d')
            else:
                date = datetime.strptime(str(date_val).strip(), '%Y-%m-%d').strftime('%Y-%m-%d')

            txn_type = 'Buy' if activity.lower() == 'buy' else 'Sell'
            amount   = round(units * price, 6)

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
