import re
from collections import defaultdict, Counter
import sys

def format_item_data_to_comma_separated(data_lines):
    """將輸入的品項編號及數量轉換為用逗號分隔的格式，同時累加相同品項的數量"""
    formatted_data = defaultdict(int)
    for line in data_lines:
        parts = line.strip().split()
        if len(parts) == 2:
            item_code = parts[0].strip()
            quantity = int(parts[1].strip())
            formatted_data[item_code] += quantity
    
    # 將結果轉換為列表，格式為 "品項編號,數量"
    formatted_list = [f"{item_code},{quantity}" for item_code, quantity in formatted_data.items()]
    
    '''
    # 調試輸出：檢查格式化後的結果
    print("\n[調試] 格式化後的品項編號及數量（前10個）：")
    for line in formatted_list[:10]:
        print(line)
    '''
    return formatted_list

def extract_product_code(item_code):
    """將品項編號轉換為標準格式（去掉開頭部分，只保留G後9位數字）"""
    match = re.search(r'([A-Z]\d{9})', item_code.strip(), re.IGNORECASE)
    if match:
        return match.group(1).upper().strip()
    return None

def transform_item_number(item_number):
    """將完整料號轉換為標準的品項編號（G後7位數字）"""
    match = re.search(r'([A-Z])(.{7})', item_number.strip())
    if match:
        first_char = match.group(1)
        next_seven_chars = match.group(2)
        return f"{first_char}00{next_seven_chars}"
    return None

def main():
    # 第一階段：用戶輸入品項的編號及數量，格式為 "品項編號 數量"
    print("請先輸入外部完整物料號碼及數量，中間用TAB分隔，完成輸入後按Ctrl+Z 然後 Enter結束輸入:")
    user_given_data_input = sys.stdin.read()

    # 將多行字串拆分為單獨的品項條目
    given_data_lines = user_given_data_input.strip().splitlines()

    # 格式化為用逗號分隔的格式，並累加相同品項的數量
    formatted_data = format_item_data_to_comma_separated(given_data_lines)
    
    # 使用 defaultdict 來存儲最終結果
    given_data = {}
    for line in formatted_data:
        parts = line.split(',')
        if len(parts) == 2:
            item_code = parts[0].strip()
            quantity = int(parts[1].strip())
            product_code = extract_product_code(item_code)
            if product_code:
                given_data[item_code] = (product_code, quantity)
    '''
    # 調試輸出：檢查提取出來的品項編號及其對應的標準編號
    print("\n[調試] 提取出來的品項編號及標準品項編號（前10個）：")
    for item_code, (product_code, quantity) in list(given_data.items()):
        print(f"{item_code} -> {product_code}, 數量: {quantity}")
    '''
    # 第二階段：用戶一次性輸入所有料號，使用換行符號來分隔各個料號
    print("\n請一次性輸入所有料號，每個料號用換行分隔，完成輸入後按 Ctrl+Z 然後 Enter結束輸入:")
    user_input = sys.stdin.read()

    # 將多行字串拆分為單獨的料號
    item_numbers_list = user_input.splitlines()

    # 移除空行並去除料號兩端的空格
    item_numbers_list = [item.strip() for item in item_numbers_list if item.strip()]
    
    product_codes = [transform_item_number(item) for item in item_numbers_list if transform_item_number(item)]
    product_code_counts = Counter(product_codes)
    #sorted_product_code_counts = sorted(product_code_counts.items())
    '''
    print("\nProduct Code Counts (Ascending Order):")
    for code, count in sorted_product_code_counts:
      print(f"{code}: {count} ")
    # 轉換料號為品項編號並統計數量
    product_code_counts = defaultdict(int)
    for item in item_numbers_list:
        product_code = transform_item_number(item)
        if product_code:
            product_code_counts[product_code] += 1
    
    # 調試輸出：檢查轉換後的品項編號及其數量（前10個）
    print("\n[調試] 轉換後的品項編號及其數量（前10個）：")
    for product_code, count in list(product_code_counts.items()):
        print(f"{product_code}: {count}筆")
    '''
    # 調試輸出：檢查比對時的情況
    
    for item_code, (product_code, quantity) in list(given_data.items()):
        actual_quantity = product_code_counts.get(product_code, 0)
        print(f"{item_code}應該有:{quantity}, {product_code}實際找到:{actual_quantity}")

    # 確保程式不會自動退出
    input("\n按下Enter鍵退出...")

if __name__ == "__main__":
    main()
