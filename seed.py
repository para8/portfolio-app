"""
One-time seed script. Populates all 8 tables with data from portfolio_v4.html.
Run: python seed.py
"""
import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine
import models

models.Base.metadata.create_all(bind=engine)


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Transaction data (parsed from portfolio_v4.html) ─────────────────────────
VESTED = [
  {"date":"2026-03-20","name":"Microsoft","ticker":"MSFT","type":"Buy","units":2.88439291,"price":389.50,"amount":1122,"currency":"USD","broker":"Vested"},
  {"date":"2026-03-17","name":"Alphabet Inc.","ticker":"GOOGL","type":"Buy","units":3.6,"price":305.56,"amount":1100,"currency":"USD","broker":"Vested"},
  {"date":"2026-01-12","name":"Exxon Mobil","ticker":"XOM","type":"Buy","units":4.00996944,"price":124.38,"amount":500,"currency":"USD","broker":"Vested"},
  {"date":"2026-01-12","name":"Chevron","ticker":"CVX","type":"Buy","units":3.42705521,"price":163,"amount":560,"currency":"USD","broker":"Vested"},
  {"date":"2026-01-12","name":"INVESCO NASDAQ 100 ETF","ticker":"QQQM","type":"Buy","units":2.17977133,"price":256.27,"amount":560,"currency":"USD","broker":"Vested"},
  {"date":"2026-01-12","name":"Alphabet Inc.","ticker":"GOOGL","type":"Buy","units":1.71379045,"price":325.95,"amount":560,"currency":"USD","broker":"Vested"},
  {"date":"2026-01-12","name":"Amazon","ticker":"AMZN","type":"Buy","units":2.26442093,"price":246.69,"amount":560,"currency":"USD","broker":"Vested"},
  {"date":"2026-01-05","name":"ASML Holding","ticker":"ASML","type":"Buy","units":0.32379585,"price":1232.29,"amount":400,"currency":"USD","broker":"Vested"},
  {"date":"2026-01-05","name":"Invesco Semi ETF","ticker":"SOXQ","type":"Buy","units":20.31385233,"price":58.93,"amount":1200,"currency":"USD","broker":"Vested"},
  {"date":"2026-01-05","name":"Amazon","ticker":"AMZN","type":"Buy","units":2.39964134,"price":228.63,"amount":550,"currency":"USD","broker":"Vested"},
  {"date":"2026-01-05","name":"ASML Holding","ticker":"ASML","type":"Buy","units":0.49395462,"price":1211.67,"amount":600,"currency":"USD","broker":"Vested"},
  {"date":"2025-11-26","name":"Uber","ticker":"UBER","type":"Buy","units":7,"price":85.87,"amount":602.56,"currency":"USD","broker":"Vested"},
  {"date":"2025-11-26","name":"Microsoft","ticker":"MSFT","type":"Buy","units":1.2,"price":487.28,"amount":586.2,"currency":"USD","broker":"Vested"},
  {"date":"2025-10-27","name":"Invesco Semi ETF","ticker":"SOXQ","type":"Buy","units":18.0750536,"price":55.96,"amount":1014,"currency":"USD","broker":"Vested"},
  {"date":"2025-10-27","name":"INVESCO NASDAQ 100 ETF","ticker":"QQQM","type":"Buy","units":3.92656268,"price":257.09,"amount":1012,"currency":"USD","broker":"Vested"},
  {"date":"2025-09-15","name":"ASML Holding","ticker":"ASML","type":"Buy","units":0.62781705,"price":857.99,"amount":540,"currency":"USD","broker":"Vested"},
  {"date":"2025-09-15","name":"Meta Platforms","ticker":"META","type":"Buy","units":0.78369901,"price":763.7,"amount":600,"currency":"USD","broker":"Vested"},
  {"date":"2025-09-15","name":"Invesco Semi ETF","ticker":"SOXQ","type":"Buy","units":23.06680008,"price":47.57,"amount":1100,"currency":"USD","broker":"Vested"},
  {"date":"2025-09-15","name":"INVESCO NASDAQ 100 ETF","ticker":"QQQM","type":"Buy","units":4.51445146,"price":243.06,"amount":1100,"currency":"USD","broker":"Vested"},
  {"date":"2025-07-16","name":"INVESCO NASDAQ 100 ETF","ticker":"QQQM","type":"Buy","units":0.27413237,"price":229.27,"amount":63,"currency":"USD","broker":"Vested"},
  {"date":"2025-07-16","name":"Invesco Semi ETF","ticker":"SOXQ","type":"Buy","units":25.72131985,"price":44.6,"amount":1150,"currency":"USD","broker":"Vested"},
  {"date":"2025-07-16","name":"INVESCO NASDAQ 100 ETF","ticker":"QQQM","type":"Buy","units":4.78651195,"price":229.24,"amount":1100,"currency":"USD","broker":"Vested"},
  {"date":"2025-04-21","name":"iShares Bitcoin Trust","ticker":"IBIT","type":"Buy","units":14.38232174,"price":50.16,"amount":725,"currency":"USD","broker":"Vested"},
  {"date":"2025-04-21","name":"Meta Platforms","ticker":"META","type":"Buy","units":2.02873761,"price":491.69,"amount":1000,"currency":"USD","broker":"Vested"},
  {"date":"2025-04-15","name":"INVESCO NASDAQ 100 ETF","ticker":"QQQM","type":"Buy","units":4.3958366,"price":188.35,"amount":830,"currency":"USD","broker":"Vested"},
  {"date":"2025-04-09","name":"Invesco Semi ETF","ticker":"SOXQ","type":"Buy","units":31.13287372,"price":28.84,"amount":900,"currency":"USD","broker":"Vested"},
  {"date":"2025-04-04","name":"Invesco Semi ETF","ticker":"SOXQ","type":"Buy","units":22.06252332,"price":28.94,"amount":640,"currency":"USD","broker":"Vested"},
  {"date":"2025-04-04","name":"Meta Platforms","ticker":"META","type":"Buy","units":2.1331891,"price":514.38,"amount":1100,"currency":"USD","broker":"Vested"},
  {"date":"2025-03-07","name":"Meta Platforms","ticker":"META","type":"Buy","units":0.6376712,"price":625.73,"amount":400,"currency":"USD","broker":"Vested"},
  {"date":"2025-03-07","name":"Invesco Semi ETF","ticker":"SOXQ","type":"Buy","units":9.77955182,"price":35.7,"amount":350,"currency":"USD","broker":"Vested"},
  {"date":"2025-03-06","name":"INVESCO NASDAQ 100 ETF","ticker":"QQQM","type":"Buy","units":2.94571316,"price":203.18,"amount":600,"currency":"USD","broker":"Vested"},
  {"date":"2025-02-06","name":"INVESCO NASDAQ 100 ETF","ticker":"QQQM","type":"Buy","units":3.97995853,"price":217.05,"amount":866,"currency":"USD","broker":"Vested"},
  {"date":"2025-02-06","name":"Invesco Semi ETF","ticker":"SOXQ","type":"Buy","units":21.22377972,"price":39.95,"amount":850,"currency":"USD","broker":"Vested"},
  {"date":"2025-01-28","name":"Invesco Semi ETF","ticker":"SOXQ","type":"Buy","units":31.16694092,"price":38.41,"amount":1200,"currency":"USD","broker":"Vested"},
  {"date":"2025-01-28","name":"NVIDIA","ticker":"NVDA","type":"Buy","units":9.84951028,"price":121.53,"amount":1200,"currency":"USD","broker":"Vested"},
  {"date":"2025-01-21","name":"Invesco Semi ETF","ticker":"SOXQ","type":"Buy","units":17.72819905,"price":42.2,"amount":750,"currency":"USD","broker":"Vested"},
  {"date":"2025-01-06","name":"Invesco Semi ETF","ticker":"SOXQ","type":"Buy","units":4.31946114,"price":41.57,"amount":180,"currency":"USD","broker":"Vested"},
  {"date":"2025-01-02","name":"INVESCO NASDAQ 100 ETF","ticker":"QQQM","type":"Buy","units":2.86429256,"price":212.44,"amount":610,"currency":"USD","broker":"Vested"},
  {"date":"2025-01-06","name":"PayPal","ticker":"PYPL","type":"Sell","units":8.55965267,"price":87.93,"amount":750.78,"currency":"USD","broker":"Vested"},
  {"date":"2024-12-30","name":"Invesco Semi ETF","ticker":"SOXQ","type":"Buy","units":15.16889528,"price":39.46,"amount":600,"currency":"USD","broker":"Vested"},
  {"date":"2024-12-18","name":"Uber","ticker":"UBER","type":"Buy","units":4.68765664,"price":63.84,"amount":300,"currency":"USD","broker":"Vested"},
  {"date":"2024-12-17","name":"Uber","ticker":"UBER","type":"Buy","units":4.98017888,"price":60.24,"amount":300,"currency":"USD","broker":"Vested"},
  {"date":"2024-12-12","name":"Uber","ticker":"UBER","type":"Buy","units":9.46410499,"price":63.24,"amount":600,"currency":"USD","broker":"Vested"},
  {"date":"2024-12-02","name":"INVESCO NASDAQ 100 ETF","ticker":"QQQM","type":"Buy","units":2.87537656,"price":211.62,"amount":610,"currency":"USD","broker":"Vested"},
  {"date":"2024-11-13","name":"Tesla","ticker":"TSLA","type":"Buy","units":0.97707514,"price":335.88,"amount":329,"currency":"USD","broker":"Vested"},
  {"date":"2024-11-11","name":"PayPal","ticker":"PYPL","type":"Buy","units":3.55965267,"price":84.07,"amount":300,"currency":"USD","broker":"Vested"},
  {"date":"2024-11-07","name":"ASML Holding","ticker":"ASML","type":"Buy","units":0.88821671,"price":673.83,"amount":600,"currency":"USD","broker":"Vested"},
  {"date":"2024-11-07","name":"INVESCO NASDAQ 100 ETF","ticker":"QQQM","type":"Buy","units":2.85998948,"price":209.27,"amount":600,"currency":"USD","broker":"Vested"},
  {"date":"2024-11-04","name":"ASML Holding","ticker":"ASML","type":"Buy","units":0.03998641,"price":673.73,"amount":27,"currency":"USD","broker":"Vested"},
  {"date":"2024-11-05","name":"S&P Regional Banking ETF","ticker":"KRE","type":"Sell","units":19.96,"price":58.32,"amount":1161.16,"currency":"USD","broker":"Vested"},
  {"date":"2024-10-21","name":"ASML Holding","ticker":"ASML","type":"Buy","units":1.73594652,"price":724.02,"amount":1260,"currency":"USD","broker":"Vested"},
  {"date":"2024-10-04","name":"Meta Platforms","ticker":"META","type":"Buy","units":0.51266852,"price":583.73,"amount":300,"currency":"USD","broker":"Vested"},
  {"date":"2024-10-04","name":"Tesla","ticker":"TSLA","type":"Buy","units":0.76851025,"price":246.62,"amount":190,"currency":"USD","broker":"Vested"},
  {"date":"2024-10-04","name":"INVESCO NASDAQ 100 ETF","ticker":"QQQM","type":"Buy","units":5.96595893,"price":200.64,"amount":1200,"currency":"USD","broker":"Vested"},
  {"date":"2024-09-24","name":"INVESCO NASDAQ 100 ETF","ticker":"QQQM","type":"Buy","units":5.51228562,"price":199.42,"amount":1102,"currency":"USD","broker":"Vested"},
  {"date":"2024-08-05","name":"Franklin Bitcoin ETF","ticker":"EZBC","type":"Buy","units":19.01297057,"price":31.61,"amount":604,"currency":"USD","broker":"Vested"},
  {"date":"2024-08-05","name":"NVIDIA","ticker":"NVDA","type":"Buy","units":5.90897467,"price":101.29,"amount":600,"currency":"USD","broker":"Vested"},
  {"date":"2024-08-05","name":"Meta Platforms","ticker":"META","type":"Buy","units":0.62902943,"price":475.75,"amount":300,"currency":"USD","broker":"Vested"},
  {"date":"2024-08-05","name":"Alphabet Inc.","ticker":"GOOGL","type":"Buy","units":1.84614435,"price":162.1,"amount":300,"currency":"USD","broker":"Vested"},
  {"date":"2024-08-05","name":"Franklin Bitcoin ETF","ticker":"EZBC","type":"Buy","units":9.49749287,"price":31.43,"amount":300,"currency":"USD","broker":"Vested"},
  {"date":"2024-08-05","name":"NVIDIA","ticker":"NVDA","type":"Buy","units":3.01354413,"price":99.31,"amount":300,"currency":"USD","broker":"Vested"},
  {"date":"2024-07-12","name":"Meta Platforms","ticker":"META","type":"Buy","units":0.63220795,"price":497.02,"amount":315,"currency":"USD","broker":"Vested"},
  {"date":"2024-07-12","name":"NVIDIA","ticker":"NVDA","type":"Buy","units":2.33432137,"price":128.2,"amount":300,"currency":"USD","broker":"Vested"},
  {"date":"2024-07-12","name":"iShares Bitcoin Trust","ticker":"IBIT","type":"Buy","units":18.20182926,"price":32.8,"amount":600,"currency":"USD","broker":"Vested"},
  {"date":"2024-06-03","name":"Tesla","ticker":"TSLA","type":"Buy","units":1.7,"price":178.08,"amount":303.34,"currency":"USD","broker":"Vested"},
  {"date":"2024-06-03","name":"PayPal","ticker":"PYPL","type":"Buy","units":5,"price":63.05,"amount":315.88,"currency":"USD","broker":"Vested"},
  {"date":"2024-05-23","name":"iShares Bitcoin Trust","ticker":"IBIT","type":"Buy","units":15,"price":39.48,"amount":593.39,"currency":"USD","broker":"Vested"},
  {"date":"2023-12-12","name":"NVIDIA","ticker":"NVDA","type":"Buy","units":0.02,"price":460.46,"amount":9.22,"currency":"USD","broker":"Vested"},
  {"date":"2023-12-04","name":"Microsoft","ticker":"MSFT","type":"Buy","units":1.55,"price":369,"amount":573.11,"currency":"USD","broker":"Vested"},
  {"date":"2023-11-07","name":"Apple","ticker":"AAPL","type":"Buy","units":2.56,"price":179.22,"amount":459.71,"currency":"USD","broker":"Vested"},
  {"date":"2023-11-06","name":"INVESCO NASDAQ 100 ETF","ticker":"QQQM","type":"Buy","units":4,"price":151.63,"amount":607.72,"currency":"USD","broker":"Vested"},
  {"date":"2023-08-07","name":"Apple","ticker":"AAPL","type":"Buy","units":1.38,"price":182.13,"amount":251.34,"currency":"USD","broker":"Vested"},
  {"date":"2023-07-18","name":"Microsoft","ticker":"MSFT","type":"Buy","units":1,"price":343.83,"amount":343.83,"currency":"USD","broker":"Vested"},
  {"date":"2023-07-07","name":"Meta Platforms","ticker":"META","type":"Buy","units":2.06,"price":292.11,"amount":601.75,"currency":"USD","broker":"Vested"},
  {"date":"2023-06-09","name":"S&P Regional Banking ETF","ticker":"KRE","type":"Buy","units":6.56,"price":44.1,"amount":289.3,"currency":"USD","broker":"Vested"},
  {"date":"2023-05-16","name":"S&P Regional Banking ETF","ticker":"KRE","type":"Buy","units":6.7,"price":37.55,"amount":251.59,"currency":"USD","broker":"Vested"},
  {"date":"2023-05-15","name":"Apple","ticker":"AAPL","type":"Buy","units":1,"price":173.1,"amount":173.1,"currency":"USD","broker":"Vested"},
  {"date":"2023-05-15","name":"S&P Regional Banking ETF","ticker":"KRE","type":"Buy","units":6.7,"price":36.42,"amount":244.01,"currency":"USD","broker":"Vested"},
  {"date":"2023-04-17","name":"Microsoft","ticker":"MSFT","type":"Buy","units":0.85,"price":287.18,"amount":244.1,"currency":"USD","broker":"Vested"},
  {"date":"2023-04-17","name":"Apple","ticker":"AAPL","type":"Buy","units":1.5,"price":164.58,"amount":246.87,"currency":"USD","broker":"Vested"},
]

MF = [
  {"date":"2022-03-28","name":"Axis ELSS Tax Saver","ticker":"AXIS-ELSS","type":"Buy","units":471.9,"price":74.16,"amount":34998,"currency":"INR","broker":"MF"},
  {"date":"2024-01-23","name":"DSP ELSS Tax Saver","ticker":"DSP-ELSS","type":"Buy","units":424.3,"price":117.84,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2022-03-28","name":"DSP ELSS Tax Saver","ticker":"DSP-ELSS","type":"Buy","units":353.18,"price":84.94,"amount":29998,"currency":"INR","broker":"MF"},
  {"date":"2025-03-03","name":"Edelweiss Smallcap 250","ticker":"EDEL-SC250","type":"Buy","units":3499.46,"price":14.29,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2024-10-03","name":"Edelweiss Smallcap 250","ticker":"EDEL-SC250","type":"Buy","units":5300.98,"price":18.86,"amount":99995,"currency":"INR","broker":"MF"},
  {"date":"2025-04-04","name":"Edelweiss Smallcap 250","ticker":"EDEL-SC250","type":"Buy","units":4893.11,"price":15.33,"amount":74996,"currency":"INR","broker":"MF"},
  {"date":"2025-02-06","name":"Edelweiss Smallcap 250","ticker":"EDEL-SC250","type":"Buy","units":4487.78,"price":16.71,"amount":74996,"currency":"INR","broker":"MF"},
  {"date":"2025-01-08","name":"Edelweiss Smallcap 250","ticker":"EDEL-SC250","type":"Buy","units":5519.49,"price":18.12,"amount":99995,"currency":"INR","broker":"MF"},
  {"date":"2025-01-08","name":"Edelweiss Smallcap 250","ticker":"EDEL-SC250","type":"Buy","units":6899.37,"price":18.12,"amount":124993,"currency":"INR","broker":"MF"},
  {"date":"2025-07-16","name":"Edelweiss Smallcap 250","ticker":"EDEL-SC250","type":"Buy","units":5359.13,"price":18.66,"amount":99995,"currency":"INR","broker":"MF"},
  {"date":"2025-05-19","name":"Edelweiss Smallcap 250","ticker":"EDEL-SC250","type":"Buy","units":4379.98,"price":17.12,"amount":74996,"currency":"INR","broker":"MF"},
  {"date":"2025-05-23","name":"Edelweiss Smallcap 250","ticker":"EDEL-SC250","type":"Buy","units":4375.74,"price":17.14,"amount":74996,"currency":"INR","broker":"MF"},
  {"date":"2022-05-01","name":"LIC MF Liquid Fund","ticker":"LIC-LIQ","type":"Buy","units":25.78,"price":3878.65,"amount":99995,"currency":"INR","broker":"MF"},
  {"date":"2023-04-17","name":"LIC MF Liquid Fund","ticker":"LIC-LIQ","type":"Sell","units":25.78,"price":4102.12,"amount":105756,"currency":"INR","broker":"MF"},
  {"date":"2023-02-06","name":"Mirae Asset ELSS Tax Saver","ticker":"MIRAE-ELSS","type":"Buy","units":3824.69,"price":33.99,"amount":129993,"currency":"INR","broker":"MF"},
  {"date":"2022-03-25","name":"Mirae Asset ELSS Tax Saver","ticker":"MIRAE-ELSS","type":"Buy","units":1068.52,"price":32.75,"amount":34998,"currency":"INR","broker":"MF"},
  {"date":"2024-01-31","name":"Mirae Asset ELSS Tax Saver","ticker":"MIRAE-ELSS","type":"Buy","units":1773.71,"price":45.1,"amount":79996,"currency":"INR","broker":"MF"},
  {"date":"2025-03-03","name":"Navi Nifty 50 Index","ticker":"NAVI-N50","type":"Buy","units":6962.23,"price":14.36,"amount":99995,"currency":"INR","broker":"MF"},
  {"date":"2024-10-03","name":"Navi Nifty 50 Index","ticker":"NAVI-N50","type":"Buy","units":6119.94,"price":16.34,"amount":99995,"currency":"INR","broker":"MF"},
  {"date":"2026-01-05","name":"Navi Nifty 50 Index","ticker":"NAVI-N50","type":"Buy","units":5814.98,"price":17.2,"amount":99995,"currency":"INR","broker":"MF"},
  {"date":"2025-01-08","name":"Navi Nifty 50 Index","ticker":"NAVI-N50","type":"Buy","units":6515.31,"price":15.35,"amount":99995,"currency":"INR","broker":"MF"},
  {"date":"2025-07-16","name":"Navi Nifty 50 Index","ticker":"NAVI-N50","type":"Buy","units":6078.69,"price":16.45,"amount":99995,"currency":"INR","broker":"MF"},
  {"date":"2024-08-01","name":"Navi Nifty Midcap 150","ticker":"NAVI-MC150","type":"Buy","units":2439.02,"price":20.5,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2025-03-03","name":"Navi Nifty Midcap 150","ticker":"NAVI-MC150","type":"Buy","units":2972.31,"price":16.82,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2025-04-04","name":"Navi Nifty Midcap 150","ticker":"NAVI-MC150","type":"Buy","units":2833.86,"price":17.64,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2025-04-04","name":"Navi Nifty Midcap 150","ticker":"NAVI-MC150","type":"Buy","units":4250.79,"price":17.64,"amount":74996,"currency":"INR","broker":"MF"},
  {"date":"2025-02-06","name":"Navi Nifty Midcap 150","ticker":"NAVI-MC150","type":"Buy","units":4007.62,"price":18.71,"amount":74996,"currency":"INR","broker":"MF"},
  {"date":"2025-01-08","name":"Navi Nifty Midcap 150","ticker":"NAVI-MC150","type":"Buy","units":5077.0,"price":19.7,"amount":99995,"currency":"INR","broker":"MF"},
  {"date":"2025-01-08","name":"Navi Nifty Midcap 150","ticker":"NAVI-MC150","type":"Buy","units":6346.25,"price":19.7,"amount":124993,"currency":"INR","broker":"MF"},
  {"date":"2025-07-17","name":"Navi Nifty Midcap 150","ticker":"NAVI-MC150","type":"Buy","units":4808.24,"price":20.8,"amount":99995,"currency":"INR","broker":"MF"},
  {"date":"2025-05-19","name":"Navi Nifty Midcap 150","ticker":"NAVI-MC150","type":"Buy","units":3783.31,"price":19.82,"amount":74996,"currency":"INR","broker":"MF"},
  {"date":"2024-09-23","name":"Navi Nifty Midcap 150","ticker":"NAVI-MC150","type":"Buy","units":4719.37,"price":21.19,"amount":99995,"currency":"INR","broker":"MF"},
  {"date":"2024-07-30","name":"Navi Nifty Midcap 150","ticker":"NAVI-MC150","type":"Buy","units":2434.22,"price":20.54,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2024-04-02","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":324.67,"price":154.0,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2024-08-02","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":293.32,"price":170.45,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2024-01-02","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":336.84,"price":148.43,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2022-05-02","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":87.01,"price":114.93,"amount":9999,"currency":"INR","broker":"MF"},
  {"date":"2022-05-02","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":87.01,"price":114.93,"amount":9999,"currency":"INR","broker":"MF"},
  {"date":"2024-05-02","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":321.92,"price":155.31,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2023-07-03","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":379.23,"price":131.84,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2024-06-03","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":312.38,"price":160.05,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2023-11-03","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":379.41,"price":131.78,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2023-10-03","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":374.12,"price":133.64,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2023-12-04","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":352.72,"price":141.75,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2023-01-06","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":412.08,"price":121.33,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2022-05-06","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":90.5,"price":110.5,"amount":9999,"currency":"INR","broker":"MF"},
  {"date":"2023-11-07","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":375.98,"price":132.98,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2023-04-10","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":166.98,"price":119.77,"amount":19999,"currency":"INR","broker":"MF"},
  {"date":"2023-04-10","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":417.45,"price":119.77,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2023-01-10","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":8.22,"price":121.7,"amount":999,"currency":"INR","broker":"MF"},
  {"date":"2024-07-12","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":296.08,"price":168.87,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2022-04-13","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":85.0,"price":117.64,"amount":9999,"currency":"INR","broker":"MF"},
  {"date":"2023-05-15","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":799.59,"price":125.06,"amount":99995,"currency":"INR","broker":"MF"},
  {"date":"2025-05-19","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":433.82,"price":172.87,"amount":74996,"currency":"INR","broker":"MF"},
  {"date":"2022-06-20","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":240.66,"price":103.87,"amount":24998,"currency":"INR","broker":"MF"},
  {"date":"2022-12-27","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":284.1,"price":123.19,"amount":34998,"currency":"INR","broker":"MF"},
  {"date":"2023-03-27","name":"UTI Nifty 50 Index","ticker":"UTI-N50","type":"Buy","units":433.08,"price":115.45,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2022-05-01","name":"Union Liquid Fund","ticker":"UNION-LIQ","type":"Buy","units":24.3,"price":2057.37,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2022-11-01","name":"Union Liquid Fund","ticker":"UNION-LIQ","type":"Buy","units":23.7,"price":2110.06,"amount":49997,"currency":"INR","broker":"MF"},
  {"date":"2023-04-17","name":"Union Liquid Fund","ticker":"UNION-LIQ","type":"Sell","units":48.0,"price":2177.17,"amount":104497,"currency":"INR","broker":"MF"},
  {"date":"2026-03-16","name":"Mirae Asset ELSS Tax Saver","ticker":"MIRAE-ELSS","type":"Sell","units":4893.21,"price":52.11,"amount":254967,"currency":"INR","broker":"MF"},
  {"date":"2026-03-16","name":"DSP ELSS Tax Saver","ticker":"DSP-ELSS","type":"Sell","units":353.18,"price":146.34,"amount":51681,"currency":"INR","broker":"MF"},
  {"date":"2026-03-16","name":"Axis ELSS Tax Saver","ticker":"AXIS-ELSS","type":"Sell","units":471.9,"price":100.40,"amount":47376,"currency":"INR","broker":"MF"},
]

INDIA_EQ = [
  {"date":"2023-10-16","name":"SBI Cards","ticker":"SBICARD","type":"Buy","units":31,"price":794.8,"amount":24638.8,"currency":"INR","broker":"Zerodha"},
  {"date":"2023-10-30","name":"SBI Cards","ticker":"SBICARD","type":"Buy","units":13,"price":749.4,"amount":9742.2,"currency":"INR","broker":"Zerodha"},
  {"date":"2023-11-07","name":"Narayana Hrudayalaya","ticker":"NH","type":"Buy","units":46,"price":1040.0,"amount":47840.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2023-11-07","name":"Reliance Industries","ticker":"RELIANCE","type":"Buy","units":21,"price":2334.05,"amount":49015.05,"currency":"INR","broker":"Zerodha"},
  {"date":"2023-11-10","name":"Reliance Industries","ticker":"RELIANCE","type":"Buy","units":21,"price":2305.55,"amount":48416.55,"currency":"INR","broker":"Zerodha"},
  {"date":"2023-12-04","name":"Narayana Hrudayalaya","ticker":"NH","type":"Buy","units":40,"price":1244.85,"amount":49794.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2023-12-04","name":"Narayana Hrudayalaya","ticker":"NH","type":"Buy","units":2,"price":1244.85,"amount":2489.7,"currency":"INR","broker":"Zerodha"},
  {"date":"2023-12-05","name":"Kotak Mahindra Bank","ticker":"KOTAKBANK","type":"Buy","units":49,"price":1828.0,"amount":89572.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2023-12-06","name":"Kotak Mahindra Bank","ticker":"KOTAKBANK","type":"Buy","units":52,"price":1832.05,"amount":95266.6,"currency":"INR","broker":"Zerodha"},
  {"date":"2023-12-08","name":"SBI Cards","ticker":"SBICARD","type":"Buy","units":81,"price":773.7,"amount":62669.7,"currency":"INR","broker":"Zerodha"},
  {"date":"2023-12-08","name":"Kotak Mahindra Bank","ticker":"KOTAKBANK","type":"Buy","units":8,"price":1826.85,"amount":14614.8,"currency":"INR","broker":"Zerodha"},
  {"date":"2023-12-12","name":"SBI Cards","ticker":"SBICARD","type":"Buy","units":33,"price":758.9,"amount":25043.7,"currency":"INR","broker":"Zerodha"},
  {"date":"2023-12-12","name":"Kotak Mahindra Bank","ticker":"KOTAKBANK","type":"Buy","units":26,"price":1848.0,"amount":48048.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2023-12-13","name":"SBI Cards","ticker":"SBICARD","type":"Buy","units":15,"price":760.0,"amount":11400.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2024-01-15","name":"Bajaj Finance","ticker":"BAJFINANCE","type":"Buy","units":6,"price":7662.1,"amount":45972.6,"currency":"INR","broker":"Zerodha"},
  {"date":"2024-01-15","name":"HDFC Bank","ticker":"HDFCBANK","type":"Buy","units":58,"price":1646.15,"amount":95476.7,"currency":"INR","broker":"Zerodha"},
  {"date":"2024-01-15","name":"HDFC Bank","ticker":"HDFCBANK","type":"Buy","units":5,"price":1669.95,"amount":8349.75,"currency":"INR","broker":"Zerodha"},
  {"date":"2024-01-31","name":"HDFC Bank","ticker":"HDFCBANK","type":"Buy","units":67,"price":1442.1,"amount":96620.7,"currency":"INR","broker":"Zerodha"},
  {"date":"2024-01-31","name":"Bajaj Finance","ticker":"BAJFINANCE","type":"Buy","units":7,"price":6827.0,"amount":47789.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2024-02-13","name":"Bajaj Finance","ticker":"BAJFINANCE","type":"Buy","units":8,"price":6600.0,"amount":52800.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2024-02-15","name":"SBI Cards","ticker":"SBICARD","type":"Buy","units":6,"price":723.5,"amount":4341.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2024-05-21","name":"Kotak Mahindra Bank","ticker":"KOTAKBANK","type":"Buy","units":30,"price":1696.4,"amount":50892.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2024-05-21","name":"HDFC Bank","ticker":"HDFCBANK","type":"Buy","units":65,"price":1454.0,"amount":94510.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2024-06-03","name":"Bajaj Finance","ticker":"BAJFINANCE","type":"Buy","units":7,"price":6948.85,"amount":48641.95,"currency":"INR","broker":"Zerodha"},
  {"date":"2024-10-03","name":"Mirae China ETF","ticker":"MAHKTECH","type":"Buy","units":2450,"price":20.07,"amount":49171.5,"currency":"INR","broker":"Zerodha"},
  {"date":"2024-11-12","name":"Swiggy","ticker":"SWIGGY","type":"Buy","units":266,"price":390.0,"amount":103740.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2024-11-19","name":"Swiggy","ticker":"SWIGGY","type":"Sell","units":133,"price":416.59,"amount":55406.47,"currency":"INR","broker":"Zerodha"},
  {"date":"2025-01-06","name":"Kotak Mahindra Bank","ticker":"KOTAKBANK","type":"Sell","units":85,"price":1821.0,"amount":154785.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2025-01-06","name":"HDFC Bank","ticker":"HDFCBANK","type":"Sell","units":100,"price":1740.1,"amount":174010.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2025-01-06","name":"Reliance Industries","ticker":"RELIANCE","type":"Sell","units":84,"price":1253.95,"amount":105331.8,"currency":"INR","broker":"Zerodha"},
  {"date":"2025-01-06","name":"Narayana Hrudayalaya","ticker":"NH","type":"Sell","units":88,"price":1315.0,"amount":115720.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2025-01-14","name":"SBI Cards","ticker":"SBICARD","type":"Sell","units":179,"price":708.55,"amount":126830.45,"currency":"INR","broker":"Zerodha"},
  {"date":"2025-01-14","name":"Bajaj Finance","ticker":"BAJFINANCE","type":"Sell","units":28,"price":7230.0,"amount":202440.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2025-10-23","name":"ICICI Nifty ETF","ticker":"NIFTYIETF","type":"Buy","units":350,"price":291.99,"amount":102196.5,"currency":"INR","broker":"Zerodha"},
  {"date":"2025-11-10","name":"ICICI Nifty ETF","ticker":"NIFTYIETF","type":"Buy","units":17,"price":288.76,"amount":4908.92,"currency":"INR","broker":"Zerodha"},
  {"date":"2026-01-19","name":"Kotak Mahindra Bank","ticker":"KOTAKBANK","type":"Sell","units":400,"price":418.3,"amount":167320.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2026-01-19","name":"Swiggy","ticker":"SWIGGY","type":"Sell","units":133,"price":340.0,"amount":45220.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2026-01-19","name":"Mirae China ETF","ticker":"MAHKTECH","type":"Buy","units":1850,"price":27.38,"amount":50653.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2026-01-20","name":"Amagi Media Labs","ticker":"AMAGI","type":"Buy","units":41,"price":361.0,"amount":14801.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2026-01-27","name":"Zerodha Gold ETF","ticker":"GOLDCASE","type":"Buy","units":800,"price":25.1,"amount":20080.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2026-01-27","name":"Zerodha Silver ETF","ticker":"SILVERCASE","type":"Buy","units":600,"price":33.25,"amount":19950.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2026-02-04","name":"Zerodha Silver ETF","ticker":"SILVERCASE","type":"Buy","units":1100,"price":27.87,"amount":30657.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2026-02-04","name":"Zerodha Gold ETF","ticker":"GOLDCASE","type":"Buy","units":1300,"price":24.82,"amount":32266.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2026-03-04","name":"Zerodha Gold ETF","ticker":"GOLDCASE","type":"Buy","units":4100,"price":25.48,"amount":104468.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2026-03-17","name":"ICICI Nifty ETF","ticker":"NIFTYIETF","type":"Buy","units":390,"price":264.51,"amount":103158.9,"currency":"INR","broker":"Zerodha"},
  {"date":"2026-03-17","name":"ICICI Nifty ETF","ticker":"NIFTYIETF","type":"Buy","units":57,"price":265.81,"amount":15151.17,"currency":"INR","broker":"Zerodha"},
  {"date":"2026-03-17","name":"Amagi Media Labs","ticker":"AMAGI","type":"Sell","units":41,"price":358.31,"amount":14690.71,"currency":"INR","broker":"Zerodha"},
  {"date":"2026-03-20","name":"ICICI Nifty ETF","ticker":"NIFTYIETF","type":"Buy","units":770,"price":261.85,"amount":201624.5,"currency":"INR","broker":"Zerodha"},
  {"date":"2026-03-20","name":"ICICI Nifty ETF","ticker":"NIFTYIETF","type":"Buy","units":175,"price":262.08,"amount":45864.0,"currency":"INR","broker":"Zerodha"},
  {"date":"2026-03-20","name":"Mirae Nifty Midcap 150 ETF","ticker":"MAM150ETF","type":"Buy","units":4870,"price":20.85,"amount":101539.5,"currency":"INR","broker":"Zerodha"},
]

INDMONEY = [
  {"date":"2022-12-19","name":"Alphabet Inc.","ticker":"GOOGL","type":"Buy","units":5.40627077,"price":90.26,"amount":487.97,"currency":"USD","broker":"IndMoney"},
  {"date":"2022-12-18","name":"Invesco Nasdaq 100 ETF","ticker":"QQQM","type":"Buy","units":2.63713829,"price":112.66,"amount":297.1,"currency":"USD","broker":"IndMoney"},
  {"date":"2022-12-17","name":"Invesco Nasdaq 100 ETF","ticker":"QQQM","type":"Buy","units":2.63722705,"price":112.66,"amount":297.11,"currency":"USD","broker":"IndMoney"},
  {"date":"2022-11-10","name":"Alphabet Inc.","ticker":"GOOGL","type":"Buy","units":1.25246253,"price":93.4,"amount":116.98,"currency":"USD","broker":"IndMoney"},
  {"date":"2022-11-03","name":"Alphabet Inc.","ticker":"GOOGL","type":"Buy","units":0.20734676,"price":90.38,"amount":18.74,"currency":"USD","broker":"IndMoney"},
  {"date":"2022-11-03","name":"Meta Platforms","ticker":"META","type":"Buy","units":1.05674733,"price":94.63,"amount":100.0,"currency":"USD","broker":"IndMoney"},
  {"date":"2022-12-28","name":"Microsoft","ticker":"MSFT","type":"Buy","units":0.79235733,"price":237.09,"amount":187.86,"currency":"USD","broker":"IndMoney"},
  {"date":"2022-12-28","name":"Meta Platforms","ticker":"META","type":"Buy","units":4.29405703,"price":116.44,"amount":500.0,"currency":"USD","broker":"IndMoney"},
  {"date":"2022-12-27","name":"Microsoft","ticker":"MSFT","type":"Buy","units":2.10384583,"price":237.66,"amount":500.0,"currency":"USD","broker":"IndMoney"},
  {"date":"2022-12-27","name":"Invesco Nasdaq 100 ETF","ticker":"QQQM","type":"Buy","units":5.41193622,"price":109.75,"amount":593.96,"currency":"USD","broker":"IndMoney"},
  {"date":"2022-12-26","name":"Alphabet Inc.","ticker":"GOOGL","type":"Buy","units":6.69303584,"price":88.74,"amount":593.94,"currency":"USD","broker":"IndMoney"},
  {"date":"2022-12-19","name":"Alphabet Inc.","ticker":"GOOGL","type":"Sell","units":0.0111657,"price":89.56,"amount":1.0,"currency":"USD","broker":"IndMoney"},
  {"date":"2026-01-03","name":"Alphabet Inc.","ticker":"GOOGL","type":"Buy","units":0.09117499,"price":317.96,"amount":28.99,"currency":"USD","broker":"IndMoney"},
  {"date":"2025-06-01","name":"Meta Platforms","ticker":"META","type":"Buy","units":0.07907835,"price":644.93,"amount":51.0,"currency":"USD","broker":"IndMoney"},
  {"date":"2023-11-19","name":"Nvidia Corp","ticker":"NVDA","type":"Buy","units":0.02572836,"price":493.23,"amount":12.69,"currency":"USD","broker":"IndMoney"},
  {"date":"2023-02-11","name":"Invesco Nasdaq 100 ETF","ticker":"QQQM","type":"Buy","units":4.88189297,"price":122.77,"amount":599.35,"currency":"USD","broker":"IndMoney"},
  {"date":"2023-01-26","name":"Microsoft","ticker":"MSFT","type":"Sell","units":0.02071337,"price":241.39,"amount":5.0,"currency":"USD","broker":"IndMoney"},
]

MANUAL = [
  {"date":"2026-03-20","name":"Bank Account","ticker":"CASH-BANK","type":"Buy","units":600000,"price":1,"amount":600000,"currency":"INR","broker":"Manual"},
  {"date":"2026-03-14","name":"Fixed Deposits","ticker":"CASH-FD","type":"Buy","units":900000,"price":1,"amount":900000,"currency":"INR","broker":"Manual"},
]


def main():
    db = SessionLocal()

    # ── 1. Categories ──────────────────────────────────────────────────────────
    CATEGORIES = [
        ("Indian Equity",  "#facc15"),
        ("US Equities",    "#93c5fd"),
        ("US Indexes",     "#d8b4fe"),
        ("Bitcoin",        "#fdba74"),
        ("Metals",         "#fbbf24"),
        ("Fixed Deposit",  "#a5f3fc"),
        ("Cash",           "#6ee7b7"),
    ]
    cat_id = {}
    for name, color in CATEGORIES:
        existing = db.query(models.Category).filter_by(name=name).first()
        if not existing:
            c = models.Category(name=name, color=color)
            db.add(c)
            db.flush()
            cat_id[name] = c.id
        else:
            cat_id[name] = existing.id
    db.commit()
    print(f"  Categories: {len(cat_id)}")

    # ── 2. Sectors ─────────────────────────────────────────────────────────────
    SECTORS = [
        ("Magnificent 7",       "#93c5fd"),
        ("AI / Semiconductors", "#d8b4fe"),
        ("India Index Core",    "#facc15"),
        ("Energy",              "#fbbf24"),
        ("Crypto",              "#fdba74"),
        ("Capital Preservation","#6ee7b7"),
        ("Others",              "#9a9aa3"),
    ]
    sec_id = {}
    for name, color in SECTORS:
        existing = db.query(models.Sector).filter_by(name=name).first()
        if not existing:
            s = models.Sector(name=name, color=color)
            db.add(s)
            db.flush()
            sec_id[name] = s.id
        else:
            sec_id[name] = existing.id
    db.commit()
    print(f"  Sectors: {len(sec_id)}")

    # ── 3. Brokers ─────────────────────────────────────────────────────────────
    BROKERS = ["Vested", "IndMoney", "MF", "Zerodha", "Manual"]
    broker_id = {}
    for name in BROKERS:
        existing = db.query(models.Broker).filter_by(name=name).first()
        if not existing:
            b = models.Broker(name=name)
            db.add(b)
            db.flush()
            broker_id[name] = b.id
        else:
            broker_id[name] = existing.id
    db.commit()
    print(f"  Brokers: {len(broker_id)}")

    # ── 4. FX History ──────────────────────────────────────────────────────────
    FX_HISTORY = [
        ("2026-01", 87), ("2025-10", 85), ("2025-07", 84), ("2025-04", 85),
        ("2025-01", 87), ("2024-10", 84), ("2024-07", 84), ("2024-04", 83),
        ("2024-01", 83), ("2023-01", 82), ("2022-10", 82), ("2022-07", 79),
        ("2022-04", 77), ("2022-01", 75), ("2000-01", 74),
    ]
    if db.query(models.FxHistory).count() == 0:
        for from_ym, rate in FX_HISTORY:
            db.add(models.FxHistory(from_ym=from_ym, rate=float(rate)))
        db.commit()
    print(f"  FX history rows: {len(FX_HISTORY)}")

    # ── 5. Config ──────────────────────────────────────────────────────────────
    if not db.query(models.Config).filter_by(key="fx_rate_usd_inr").first():
        db.add(models.Config(key="fx_rate_usd_inr", value="86", updated_at=now_iso()))
        db.commit()
    print("  Config: fx_rate_usd_inr = 86")

    # ── 6. Ticker metadata ─────────────────────────────────────────────────────
    TICKER_CAT = {
        "UTI-N50": "Indian Equity",    "NAVI-N50": "Indian Equity",
        "NIFTYIETF": "Indian Equity",  "NAVI-MC150": "Indian Equity",
        "MAM150ETF": "Indian Equity",  "EDEL-SC250": "Indian Equity",
        "AXIS-ELSS": "Indian Equity",  "DSP-ELSS": "Indian Equity",
        "MIRAE-ELSS": "Indian Equity", "HDFCBANK": "Indian Equity",
        "SWIGGY": "Indian Equity",     "AMAGI": "Indian Equity",
        "MAHKTECH": "Indian Equity",   "GOLDCASE": "Metals",
        "SILVERCASE": "Metals",        "CASH-BANK": "Cash",
        "CASH-FD": "Fixed Deposit",    "META": "US Equities",
        "NVDA": "US Equities",         "ASML": "US Equities",
        "GOOGL": "US Equities",        "AMZN": "US Equities",
        "MSFT": "US Equities",         "UBER": "US Equities",
        "TSLA": "US Equities",         "AAPL": "US Equities",
        "CVX": "US Equities",          "XOM": "US Equities",
        "QQQM": "US Indexes",          "SOXQ": "US Indexes",
        "IBIT": "Bitcoin",             "EZBC": "Bitcoin",
    }
    TICKER_SEC = {
        "META": "Magnificent 7",       "NVDA": "AI / Semiconductors",
        "ASML": "AI / Semiconductors", "GOOGL": "Magnificent 7",
        "AMZN": "Magnificent 7",       "MSFT": "Magnificent 7",
        "UBER": "Others",              "TSLA": "Magnificent 7",
        "AAPL": "Magnificent 7",       "CVX": "Energy",
        "XOM": "Energy",               "QQQM": "AI / Semiconductors",
        "SOXQ": "AI / Semiconductors", "IBIT": "Crypto",
        "EZBC": "Crypto",              "UTI-N50": "India Index Core",
        "NAVI-N50": "India Index Core","NIFTYIETF": "India Index Core",
        "NAVI-MC150": "India Index Core","MAM150ETF": "India Index Core",
        "EDEL-SC250": "India Index Core","AXIS-ELSS": "India Index Core",
        "DSP-ELSS": "India Index Core", "MIRAE-ELSS": "India Index Core",
        "HDFCBANK": "Others",           "SWIGGY": "Others",
        "AMAGI": "Others",              "MAHKTECH": "Others",
        "GOLDCASE": "Capital Preservation","SILVERCASE": "Capital Preservation",
        "CASH-BANK": "Capital Preservation","CASH-FD": "Capital Preservation",
    }
    TICKER_NAME = {
        "UTI-N50": "UTI Nifty 50 Index",        "NAVI-N50": "Navi Nifty 50 Index",
        "NIFTYIETF": "ICICI Nifty ETF",          "NAVI-MC150": "Navi Nifty Midcap 150",
        "MAM150ETF": "Mirae Nifty Midcap 150 ETF","EDEL-SC250": "Edelweiss Smallcap 250",
        "AXIS-ELSS": "Axis ELSS Tax Saver",       "DSP-ELSS": "DSP ELSS Tax Saver",
        "MIRAE-ELSS": "Mirae Asset ELSS Tax Saver","QQQM": "Nasdaq 100 ETF",
        "SOXQ": "Invesco Semi ETF",               "IBIT": "iShares Bitcoin Trust",
        "EZBC": "Franklin Bitcoin ETF",            "META": "Meta Platforms",
        "NVDA": "NVIDIA",                          "ASML": "ASML Holding",
        "GOOGL": "Alphabet Inc.",                  "AMZN": "Amazon",
        "MSFT": "Microsoft",                       "UBER": "Uber",
        "TSLA": "Tesla",                           "AAPL": "Apple",
        "CVX": "Chevron",                          "XOM": "Exxon Mobil",
        "HDFCBANK": "HDFC Bank",                   "SWIGGY": "Swiggy",
        "AMAGI": "Amagi Media Labs",               "MAHKTECH": "Mirae China ETF",
        "GOLDCASE": "Zerodha Gold ETF",            "SILVERCASE": "Zerodha Silver ETF",
        "CASH-BANK": "Bank Account",               "CASH-FD": "Fixed Deposits",
        "LIC-LIQ": "LIC MF Liquid Fund",          "UNION-LIQ": "Union Liquid Fund",
        "PYPL": "PayPal",                          "KRE": "S&P Regional Banking ETF",
        "SBICARD": "SBI Cards",                    "NH": "Narayana Hrudayalaya",
        "RELIANCE": "Reliance Industries",         "KOTAKBANK": "Kotak Mahindra Bank",
        "BAJFINANCE": "Bajaj Finance",
    }

    # ── 7. Tickers ─────────────────────────────────────────────────────────────
    all_txns = VESTED + MF + INDIA_EQ + INDMONEY + MANUAL
    seen_tickers = {}
    for t in all_txns:
        tk = t.get("ticker", "")
        if not tk or tk in seen_tickers:
            continue
        seen_tickers[tk] = {
            "name": TICKER_NAME.get(tk, t.get("name", tk)),
            "currency": t.get("currency", "INR"),
            "category_id": cat_id.get(TICKER_CAT.get(tk, "Indian Equity")),
            "sector_id": sec_id.get(TICKER_SEC.get(tk, "Others")),
        }

    tickers_added = 0
    for tk, meta in seen_tickers.items():
        if not db.query(models.Ticker).filter_by(ticker=tk).first():
            db.add(models.Ticker(
                ticker=tk, name=meta["name"], currency=meta["currency"],
                category_id=meta["category_id"], sector_id=meta["sector_id"],
                created_at=now_iso(),
            ))
            tickers_added += 1
    db.commit()
    print(f"  Tickers added: {tickers_added} (total unique: {len(seen_tickers)})")

    # ── 8. Transactions ────────────────────────────────────────────────────────
    txns_added = 0
    if db.query(models.Transaction).count() == 0:
        for t in all_txns:
            tk = t.get("ticker", "")
            if not tk:
                continue
            bid = broker_id.get(t.get("broker", "Manual"), broker_id.get("Manual"))
            units = float(t.get("units", 0))
            price = float(t.get("price", 0))
            db.add(models.Transaction(
                date=t.get("date", ""),
                ticker=tk,
                type=t.get("type", "Buy"),
                units=units,
                price=price,
                amount=units * price,
                broker_id=bid,
                created_at=now_iso(),
            ))
            txns_added += 1
        db.commit()
    print(f"  Transactions added: {txns_added}")

    # ── 9. Prices ──────────────────────────────────────────────────────────────
    CUR_USD = {
        "QQQM": 244, "SOXQ": 60, "META": 613, "ASML": 1345, "MSFT": 395,
        "NVDA": 180, "UBER": 73, "AAPL": 250, "GOOGL": 302, "AMZN": 207,
        "TSLA": 391, "CVX": 197, "XOM": 156, "IBIT": 40, "EZBC": 41,
    }
    CUR_NAV = {
        "UTI-N50": 162, "NAVI-MC150": 19, "MAM150ETF": 20.85, "EDEL-SC250": 15,
        "NAVI-N50": 15, "MIRAE-ELSS": 51, "DSP-ELSS": 145, "AXIS-ELSS": 99,
        "HDFCBANK": 817, "GOLDCASE": 24, "NIFTYIETF": 261, "SILVERCASE": 26,
        "AMAGI": 364, "MAHKTECH": 22, "CASH-BANK": 1, "CASH-FD": 1,
    }
    prices_added = 0
    for tk, price in {**CUR_USD, **CUR_NAV}.items():
        existing = db.query(models.Price).filter_by(ticker=tk).first()
        if not existing:
            db.add(models.Price(ticker=tk, price=float(price), updated_at=now_iso()))
            prices_added += 1
        else:
            existing.price = float(price)
            existing.updated_at = now_iso()
    db.commit()
    print(f"  Prices seeded: {prices_added}")

    db.close()
    print("\nSeed complete! Run: uvicorn main:app --reload")


if __name__ == "__main__":
    main()
