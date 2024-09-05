import pandas as pd
import re
from io import BytesIO
from flask import Flask, request, render_template, send_file, session, jsonify

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # 用於加密 session 數據

# 添加配置選項
app.config['UPLOAD_FOLDER'] = '/path/to/upload'  # 設定文件上傳文件夾
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制文件大小為 16 MB

def read_excel_file(file):
    try:
        file.seek(0)  # 確保文件指標在開頭
        if file.filename.endswith('.xls'):
            df = pd.read_excel(file, engine='xlrd')  # 使用 xlrd 引擎讀取 .xls 文件
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(file, engine='openpyxl')  # 使用 openpyxl 引擎讀取 .xlsx 文件
        else:
            return None, "不支援的文件格式，請上傳 .xls 或 .xlsx 文件。"
        return df, None
    except ValueError as e:
        return None, f"文件內容格式錯誤: {e}"
    except Exception as e:
        return None, f"讀取文件時發生錯誤: {e}"

def process_expected_data(file):
    df, error = read_excel_file(file)
    if error:
        return None, f"處理應到數據時發生錯誤: {error}"
    
    if df is None:
        return None, "無法讀取文件。請確認文件格式正確並重新上傳。"
    
    if '外部完整物料號碼' not in df.columns or '未限制' not in df.columns:
        return None, "Excel 文件中必須包含 '外部完整物料號碼' 和 '未限制' 兩列。"
    
    df['產品簡碼'] = 'G' + df['外部完整物料號碼'].str.extract(r'G(\d{9})')
    result_df = df.groupby('產品簡碼')['未限制'].sum().reset_index()
    result_df = result_df[result_df['未限制'] != 0]
    return result_df, None


def process_actual_data(file):
    df, error = read_excel_file(file)
    if error:
        return None, f"處理實到數據時發生錯誤: {error}"
    
    if '外部完整物料號碼' not in df.columns:
        return None, "Excel 文件中必須包含 '外部完整物料號碼' 列。"
    
    df['產品簡碼'] = 'G00' + df['外部完整物料號碼'].str.extract(r'G(\d{7})')[0]
    count = df['產品簡碼'].value_counts().reset_index()
    count.columns = ['產品簡碼', '數量']

    return count, None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'expected_file' not in request.files or 'actual_file' not in request.files:
            return "未找到兩個文件", 400

        expected_file = request.files['expected_file']
        actual_file = request.files['actual_file']
        
        if expected_file.filename == '' or actual_file.filename == '':
            return "兩個文件都必須選擇", 400

        expected_df, error = process_expected_data(expected_file)
        if error:
            return error, 400

        actual_df, error = process_actual_data(actual_file)
        if error:
            return error, 400

        comparison_result = pd.merge(expected_df, actual_df, on='產品簡碼', how='left', suffixes=('_應到', '_實到'))

        comparison_result['應到'] = comparison_result['未限制'].fillna(0)
        comparison_result['實到'] = comparison_result['數量'].fillna(0)
        comparison_result['差異'] = comparison_result['實到'] - comparison_result['應到']
        comparison_result = comparison_result[['產品簡碼', '未限制', '應到', '實到', '差異']]

        session['comparison_result'] = comparison_result.to_dict()

        expected_html = expected_df.head().to_html(classes='table table-striped', index=False)
        actual_html = actual_df.head().to_html(classes='table table-striped', index=False)
        comparison_html = comparison_result.head().to_html(classes='table table-striped', index=False)

        return f"""
        <html>
        <head>
            <style>
                .header {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .header img {{
                    width: 150px; /* 根据需要调整 logo 的大小 */
                    height: auto;
                }}
                .container {{
                    display: flex;
                    justify-content: space-between;
                }}
                .section {{
                    width: 48%;
                }}
                .clear {{
                    clear: both;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                th, td {{
                    border: 1px solid black;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <img src="/static/logo.png" alt="撼訊科技股份有限公司 Logo">
                <h1>撼訊科技股份有限公司</h1>
            </div>
            <h1>數據預覽</h1>
            <div class="container">
                <div class="section">
                    <h2>應到數據預覽：</h2>
                    {expected_html}
                </div>
                <div class="section">
                    <h2>實到數據預覽：</h2>
                    {actual_html}
                </div>
            </div>
            <div class="clear">
                <h2>比較結果預覽：</h2>
                {comparison_html}
            </div>
            <h2>下載比較結果：</h2>
            <a href="/download">下載 Excel 文件</a>
        </body>
        </html>
        """
    return render_template('index.html')


@app.route('/api/products')
def get_products():
    comparison_result_dict = session.get('comparison_result', None)
    if not comparison_result_dict:
        return jsonify([])  # 如果沒有數據返回空列表

    comparison_result = pd.DataFrame.from_dict(comparison_result_dict)
    product_list = comparison_result['產品簡碼'].tolist()  # 提取“產品簡碼”列的數據
    return jsonify(product_list)  # 返回 JSON 格式的產品數據

@app.route('/download')
def download_file():
    comparison_result_dict = session.get('comparison_result', None)
    if not comparison_result_dict:
        return "沒有數據可供下載", 400

    comparison_result = pd.DataFrame.from_dict(comparison_result_dict)
    
    # 將 '未限制' 列名改為 '數量'，'產品簡碼' 列名改為 '物料號碼'
    comparison_result.rename(columns={'未限制': '數量', '產品簡碼': '物料號碼'}, inplace=True)
    
    # 按 '差異' 列降序排列，將 '差異' 為 0 的行放到最後
    comparison_result = comparison_result.sort_values(by='差異', ascending=False)
    
    # 将 '數量' 和 '應到' 列拼接成 '應到數量'
    comparison_result['應到數量'] = comparison_result['應到'].astype(str)
    
    # 选择需要的列并重新排序
    columns_order = ['物料號碼', '應到數量', '實到', '差異']
    comparison_result = comparison_result[columns_order]

    # 將結果寫入到 Excel 文件
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        comparison_result.to_excel(writer, index=False, sheet_name='ComparisonResult')
    
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="comparison_result.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
