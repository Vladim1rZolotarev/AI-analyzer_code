import re
import sys
import psycopg2
from git import Repo, NULL_TREE
from datetime import datetime

# Поддержка различных форматов комментариев для разных языков программирования
COMMENT_PATTERNS = {
    # JavaScript, Java, C, C++, C#, TypeScript и др.
    'js': {
        'start': re.compile(r'//\s*AI-generated start', re.IGNORECASE),
        'end': re.compile(r'//\s*AI-generated end', re.IGNORECASE)
    },
    # Python, Ruby, Shell и др.
    'py': {
        'start': re.compile(r'#\s*AI-generated start', re.IGNORECASE),
        'end': re.compile(r'#\s*AI-generated end', re.IGNORECASE)
    },
    # HTML, XML и др.
    'html': {
        'start': re.compile(r'<!--\s*AI-generated start\s*-->', re.IGNORECASE),
        'end': re.compile(r'<!--\s*AI-generated end\s*-->', re.IGNORECASE)
    },
    # CSS, SCSS, Less
    'css': {
        'start': re.compile(r'/\*\s*AI-generated start\s*\*/', re.IGNORECASE),
        'end': re.compile(r'/\*\s*AI-generated end\s*\*/', re.IGNORECASE)
    }
}

# Параметры подключения к PostgreSQL
DB_NAME = "ai_code_reports"
DB_USER = "postgres"
DB_PASSWORD = "2739"
DB_HOST = "localhost"
DB_PORT = "5432"

def connect_to_db():
    """Устанавливает соединение с базой данных PostgreSQL."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.Error as e:
        print(f"Ошибка при подключении к базе данных: {e}")
        return None

def save_to_db(commit_hash, commit_message, author_name, author_email, total_lines, ai_lines, ai_percentage):
    """Сохраняет данные отчета в базу данных PostgreSQL."""
    conn = connect_to_db()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO ai_reports (commit_hash, commit_message, author_name, author_email, total_lines, ai_lines, ai_percentage)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        
        cursor.execute(insert_query, (commit_hash, commit_message, author_name, author_email, total_lines, ai_lines, ai_percentage))
        record_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"Данные успешно сохранены (ID: {record_id})")
        
        # Выводим последние 10 записей
        print("\nПоследние записи в базе данных:")
        cursor.execute("""
            SELECT id, commit_hash, commit_message, author_name, total_lines, ai_lines, ai_percentage, report_date 
            FROM ai_reports 
            ORDER BY report_date DESC 
            LIMIT 10;
        """)
        
        # Красивое форматирование вывода
        print(f"{'ID':<5} {'Commit Hash':<15} {'Commit Message':<30} {'Author':<20} {'Total':<8} {'AI':<8} {'AI%':<6} {'Date':<20}")
        print("-" * 120)
        for record in cursor.fetchall():
            commit_msg = record[2] if record[2] is not None else ""
            print(f"{record[0]:<5} {record[1][:12]:<15} {commit_msg[:28]:<30} {record[3][:18]:<20} {record[4]:<8} {record[5]:<8} {record[6]:<6.1f} {record[7]}")
        
        return True
    
    except psycopg2.Error as e:
        print(f"Ошибка при сохранении данных: {e}")
        conn.rollback()
        return False
    
    finally:
        if conn:
            cursor.close()
            conn.close()

def get_comment_patterns(file_extension):
    """Возвращает шаблоны комментариев для указанного расширения файла."""
    if file_extension in ['js', 'java', 'c', 'cpp', 'cs', 'ts']:
        return COMMENT_PATTERNS['js']
    elif file_extension in ['py', 'rb', 'sh']:
        return COMMENT_PATTERNS['py']
    elif file_extension in ['html', 'xml', 'xhtml']:
        return COMMENT_PATTERNS['html']
    elif file_extension in ['css', 'scss', 'less']:
        return COMMENT_PATTERNS['css']
    else:
        return COMMENT_PATTERNS['js']  # По умолчанию

def is_ai_generated_line(line, file_extension, in_ai_block):
    """Проверяет, является ли строка AI-генерированной."""
    patterns = get_comment_patterns(file_extension)
    
    if patterns['start'].search(line):
        return False, True  # Не считаем маркер, включаем AI-блок
    if patterns['end'].search(line):
        return False, False  # Не считаем маркер, выключаем AI-блок
    
    return True, in_ai_block  # Считаем строку, сохраняем состояние блока

def analyze_file_content(file_path, file_extension):
    """Анализирует содержимое файла на наличие AI-генерированного кода."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = 0
        ai_lines = 0
        in_ai_block = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue  # Пропускаем пустые строки
            
            count_line, new_in_ai_block = is_ai_generated_line(line, file_extension, in_ai_block)
            
            if in_ai_block != new_in_ai_block:
                if new_in_ai_block:
                    print(f"Начало AI-блока в файле {file_path}")
                else:
                    print(f"Конец AI-блока в файле {file_path}")
            
            in_ai_block = new_in_ai_block
            
            if count_line:
                total_lines += 1
                if in_ai_block:
                    ai_lines += 1
                    print(f"AI строка: {line}")
                else:
                    print(f"Обычная строка: {line}")
        
        return total_lines, ai_lines
    
    except Exception as e:
        print(f"Ошибка при анализе файла {file_path}: {str(e)}")
        return 0, 0

def analyze_commit(repo_path, commit_hash):
    """Анализирует коммит и определяет AI-генерированный код."""
    print(f"\n{'='*50}")
    print(f"Анализ коммита {commit_hash[:8]}...")
    
    repo = Repo(repo_path)
    commit = repo.commit(commit_hash)
    
    # Информация о коммите
    commit_info = {
        'author_name': commit.author.name,
        'author_email': commit.author.email,
        'commit_message': commit.message.strip(),
        'commit_date': datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M:%S'),
        'total_lines': 0,
        'ai_lines': 0,
        'files_changed': 0
    }
    
    print(f"Автор: {commit_info['author_name']} <{commit_info['author_email']}>")
    print(f"Сообщение коммита: {commit_info['commit_message']}")
    print(f"Дата коммита: {commit_info['commit_date']}")
    
    # Получаем diff коммита
    try:
        # Проверяем, есть ли у коммита родители
        has_parents = len(commit.parents) > 0
        
        if has_parents:
            # Если есть родители, получаем diff с родительским коммитом
            try:
                diff = repo.git.diff(f"{commit_hash}^!", unified=0)
                print(f"Получен diff с помощью git.diff, длина: {len(diff)} символов")
                
                # Сохраняем diff в файл для отладки
                with open("commit_diff.txt", "w", encoding='utf-8') as f:
                    f.write(diff)
                print("Diff сохранен в файл commit_diff.txt для отладки")
                
                if not diff:
                    print("Предупреждение: diff пустой, нет изменений для анализа")
                    return commit_info
                
                current_file = None
                file_extension = None
                in_ai_block = False
                
                for line in diff.split('\n'):
                    line = line.replace('\r', '')
                    
                    if line.startswith('+++ b/'):
                        current_file = line[6:]
                        file_extension = current_file.split('.')[-1].lower() if '.' in current_file else None
                        commit_info['files_changed'] += 1
                        print(f"Обрабатывается файл: {current_file} (расширение: {file_extension})")
                        in_ai_block = False
                    
                    elif line.startswith('+') and current_file and file_extension:
                        line_content = line[1:]
                        
                        if not line_content.strip():
                            continue  # Пропускаем пустые строки
                        
                        count_line, new_in_ai_block = is_ai_generated_line(line_content, file_extension, in_ai_block)
                        
                        # Если состояние AI-блока изменилось, выводим информацию
                        if in_ai_block != new_in_ai_block:
                            if new_in_ai_block:
                                print(f"Начало AI-блока в файле {current_file}")
                            else:
                                print(f"Конец AI-блока в файле {current_file}")
                        
                        in_ai_block = new_in_ai_block
                        
                        if count_line:
                            commit_info['total_lines'] += 1
                            if in_ai_block:
                                commit_info['ai_lines'] += 1
                                print(f"AI строка: {line_content}")
                            else:
                                print(f"Обычная строка: {line_content}")
            
            except Exception as e:
                print(f"Ошибка при получении diff: {str(e)}")
                print("Пробуем альтернативный метод анализа...")
                
                # Альтернативный метод: анализируем файлы напрямую
                for item in commit.tree.traverse():
                    if item.type == 'blob':  # Это файл
                        file_path = item.path
                        file_extension = file_path.split('.')[-1].lower() if '.' in file_path else None
                        
                        if file_extension:
                            print(f"Анализ файла: {file_path} (расширение: {file_extension})")
                            
                            # Сохраняем содержимое файла во временный файл
                            temp_file = f"temp_{file_path.replace('/', '_')}"
                            with open(temp_file, 'wb') as f:
                                f.write(item.data_stream.read())
                            
                            # Анализируем содержимое файла
                            total, ai = analyze_file_content(temp_file, file_extension)
                            commit_info['total_lines'] += total
                            commit_info['ai_lines'] += ai
                            commit_info['files_changed'] += 1
        
        else:
            # Если это первый коммит, анализируем все файлы в коммите
            print("Это первый коммит в репозитории, анализируем все файлы...")
            
            for item in commit.tree.traverse():
                if item.type == 'blob':  # Это файл
                    file_path = item.path
                    file_extension = file_path.split('.')[-1].lower() if '.' in file_path else None
                    
                    if file_extension:
                        print(f"Анализ файла: {file_path} (расширение: {file_extension})")
                        
                        # Сохраняем содержимое файла во временный файл
                        temp_file = f"temp_{file_path.replace('/', '_')}"
                        with open(temp_file, 'wb') as f:
                            f.write(item.data_stream.read())
                        
                        # Анализируем содержимое файла
                        total, ai = analyze_file_content(temp_file, file_extension)
                        commit_info['total_lines'] += total
                        commit_info['ai_lines'] += ai
                        commit_info['files_changed'] += 1
    
    except Exception as e:
        print(f"Ошибка при анализе коммита: {str(e)}")
        import traceback
        traceback.print_exc()
        return commit_info
    
    print(f"Всего строк: {commit_info['total_lines']}, AI-строк: {commit_info['ai_lines']}")
    return commit_info

def generate_report(commit_info, commit_hash):
    """Генерирует отчет в удобном формате."""
    ai_percent = (commit_info['ai_lines'] / commit_info['total_lines'] * 100) if commit_info['total_lines'] > 0 else 0
    
    report = f"""
AI Code Analysis Report
{'='*50}
Автор:       {commit_info['author_name']} <{commit_info['author_email']}>
Коммит:      {commit_hash[:8]}
Дата:        {commit_info['commit_date']}
Файлов:      {commit_info['files_changed']}
Строк кода:  {commit_info['total_lines']} (без пустых и маркеров)
AI-строк:    {commit_info['ai_lines']}
Процент AI:  {ai_percent:.2f}%
{'='*50}
Сообщение коммита:
{commit_info['commit_message']}
"""
    return report, ai_percent

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Использование: python ai_code_analyzer.py <путь_к_репозиторию> <хеш_коммита>")
        sys.exit(1)

    repo_path = sys.argv[1]
    commit_hash = sys.argv[2]

    # Анализ коммита
    commit_info = analyze_commit(repo_path, commit_hash)
    if not commit_info:
        print("Не удалось проанализировать коммит")
        sys.exit(1)

    report, ai_percent = generate_report(commit_info, commit_hash)
    print(report)
    
    # Сохранение в файл
    with open("ai_report.txt", "a", encoding='utf-8') as f:
        f.write(report)
        f.write(f"\n[metrics] date={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        f.write(f" author={commit_info['author_name']}")
        f.write(f" files={commit_info['files_changed']}")
        f.write(f" lines={commit_info['total_lines']}")
        f.write(f" ai_lines={commit_info['ai_lines']}")
        f.write(f" ai_percent={ai_percent:.2f}\n")
    
    # Сохранение в БД
    db_success = save_to_db(
        commit_hash,
        commit_info['commit_message'],
        commit_info['author_name'],
        commit_info['author_email'],
        commit_info['total_lines'],
        commit_info['ai_lines'],
        ai_percent
    )
    
    if not db_success:
        print("Предупреждение: данные не сохранены в БД")
    
    print("Анализ завершен успешно")
