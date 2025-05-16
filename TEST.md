## Поддерживаемые форматы файлов

Скрипт распознает AI-генерированный код в следующих форматах:

1. JavaScript/Java/C/C++/C#/TypeScript:
   ```javascript
   // AI-generated start
   console.log("Hello, world!");
   // AI-generated end
   ```

2. Python/Ruby/Shell:
   ```python
   # AI-generated start
   print("Hello, world!")
   # AI-generated end
   ```

3. HTML/XML:
   ```html
   <!-- AI-generated start -->
   <p>Hello, world!</p>
   <!-- AI-generated end -->
   ```

4. CSS/SCSS/Less:
   ```css
   /* AI-generated start */
   body { color: red; }
   /* AI-generated end */
   ```

## Команды для ручного тестирования

### 1. Установка и настройка PostgreSQL

```bash
# Установка PostgreSQL
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib

# Установка Python-библиотеки для работы с PostgreSQL
sudo apt-get install -y python3-psycopg2

# Установка Python-библиотеки для работы с Git
sudo apt-get install -y python3-git

# Создание базы данных
sudo -u postgres psql -c "CREATE DATABASE ai_code_reports;"

# Создание таблицы для хранения отчетов
sudo -u postgres psql -d ai_code_reports -c "CREATE TABLE ai_reports (
    id SERIAL PRIMARY KEY,
    commit_hash VARCHAR(50) NOT NULL,
    commit_message TEXT,
    author_name VARCHAR(100) NOT NULL,
    author_email VARCHAR(100) NOT NULL,
    total_lines INTEGER NOT NULL,
    ai_lines INTEGER NOT NULL,
    ai_percentage NUMERIC(5,2) NOT NULL,
    report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"

# Установка пароля для пользователя postgres
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '2739';"
```

### 2. Тестирование с финальным скриптом

```bash
# Создайте тестовый репозиторий
mkdir -p test_repo
cd test_repo
git init

# Создайте файл JavaScript с AI-генерированным кодом
echo "// Обычный комментарий" > test.js
echo "// AI-generated start" >> test.js
echo "console.log('Hello, world!');" >> test.js
echo "const x = 42;" >> test.js
echo "// AI-generated end" >> test.js
echo "console.log('This is not AI-generated');" >> test.js

# Создайте файл Python с AI-генерированным кодом
echo "# Обычный комментарий" > test.py
echo "# AI-generated start" >> test.py
echo "print('Hello, world!')" >> test.py
echo "x = 42" >> test.py
echo "# AI-generated end" >> test.py
echo "print('This is not AI-generated')" >> test.py

# Создайте файл HTML с AI-генерированным кодом
echo "<!-- Обычный комментарий -->" > test.html
echo "<!-- AI-generated start -->" >> test.html
echo "<p>Hello, world!</p>" >> test.html
echo "<div>Test</div>" >> test.html
echo "<!-- AI-generated end -->" >> test.html
echo "<p>This is not AI-generated</p>" >> test.html

# Создайте файл CSS с AI-генерированным кодом
echo "/* Обычный комментарий */" > test.css
echo "/* AI-generated start */" >> test.css
echo "body { color: red; }" >> test.css
echo "h1 { font-size: 24px; }" >> test.css
echo "/* AI-generated end */" >> test.css
echo "p { margin: 10px; }" >> test.css

# Добавьте файлы в Git и создайте коммит
git add .
git config --local user.email "test@example.com"
git config --local user.name "Test User"
git commit -m "Тестовый коммит с AI-генерированным кодом"

# Получите хеш коммита
COMMIT_HASH=$(git rev-parse HEAD)

# Запустите скрипт анализа с тестовым репозиторием
cd ..
python3 ai_code_analyzer_final.py test_repo $COMMIT_HASH
```

Результат выполнения:
- Скрипт проанализирует коммит и определит AI-генерированный код в разных типах файлов
- Подсчитает общее количество строк и количество AI-генерированных строк
- Создаст отчет и дозапишет его в файл ai_report.txt
- Сохранит данные в базу данных PostgreSQL
- Выведет содержимое таблицы ai_reports

### 3. Тестирование с существующим репозиторием

Если у вас есть существующий репозиторий с коммитами, содержащими AI-генерированный код, вы можете проанализировать их:

```bash
# Клонируйте репозиторий, если его нет локально
git clone <url_репозитория> repo_to_analyze

# Получите хеш коммита, который хотите проанализировать
cd repo_to_analyze
COMMIT_HASH=$(git rev-parse HEAD)  # или укажите конкретный хеш

# Запустите скрипт анализа
cd ..
python3 ai_code_analyzer_final.py repo_to_analyze $COMMIT_HASH
```

### 4. Проверка результатов в базе данных

```bash
# Просмотр всех записей в таблице ai_reports
sudo -u postgres psql -d ai_code_reports -c "SELECT * FROM ai_reports;"

# Просмотр последней записи
sudo -u postgres psql -d ai_code_reports -c "SELECT * FROM ai_reports ORDER BY report_date DESC LIMIT 1;"

# Просмотр статистики по авторам
sudo -u postgres psql -d ai_code_reports -c "SELECT author_name, COUNT(*), AVG(ai_percentage) FROM ai_reports GROUP BY author_name;"
```

## Особенности работы скрипта

1. Скрипт определяет тип файла по расширению и применяет соответствующие шаблоны комментариев
2. Для первого коммита в репозитории скрипт анализирует содержимое файлов напрямую
3. Для обычных коммитов скрипт анализирует diff с родительским коммитом
4. Если возникают проблемы с получением diff, скрипт автоматически переключается на альтернативный метод анализа
5. Скрипт сохраняет подробную информацию о коммите в базу данных и в файл отчета
6. Отчет дозаписывается в файл ai_report.txt с датой и временем анализа

## Использование скрипта в реальных проектах

Для анализа реальных коммитов в Git-репозитории:
```bash
python3 ai_code_analyzer_final.py <путь_к_репозиторию> <хеш_коммита>
```

Скрипт:
1. Проанализирует коммит и определит код, сгенерированный ИИ (между соответствующими маркерами)
2. Дозапишет отчет в файл ai_report.txt с датой коммита
3. Сохранит данные в базу данных PostgreSQL
4. Выведет содержимое таблицы ai_reports

Данные в базе данных могут быть использованы для дальнейшего анализа, создания дашбордов или интеграции с другими системами.
