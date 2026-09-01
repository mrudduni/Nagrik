import pandas as pd
df = pd.read_csv('ingestion/data/cleaned.csv', encoding='utf-8')
print('Cleaned CSV shape:', df.shape)
print('Columns:', list(df.columns))
for i in range(3):
    sid = df['scheme_id'].iloc[i][:40]
    lv = df['level'].iloc[i]
    cat = df['normalized_categories'].iloc[i][:80]
    url = df['source_url'].iloc[i]
    print(f'Row {i+1}: scheme_id={sid}, level={lv}')
    print(f'  categories: {cat}')
    print(f'  source_url: {url}')
