import io
import openpyxl
from datetime import datetime

HEADER_ROW = 12  # 1-indexed; row 12 has column headers, data starts row 15


def parse(file_bytes: bytes) -> list[dict]:
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=HEADER_ROW, values_only=True))
    headers = [str(h).strip() if h is not None else '' for h in rows[0]]
    col = {h: i for i, h in enumerate(headers)}

    result = []
    for row in rows[1:]:
        if not any(row):
            continue
        try:
            name     = str(row[col['Scheme Name']]).strip()
            raw_type = str(row[col['Transaction Type']]).strip()
            units    = float(row[col['Units']])
            price    = float(row[col['NAV']])
            amount   = float(str(row[col['Amount']]).replace(',', '').strip())
            date_raw = str(row[col['Date']]).strip()
            date     = datetime.strptime(date_raw, '%d %b %Y').strftime('%Y-%m-%d')
            txn_type = 'Buy' if raw_type == 'PURCHASE' else 'Sell'
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
