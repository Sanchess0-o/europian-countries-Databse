import sqlite3
from config import DATABASE

def init_db():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='countries'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("Внимание: таблица 'countries' не существует!")
            print("Запустите database_filler.py для создания базы данных")
            return False
            
        conn.close()
        return True

def get_country_by_english_name(english_name):
  
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM countries WHERE english_name = ?', (english_name,))
        result = cursor.fetchone()
        conn.close()
        
        return result


def get_all_countries():
 
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT english_name, name FROM countries ORDER BY region, name')
        result = cursor.fetchall()
        conn.close()
        
        return result


def get_countries_by_region(region):
  
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('SELECT english_name, name FROM countries WHERE region = ? ORDER BY name', (region,))
        result = cursor.fetchall()
        conn.close()
        
        return result
  

def get_country_info(english_name, field=None):

    country = get_country_by_english_name(english_name)
    
    if not country:
        return None
    

    if field:
        fields_map = {
            'name': country[1],
            'capital': country[4] or 'Не указана',
            'population': format_population(country[5]),
            'area': format_area(country[6]),
            'density': f"{country[7]:.1f} чел./км²" if country[7] else 'Не указано',
            'percentage': f"{country[8]:.2f}%" if country[8] else 'Не указано',
            'borders': country[9] or 'Не указаны'
        }
        return fields_map.get(field, 'Неизвестное поле')
    
    return country

def format_population(population):

    if population:
        if population >= 1000000:
            return f"{population / 1000000:.1f} млн чел."
        elif population >= 1000:
            return f"{population / 1000:.1f} тыс. чел."
    

def format_area(area):
  
    if area:
        return f"{area:,.0f} км²".replace(',', ' ')
    return 'Не указано'


if not init_db():
    print("1")

