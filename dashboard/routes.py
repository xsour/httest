from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps

dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')


def create_dashboard_routes(app, mysql):
    def role_required(allowed_roles):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'user' not in session:
                    flash('Ви повинні увійти в систему, щоб переглянути цю сторінку.', 'error')
                    return redirect(url_for('auth.login'))
                user_role = session.get('role')
                if user_role in allowed_roles:
                    return f(*args, **kwargs)
                else:
                    flash('У вас немає доступу до цієї сторінки.', 'error')
                    return redirect(url_for('dashboard.dashboard'))

            return decorated_function

        return decorator

    # Головна сторінка панелі керування
    @dashboard_bp.route('/dashboard')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def dashboard():
        username = session.get('username')
        return render_template('dashboard.html', username=username)

    #                                              ======= Маршрут для Торгових точок =======

    # Список торгових точок
    @dashboard_bp.route('/trading_points')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def trading_points():
        search_query = request.args.get('search')
        cur = mysql.connection.cursor()
        if search_query:
            cur.execute("SELECT * FROM trading_points WHERE name LIKE %s", ('%' + search_query + '%',))
        else:
            cur.execute("SELECT * FROM trading_points")
        trading_points = cur.fetchall()
        cur.close()
        return render_template('trading_points.html', trading_points=trading_points)

    # Додавання торгової точки
    @dashboard_bp.route('/trading_points/add', methods=['POST'])
    @role_required(['owner', 'admin'])
    def add_trading_point():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            name = request.form['name']
            type_ = request.form['type']
            size = float(request.form['size'])
            rent_fee = float(request.form['rent_fee'])
            utility_costs = float(request.form.get('utility_costs', 0.0))
            counter_count = int(request.form.get('counter_count', 0))

            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO trading_points (name, type, size, rent_fee, utility_costs, counter_count) VALUES (%s, %s, %s, %s, %s, %s)",
                (name, type_, size, rent_fee, utility_costs, counter_count))
            mysql.connection.commit()
            new_id = cur.lastrowid
            cur.execute("SELECT * FROM trading_points WHERE id = %s", (new_id,))
            new_point = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Торгова точка успішно додана.'
            response['trading_point'] = {
                'id': new_point[0],
                'name': new_point[1],
                'type': new_point[2],
                'size': new_point[3],
                'rent_fee': new_point[4],
                'utility_costs': new_point[5],
                'counter_count': new_point[6]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при додаванні торгової точки: {e}'

        return jsonify(response)

    # Редагування торгової точки
    @dashboard_bp.route('/trading_points/edit', methods=['POST'])
    @role_required(['owner', 'admin', 'operator'])
    def edit_trading_point():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            point_id = request.form['id']
            name = request.form['name']
            type_ = request.form['type']
            size = float(request.form['size'])
            rent_fee = float(request.form['rent_fee'])
            utility_costs = float(request.form.get('utility_costs', 0.0))
            counter_count = int(request.form.get('counter_count', 0))

            cur = mysql.connection.cursor()
            cur.execute(
                "UPDATE trading_points SET name = %s, type = %s, size = %s, rent_fee = %s, utility_costs = %s, counter_count = %s WHERE id = %s",
                (name, type_, size, rent_fee, utility_costs, counter_count, point_id))
            mysql.connection.commit()
            cur.execute("SELECT * FROM trading_points WHERE id = %s", (point_id,))
            updated_point = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Торгова точка успішно оновлена.'
            response['trading_point'] = {
                'id': updated_point[0],
                'name': updated_point[1],
                'type': updated_point[2],
                'size': updated_point[3],
                'rent_fee': updated_point[4],
                'utility_costs': updated_point[5],
                'counter_count': updated_point[6]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при оновленні торгової точки: {e}'

        return jsonify(response)

    # Видалення торгової точки
    @dashboard_bp.route('/trading_points/delete', methods=['POST'])
    @role_required(['owner', 'admin'])
    def delete_trading_point():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            point_id = request.form['id']
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM trading_points WHERE id = %s", (point_id,))
            mysql.connection.commit()
            cur.close()
            response['status'] = 'success'
            response['message'] = 'Торгова точка успішно видалена.'
        except Exception as e:
            response['message'] = f'Помилка при видаленні торгової точки: {e}'

        return jsonify(response)

    #                                              ======= Маршрут для зал =======

    # Список зал
    @dashboard_bp.route('/halls')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def halls():
        search_query = request.args.get('search')
        cur = mysql.connection.cursor()
        if search_query:
            cur.execute("""
                SELECT halls.id, halls.name, trading_points.name, halls.trading_point_id
                FROM halls
                JOIN trading_points ON halls.trading_point_id = trading_points.id
                WHERE halls.name LIKE %s
            """, ('%' + search_query + '%',))
        else:
            cur.execute("""
                SELECT halls.id, halls.name, trading_points.name, halls.trading_point_id
                FROM halls
                JOIN trading_points ON halls.trading_point_id = trading_points.id
            """)
        halls_data = cur.fetchall()
        halls_list = []
        for hall in halls_data:
            halls_list.append({
                'id': hall[0],
                'name': hall[1],
                'trading_point_name': hall[2],
                'trading_point_id': hall[3]
            })
        # Отримання всіх торгових точок для вибору
        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()
        trading_points_list = [{'id': tp[0], 'name': tp[1]} for tp in trading_points]
        cur.close()
        return render_template('halls.html', halls=halls_list, trading_points=trading_points_list)

    # Додавання зали
    @dashboard_bp.route('/halls/add', methods=['POST'])
    @role_required(['owner', 'admin'])
    def add_hall():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            name = request.form['name']
            trading_point_id = int(request.form['trading_point_id'])

            cur = mysql.connection.cursor()
            cur.execute(
                "INSERT INTO halls (name, trading_point_id) VALUES (%s, %s)",
                (name, trading_point_id))
            mysql.connection.commit()
            new_id = cur.lastrowid
            cur.execute("""
                SELECT halls.id, halls.name, trading_points.name, halls.trading_point_id
                FROM halls
                JOIN trading_points ON halls.trading_point_id = trading_points.id
                WHERE halls.id = %s
            """, (new_id,))
            new_hall = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Зала успішно додана.'
            response['hall'] = {
                'id': new_hall[0],
                'name': new_hall[1],
                'trading_point_name': new_hall[2],
                'trading_point_id': new_hall[3]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при додаванні зали: {e}'

        return jsonify(response)

    # Редагування зали
    @dashboard_bp.route('/halls/edit', methods=['POST'])
    @role_required(['owner', 'admin', 'operator'])
    def edit_hall():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            hall_id = int(request.form['id'])
            name = request.form['name']
            trading_point_id = int(request.form['trading_point_id'])

            cur = mysql.connection.cursor()
            cur.execute(
                "UPDATE halls SET name = %s, trading_point_id = %s WHERE id = %s",
                (name, trading_point_id, hall_id))
            mysql.connection.commit()
            cur.execute("""
                SELECT halls.id, halls.name, trading_points.name, halls.trading_point_id
                FROM halls
                JOIN trading_points ON halls.trading_point_id = trading_points.id
                WHERE halls.id = %s
            """, (hall_id,))
            updated_hall = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Зала успішно оновлена.'
            response['hall'] = {
                'id': updated_hall[0],
                'name': updated_hall[1],
                'trading_point_name': updated_hall[2],
                'trading_point_id': updated_hall[3]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при оновленні зали: {e}'

        return jsonify(response)

    # Видалення зали
    @dashboard_bp.route('/halls/delete', methods=['POST'])
    @role_required(['owner', 'admin'])
    def delete_hall():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            hall_id = int(request.form['id'])
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM halls WHERE id = %s", (hall_id,))
            mysql.connection.commit()
            cur.close()
            response['status'] = 'success'
            response['message'] = 'Зала успішно видалена.'
        except ValueError:
            response['message'] = 'Некоректний ID зали.'
        except Exception as e:
            response['message'] = f'Помилка при видаленні зали: {e}'

        return jsonify(response)

    #                                              ======= Маршрути для Працівників =======

    # Список працівників
    @dashboard_bp.route('/employees')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def employees():
        search_query = request.args.get('search')
        cur = mysql.connection.cursor()
        if search_query:
            cur.execute("""
                SELECT employees.id, employees.first_name, employees.last_name, employees.position, employees.salary,
                       trading_points.id, trading_points.name, halls.id, halls.name, sections.id, sections.name
                FROM employees
                LEFT JOIN trading_points ON employees.trading_point_id = trading_points.id
                LEFT JOIN halls ON employees.hall_id = halls.id
                LEFT JOIN sections ON employees.section_id = sections.id
                WHERE employees.first_name LIKE %s OR employees.last_name LIKE %s
            """, ('%' + search_query + '%', '%' + search_query + '%'))
        else:
            cur.execute("""
                SELECT employees.id, employees.first_name, employees.last_name, employees.position, employees.salary,
                       trading_points.id, trading_points.name, halls.id, halls.name, sections.id, sections.name
                FROM employees
                LEFT JOIN trading_points ON employees.trading_point_id = trading_points.id
                LEFT JOIN halls ON employees.hall_id = halls.id
                LEFT JOIN sections ON employees.section_id = sections.id
            """)
        employees = cur.fetchall()

        # Отримання всіх торгових точок, залів та секцій для форм
        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()

        cur.execute("SELECT id, name FROM halls")
        halls = cur.fetchall()

        cur.execute("SELECT id, name FROM sections")
        sections = cur.fetchall()

        cur.close()
        return render_template('employees.html', employees=employees, trading_points=trading_points, halls=halls, sections=sections)

    # Додавання працівника
    @dashboard_bp.route('/employees/add', methods=['POST'])
    @role_required(['owner', 'admin'])
    def add_employee():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            position = request.form['position']
            salary = float(request.form['salary'])
            trading_point_id = request.form.get('trading_point_id')
            hall_id = request.form.get('hall_id')
            section_id = request.form.get('section_id')

            # Перевірка на наявність ID, якщо вони передані
            trading_point_id = int(trading_point_id) if trading_point_id else None
            hall_id = int(hall_id) if hall_id else None
            section_id = int(section_id) if section_id else None

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO employees (first_name, last_name, position, salary, trading_point_id, hall_id, section_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (first_name, last_name, position, salary, trading_point_id, hall_id, section_id))
            mysql.connection.commit()
            new_id = cur.lastrowid
            cur.execute("""
                SELECT employees.id, employees.first_name, employees.last_name, employees.position, employees.salary,
                       trading_points.id, trading_points.name, halls.id, halls.name, sections.id, sections.name
                FROM employees
                LEFT JOIN trading_points ON employees.trading_point_id = trading_points.id
                LEFT JOIN halls ON employees.hall_id = halls.id
                LEFT JOIN sections ON employees.section_id = sections.id
                WHERE employees.id = %s
            """, (new_id,))
            new_employee = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Працівника успішно додано.'
            response['employee'] = {
                'id': new_employee[0],
                'first_name': new_employee[1],
                'last_name': new_employee[2],
                'position': new_employee[3],
                'salary': new_employee[4],
                'trading_point_id': new_employee[5],
                'trading_point': new_employee[6],
                'hall_id': new_employee[7],
                'hall': new_employee[8],
                'section_id': new_employee[9],
                'section': new_employee[10]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при додаванні працівника: {e}'

        return jsonify(response)

    # Редагування працівника
    @dashboard_bp.route('/employees/edit', methods=['POST'])
    @role_required(['owner', 'admin', 'operator'])
    def edit_employee():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            employee_id = int(request.form['id'])
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            position = request.form['position']
            salary = float(request.form['salary'])
            trading_point_id = request.form.get('trading_point_id')
            hall_id = request.form.get('hall_id')
            section_id = request.form.get('section_id')

            trading_point_id = int(trading_point_id) if trading_point_id else None
            hall_id = int(hall_id) if hall_id else None
            section_id = int(section_id) if section_id else None

            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE employees
                SET first_name = %s, last_name = %s, position = %s, salary = %s,
                    trading_point_id = %s, hall_id = %s, section_id = %s
                WHERE id = %s
            """, (first_name, last_name, position, salary, trading_point_id, hall_id, section_id, employee_id))
            mysql.connection.commit()
            cur.execute("""
                SELECT employees.id, employees.first_name, employees.last_name, employees.position, employees.salary,
                       trading_points.id, trading_points.name, halls.id, halls.name, sections.id, sections.name
                FROM employees
                LEFT JOIN trading_points ON employees.trading_point_id = trading_points.id
                LEFT JOIN halls ON employees.hall_id = halls.id
                LEFT JOIN sections ON employees.section_id = sections.id
                WHERE employees.id = %s
            """, (employee_id,))
            updated_employee = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Працівника успішно оновлено.'
            response['employee'] = {
                'id': updated_employee[0],
                'first_name': updated_employee[1],
                'last_name': updated_employee[2],
                'position': updated_employee[3],
                'salary': updated_employee[4],
                'trading_point_id': updated_employee[5],
                'trading_point': updated_employee[6],
                'hall_id': updated_employee[7],
                'hall': updated_employee[8],
                'section_id': updated_employee[9],
                'section': updated_employee[10]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при оновленні працівника: {e}'

        return jsonify(response)

    # Видалення працівника
    @dashboard_bp.route('/employees/delete', methods=['POST'])
    @role_required(['owner', 'admin'])
    def delete_employee():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            employee_id = int(request.form['id'])
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
            mysql.connection.commit()
            cur.close()
            response['status'] = 'success'
            response['message'] = 'Працівника успішно видалено.'
        except ValueError:
            response['message'] = 'Некоректний ID працівника.'
        except Exception as e:
            response['message'] = f'Помилка при видаленні працівника: {e}'

        return jsonify(response)

    #                                              ======= Маршрути для Секцій =======

    # Список секцій
    @dashboard_bp.route('/sections')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def sections():
        search_query = request.args.get('search')
        cur = mysql.connection.cursor()
        if search_query:
            cur.execute("""
                SELECT sections.id, sections.name, sections.floor, employees.id, employees.first_name, trading_points.id, trading_points.name
                FROM sections
                LEFT JOIN employees ON sections.manager_id = employees.id
                LEFT JOIN trading_points ON sections.trading_point_id = trading_points.id
                WHERE sections.name LIKE %s OR trading_points.name LIKE %s
            """, ('%' + search_query + '%', '%' + search_query + '%'))
        else:
            cur.execute("""
                SELECT sections.id, sections.name, sections.floor, employees.id, employees.first_name, trading_points.id, trading_points.name
                FROM sections
                LEFT JOIN employees ON sections.manager_id = employees.id
                LEFT JOIN trading_points ON sections.trading_point_id = trading_points.id
            """)
        sections = cur.fetchall()

        # Отримання всіх працівників для вибору менеджера
        cur.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS full_name FROM employees")
        employees = cur.fetchall()

        # Отримання всіх торгових точок для вибору
        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()

        cur.close()
        return render_template('sections.html', sections=sections, employees=employees, trading_points=trading_points)

    # Додавання секції
    @dashboard_bp.route('/sections/add', methods=['POST'])
    @role_required(['owner', 'admin'])
    def add_section():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            name = request.form['name']
            floor = int(request.form['floor'])
            manager_id = request.form.get('manager_id')
            trading_point_id = int(request.form['trading_point_id'])

            manager_id = int(manager_id) if manager_id else None

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO sections (name, floor, manager_id, trading_point_id)
                VALUES (%s, %s, %s, %s)
            """, (name, floor, manager_id, trading_point_id))
            mysql.connection.commit()
            new_id = cur.lastrowid
            cur.execute("""
                SELECT sections.id, sections.name, sections.floor, employees.id, employees.first_name, trading_points.id, trading_points.name
                FROM sections
                LEFT JOIN employees ON sections.manager_id = employees.id
                LEFT JOIN trading_points ON sections.trading_point_id = trading_points.id
                WHERE sections.id = %s
            """, (new_id,))
            new_section = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Секцію успішно додано.'
            response['section'] = {
                'id': new_section[0],
                'name': new_section[1],
                'floor': new_section[2],
                'manager_id': new_section[3],
                'manager': new_section[4] if new_section[3] else '',
                'trading_point_id': new_section[5],
                'trading_point': new_section[6]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при додаванні секції: {e}'

        return jsonify(response)

    # Редагування секції
    @dashboard_bp.route('/sections/edit', methods=['POST'])
    @role_required(['owner', 'admin', 'operator'])
    def edit_section():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            section_id = int(request.form['id'])
            name = request.form['name']
            floor = int(request.form['floor'])
            manager_id = request.form.get('manager_id')
            trading_point_id = int(request.form['trading_point_id'])

            manager_id = int(manager_id) if manager_id else None

            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE sections
                SET name = %s, floor = %s, manager_id = %s, trading_point_id = %s
                WHERE id = %s
            """, (name, floor, manager_id, trading_point_id, section_id))
            mysql.connection.commit()
            cur.execute("""
                SELECT sections.id, sections.name, sections.floor, employees.id, employees.first_name, trading_points.id, trading_points.name
                FROM sections
                LEFT JOIN employees ON sections.manager_id = employees.id
                LEFT JOIN trading_points ON sections.trading_point_id = trading_points.id
                WHERE sections.id = %s
            """, (section_id,))
            updated_section = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Секцію успішно оновлено.'
            response['section'] = {
                'id': updated_section[0],
                'name': updated_section[1],
                'floor': updated_section[2],
                'manager_id': updated_section[3],
                'manager': updated_section[4] if updated_section[3] else '',
                'trading_point_id': updated_section[5],
                'trading_point': updated_section[6]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при оновленні секції: {e}'

        return jsonify(response)

    # Видалення секції
    @dashboard_bp.route('/sections/delete', methods=['POST'])
    @role_required(['owner', 'admin'])
    def delete_section():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            section_id = int(request.form['id'])
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM sections WHERE id = %s", (section_id,))
            mysql.connection.commit()
            cur.close()
            response['status'] = 'success'
            response['message'] = 'Секцію успішно видалено.'
        except ValueError:
            response['message'] = 'Некоректний ID секції.'
        except Exception as e:
            response['message'] = f'Помилка при видаленні секції: {e}'

        return jsonify(response)

    #                                              ======= Маршрути для Постачальників =======

    # Список постачальників
    @dashboard_bp.route('/suppliers')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def suppliers():
        search_query = request.args.get('search')
        cur = mysql.connection.cursor()
        if search_query:
            cur.execute("""
                SELECT * FROM suppliers
                WHERE name LIKE %s OR contact_phone LIKE %s
            """, ('%' + search_query + '%', '%' + search_query + '%'))
        else:
            cur.execute("SELECT * FROM suppliers")
        suppliers = cur.fetchall()
        cur.close()
        return render_template('suppliers.html', suppliers=suppliers)

    # Додавання постачальника
    @dashboard_bp.route('/suppliers/add', methods=['POST'])
    @role_required(['owner', 'admin'])
    def add_supplier():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            name = request.form['name']
            contact_phone = request.form.get('contact_phone')

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO suppliers (name, contact_phone)
                VALUES (%s, %s)
            """, (name, contact_phone))
            mysql.connection.commit()
            new_id = cur.lastrowid
            cur.execute("SELECT * FROM suppliers WHERE id = %s", (new_id,))
            new_supplier = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Постачальника успішно додано.'
            response['supplier'] = {
                'id': new_supplier[0],
                'name': new_supplier[1],
                'contact_phone': new_supplier[2]
            }
        except Exception as e:
            response['message'] = f'Помилка при додаванні постачальника: {e}'

        return jsonify(response)

    # Редагування постачальника
    @dashboard_bp.route('/suppliers/edit', methods=['POST'])
    @role_required(['owner', 'admin', 'operator'])
    def edit_supplier():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            supplier_id = int(request.form['id'])
            name = request.form['name']
            contact_phone = request.form.get('contact_phone')

            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE suppliers
                SET name = %s, contact_phone = %s
                WHERE id = %s
            """, (name, contact_phone, supplier_id))
            mysql.connection.commit()
            cur.execute("SELECT * FROM suppliers WHERE id = %s", (supplier_id,))
            updated_supplier = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Постачальника успішно оновлено.'
            response['supplier'] = {
                'id': updated_supplier[0],
                'name': updated_supplier[1],
                'contact_phone': updated_supplier[2]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при оновленні постачальника: {e}'

        return jsonify(response)

    # Видалення постачальника
    @dashboard_bp.route('/suppliers/delete', methods=['POST'])
    @role_required(['owner', 'admin'])
    def delete_supplier():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            supplier_id = int(request.form['id'])
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM suppliers WHERE id = %s", (supplier_id,))
            mysql.connection.commit()
            cur.close()
            response['status'] = 'success'
            response['message'] = 'Постачальника успішно видалено.'
        except ValueError:
            response['message'] = 'Некоректний ID постачальника.'
        except Exception as e:
            response['message'] = f'Помилка при видаленні постачальника: {e}'

        return jsonify(response)

    #                                              ======= Маршрути для Товарів =======

    # Список товарів
    @dashboard_bp.route('/products')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def products():
        search_query = request.args.get('search')
        cur = mysql.connection.cursor()
        if search_query:
            cur.execute("""
                SELECT * FROM products
                WHERE name LIKE %s OR description LIKE %s
            """, ('%' + search_query + '%', '%' + search_query + '%'))
        else:
            cur.execute("SELECT * FROM products")
        products = cur.fetchall()
        cur.close()
        return render_template('products.html', products=products)

    # Додавання товару
    @dashboard_bp.route('/products/add', methods=['POST'])
    @role_required(['owner', 'admin'])
    def add_product():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            name = request.form['name']
            description = request.form.get('description')

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO products (name, description)
                VALUES (%s, %s)
            """, (name, description))
            mysql.connection.commit()
            new_id = cur.lastrowid
            cur.execute("SELECT * FROM products WHERE id = %s", (new_id,))
            new_product = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Товар успішно додано.'
            response['product'] = {
                'id': new_product[0],
                'name': new_product[1],
                'description': new_product[2]
            }
        except Exception as e:
            response['message'] = f'Помилка при додаванні товару: {e}'

        return jsonify(response)

    # Редагування товару
    @dashboard_bp.route('/products/edit', methods=['POST'])
    @role_required(['owner', 'admin', 'operator'])
    def edit_product():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            product_id = int(request.form['id'])
            name = request.form['name']
            description = request.form.get('description')

            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE products
                SET name = %s, description = %s
                WHERE id = %s
            """, (name, description, product_id))
            mysql.connection.commit()
            cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
            updated_product = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Товар успішно оновлено.'
            response['product'] = {
                'id': updated_product[0],
                'name': updated_product[1],
                'description': updated_product[2]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при оновленні товару: {e}'

        return jsonify(response)

    # Видалення товару
    @dashboard_bp.route('/products/delete', methods=['POST'])
    @role_required(['owner', 'admin'])
    def delete_product():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            product_id = int(request.form['id'])
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
            mysql.connection.commit()
            cur.close()
            response['status'] = 'success'
            response['message'] = 'Товар успішно видалено.'
        except ValueError:
            response['message'] = 'Некоректний ID товару.'
        except Exception as e:
            response['message'] = f'Помилка при видаленні товару: {e}'

        return jsonify(response)

    #                                              ======= Маршрути для Товарів від Постачальників =======

    # Список товарів від постачальників
    @dashboard_bp.route('/supplier_products')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def supplier_products():
        search_query = request.args.get('search')
        cur = mysql.connection.cursor()
        if search_query:
            cur.execute("""
                SELECT supplier_products.supplier_id, suppliers.name, supplier_products.product_id, products.name,
                       supplier_products.purchase_price
                FROM supplier_products
                JOIN suppliers ON supplier_products.supplier_id = suppliers.id
                JOIN products ON supplier_products.product_id = products.id
                WHERE suppliers.name LIKE %s OR products.name LIKE %s
            """, ('%' + search_query + '%', '%' + search_query + '%'))
        else:
            cur.execute("""
                SELECT supplier_products.supplier_id, suppliers.name, supplier_products.product_id, products.name,
                       supplier_products.purchase_price
                FROM supplier_products
                JOIN suppliers ON supplier_products.supplier_id = suppliers.id
                JOIN products ON supplier_products.product_id = products.id
            """)
        supplier_products = cur.fetchall()

        # Отримання всіх постачальників та товарів для форм
        cur.execute("SELECT id, name FROM suppliers")
        suppliers = cur.fetchall()

        cur.execute("SELECT id, name FROM products")
        products = cur.fetchall()

        cur.close()
        return render_template('supplier_products.html', supplier_products=supplier_products, suppliers=suppliers,
                               products=products)

    # Додавання товару від постачальника
    @dashboard_bp.route('/supplier_products/add', methods=['POST'])
    @role_required(['owner', 'admin'])
    def add_supplier_product():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            supplier_id = int(request.form['supplier_id'])
            product_id = int(request.form['product_id'])
            purchase_price = float(request.form['purchase_price'])

            cur = mysql.connection.cursor()
            # Перевірка чи вже існує така комбінація
            cur.execute("""
                SELECT * FROM supplier_products
                WHERE supplier_id = %s AND product_id = %s
            """, (supplier_id, product_id))
            existing = cur.fetchone()
            if existing:
                response['message'] = 'Ця комбінація постачальника та товару вже існує.'
            else:
                cur.execute("""
                    INSERT INTO supplier_products (supplier_id, product_id, purchase_price)
                    VALUES (%s, %s, %s)
                """, (supplier_id, product_id, purchase_price))
                mysql.connection.commit()
                cur.execute("""
                    SELECT supplier_products.supplier_id, suppliers.name, supplier_products.product_id, products.name,
                           supplier_products.purchase_price
                    FROM supplier_products
                    JOIN suppliers ON supplier_products.supplier_id = suppliers.id
                    JOIN products ON supplier_products.product_id = products.id
                    WHERE supplier_products.supplier_id = %s AND supplier_products.product_id = %s
                """, (supplier_id, product_id))
                new_supplier_product = cur.fetchone()
                response['status'] = 'success'
                response['message'] = 'Товар від постачальника успішно додано.'
                response['supplier_product'] = {
                    'supplier_id': new_supplier_product[0],
                    'supplier_name': new_supplier_product[1],
                    'product_id': new_supplier_product[2],
                    'product_name': new_supplier_product[3],
                    'purchase_price': new_supplier_product[4]
                }
            cur.close()
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при додаванні товару від постачальника: {e}'

        return jsonify(response)

    # Редагування товару від постачальника
    @dashboard_bp.route('/supplier_products/edit', methods=['POST'])
    @role_required(['owner', 'admin', 'operator'])
    def edit_supplier_product():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            supplier_id = int(request.form['supplier_id'])
            product_id = int(request.form['product_id'])
            purchase_price = float(request.form['purchase_price'])

            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE supplier_products
                SET purchase_price = %s
                WHERE supplier_id = %s AND product_id = %s
            """, (purchase_price, supplier_id, product_id))
            mysql.connection.commit()
            cur.execute("""
                SELECT supplier_products.supplier_id, suppliers.name, supplier_products.product_id, products.name,
                       supplier_products.purchase_price
                FROM supplier_products
                JOIN suppliers ON supplier_products.supplier_id = suppliers.id
                JOIN products ON supplier_products.product_id = products.id
                WHERE supplier_products.supplier_id = %s AND supplier_products.product_id = %s
            """, (supplier_id, product_id))
            updated_supplier_product = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Товар від постачальника успішно оновлено.'
            response['supplier_product'] = {
                'supplier_id': updated_supplier_product[0],
                'supplier_name': updated_supplier_product[1],
                'product_id': updated_supplier_product[2],
                'product_name': updated_supplier_product[3],
                'purchase_price': updated_supplier_product[4]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при оновленні товару від постачальника: {e}'

        return jsonify(response)

    # Видалення товару від постачальника
    @dashboard_bp.route('/supplier_products/delete', methods=['POST'])
    @role_required(['owner', 'admin'])
    def delete_supplier_product():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            supplier_id = int(request.form['supplier_id'])
            product_id = int(request.form['product_id'])
            cur = mysql.connection.cursor()
            cur.execute("""
                DELETE FROM supplier_products
                WHERE supplier_id = %s AND product_id = %s
            """, (supplier_id, product_id))
            mysql.connection.commit()
            cur.close()
            response['status'] = 'success'
            response['message'] = 'Товар від постачальника успішно видалено.'
        except ValueError:
            response['message'] = 'Некоректний ID постачальника або товару.'
        except Exception as e:
            response['message'] = f'Помилка при видаленні товару від постачальника: {e}'

        return jsonify(response)



    # ======= Маршрути для Price History (Історія Цін) =======

    # Список історії цін
    @dashboard_bp.route('/price_history')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def price_history():
        search_query = request.args.get('search')
        cur = mysql.connection.cursor()
        if search_query:
            cur.execute("""
                SELECT price_history.id, products.name, trading_points.name, price_history.price, price_history.start_date, price_history.end_date
                FROM price_history
                JOIN products ON price_history.product_id = products.id
                JOIN trading_points ON price_history.trading_point_id = trading_points.id
                WHERE products.name LIKE %s OR trading_points.name LIKE %s
            """, ('%' + search_query + '%', '%' + search_query + '%'))
        else:
            cur.execute("""
                SELECT price_history.id, products.name, trading_points.name, price_history.price, price_history.start_date, price_history.end_date
                FROM price_history
                JOIN products ON price_history.product_id = products.id
                JOIN trading_points ON price_history.trading_point_id = trading_points.id
            """)
        price_histories = cur.fetchall()

        # Отримання всіх продуктів та торгових точок для форм
        cur.execute("SELECT id, name FROM products")
        products = cur.fetchall()

        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()

        cur.close()
        return render_template('price_history.html', price_histories=price_histories, products=products, trading_points=trading_points)

    # Додавання запису до історії цін
    @dashboard_bp.route('/price_history/add', methods=['POST'])
    @role_required(['owner', 'admin'])
    def add_price_history():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            product_id = int(request.form['product_id'])
            trading_point_id = int(request.form['trading_point_id'])
            price = float(request.form['price'])
            start_date = request.form['start_date']
            end_date = request.form.get('end_date')  # Може бути NULL

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO price_history (product_id, trading_point_id, price, start_date, end_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (product_id, trading_point_id, price, start_date, end_date))
            mysql.connection.commit()
            new_id = cur.lastrowid
            cur.execute("""
                SELECT price_history.id, products.name, trading_points.name, price_history.price, price_history.start_date, price_history.end_date
                FROM price_history
                JOIN products ON price_history.product_id = products.id
                JOIN trading_points ON price_history.trading_point_id = trading_points.id
                WHERE price_history.id = %s
            """, (new_id,))
            new_price_history = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Запис до історії цін успішно додано.'
            response['price_history'] = {
                'id': new_price_history[0],
                'product_name': new_price_history[1],
                'trading_point_name': new_price_history[2],
                'price': new_price_history[3],
                'start_date': new_price_history[4].strftime('%Y-%m-%d'),
                'end_date': new_price_history[5].strftime('%Y-%m-%d') if new_price_history[5] else ''
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при додаванні запису до історії цін: {e}'

        return jsonify(response)

    # Редагування запису в історії цін
    @dashboard_bp.route('/price_history/edit', methods=['POST'])
    @role_required(['owner', 'admin', 'operator'])
    def edit_price_history():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            history_id = int(request.form['id'])
            price = float(request.form['price'])
            start_date = request.form['start_date']
            end_date = request.form.get('end_date')  # Може бути NULL

            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE price_history
                SET price = %s, start_date = %s, end_date = %s
                WHERE id = %s
            """, (price, start_date, end_date, history_id))
            mysql.connection.commit()
            cur.execute("""
                SELECT price_history.id, products.name, trading_points.name, price_history.price, price_history.start_date, price_history.end_date
                FROM price_history
                JOIN products ON price_history.product_id = products.id
                JOIN trading_points ON price_history.trading_point_id = trading_points.id
                WHERE price_history.id = %s
            """, (history_id,))
            updated_history = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Запис до історії цін успішно оновлено.'
            response['price_history'] = {
                'id': updated_history[0],
                'product_name': updated_history[1],
                'trading_point_name': updated_history[2],
                'price': updated_history[3],
                'start_date': updated_history[4].strftime('%Y-%m-%d'),
                'end_date': updated_history[5].strftime('%Y-%m-%d') if updated_history[5] else ''
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при оновленні запису до історії цін: {e}'

        return jsonify(response)

    # Видалення запису з історії цін
    @dashboard_bp.route('/price_history/delete', methods=['POST'])
    @role_required(['owner', 'admin'])
    def delete_price_history():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            history_id = int(request.form['id'])
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM price_history WHERE id = %s", (history_id,))
            mysql.connection.commit()
            cur.close()
            response['status'] = 'success'
            response['message'] = 'Запис з історії цін успішно видалено.'
        except ValueError:
            response['message'] = 'Некоректний ID запису.'
        except Exception as e:
            response['message'] = f'Помилка при видаленні запису з історії цін: {e}'

        return jsonify(response)

    # ======= Маршрути для Expenses (Витрати) =======

    # Список витрат
    @dashboard_bp.route('/expenses')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def expenses():
        search_query = request.args.get('search')
        cur = mysql.connection.cursor()
        if search_query:
            cur.execute("""
                SELECT expenses.id, expenses.trading_point_id, trading_points.name, expenses.expense_type, expenses.amount, expenses.start_date, expenses.end_date
                FROM expenses
                JOIN trading_points ON expenses.trading_point_id = trading_points.id
                WHERE trading_points.name LIKE %s OR expenses.expense_type LIKE %s
            """, ('%' + search_query + '%', '%' + search_query + '%'))
        else:
            cur.execute("""
                SELECT expenses.id, expenses.trading_point_id, trading_points.name, expenses.expense_type, expenses.amount, expenses.start_date, expenses.end_date
                FROM expenses
                JOIN trading_points ON expenses.trading_point_id = trading_points.id
            """)
        expenses = cur.fetchall()

        # Отримання всіх торгових точок для вибору
        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()

        cur.close()
        return render_template('expenses.html', expenses=expenses, trading_points=trading_points)

    # Додавання витрати
    @dashboard_bp.route('/expenses/add', methods=['POST'])
    @role_required(['owner', 'admin'])
    def add_expense():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            trading_point_id = int(request.form['trading_point_id'])
            expense_type = request.form['expense_type']
            amount = float(request.form['amount'])
            start_date = request.form['start_date']
            end_date = request.form.get('end_date') or None

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO expenses (trading_point_id, expense_type, amount, start_date, end_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (trading_point_id, expense_type, amount, start_date, end_date))
            mysql.connection.commit()
            new_id = cur.lastrowid
            cur.execute("""
                SELECT expenses.id, trading_points.id, trading_points.name, expenses.expense_type, expenses.amount, expenses.start_date, expenses.end_date
                FROM expenses
                JOIN trading_points ON expenses.trading_point_id = trading_points.id
                WHERE expenses.id = %s
            """, (new_id,))
            new_expense = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Витрату успішно додано.'
            response['expense'] = {
                'id': new_expense[0],
                'trading_point_id': new_expense[1],
                'trading_point_name': new_expense[2],
                'expense_type': new_expense[3],
                'amount': new_expense[4],
                'start_date': new_expense[5],
                'end_date': new_expense[6] or ''
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при додаванні витрати: {e}'

        return jsonify(response)

    # Редагування витрати
    @dashboard_bp.route('/expenses/edit', methods=['POST'])
    @role_required(['owner', 'admin', 'operator'])
    def edit_expense():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            expense_id = int(request.form['id'])
            trading_point_id = int(request.form['trading_point_id'])
            expense_type = request.form['expense_type']
            amount = float(request.form['amount'])
            start_date = request.form['start_date']
            end_date = request.form.get('end_date') or None

            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE expenses
                SET trading_point_id = %s, expense_type = %s, amount = %s, start_date = %s, end_date = %s
                WHERE id = %s
            """, (trading_point_id, expense_type, amount, start_date, end_date, expense_id))
            mysql.connection.commit()
            cur.execute("""
                SELECT expenses.id, trading_points.id, trading_points.name, expenses.expense_type, expenses.amount, expenses.start_date, expenses.end_date
                FROM expenses
                JOIN trading_points ON expenses.trading_point_id = trading_points.id
                WHERE expenses.id = %s
            """, (expense_id,))
            updated_expense = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Витрату успішно оновлено.'
            response['expense'] = {
                'id': updated_expense[0],
                'trading_point_id': updated_expense[1],
                'trading_point_name': updated_expense[2],
                'expense_type': updated_expense[3],
                'amount': updated_expense[4],
                'start_date': updated_expense[5],
                'end_date': updated_expense[6] or ''
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при оновленні витрати: {e}'

        return jsonify(response)

    # Видалення витрати
    @dashboard_bp.route('/expenses/delete', methods=['POST'])
    @role_required(['owner', 'admin'])
    def delete_expense():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            expense_id = int(request.form['id'])
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
            mysql.connection.commit()
            cur.close()
            response['status'] = 'success'
            response['message'] = 'Витрату успішно видалено.'
        except ValueError:
            response['message'] = 'Некоректний ID витрати.'
        except Exception as e:
            response['message'] = f'Помилка при видаленні витрати: {e}'

        return jsonify(response)

    # ======= Маршрути для Customers (Покупці) =======

    # Маршрути для Customers

    # Список покупців
    @dashboard_bp.route('/customers')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def customers():
        search_query = request.args.get('search')
        cur = mysql.connection.cursor()
        if search_query:
            cur.execute("""
                SELECT * FROM customers
                WHERE first_name LIKE %s OR last_name LIKE %s
            """, ('%' + search_query + '%', '%' + search_query + '%'))
        else:
            cur.execute("SELECT * FROM customers")
        customers = cur.fetchall()
        cur.close()
        return render_template('customers.html', customers=customers)

    # Додавання покупця
    @dashboard_bp.route('/customers/add', methods=['POST'])
    @role_required(['owner', 'admin'])
    def add_customer():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            phone = request.form.get('phone')
            age = int(request.form.get('age', 0))
            gender = request.form.get('gender')

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO customers (first_name, last_name, phone, age, gender)
                VALUES (%s, %s, %s, %s, %s)
            """, (first_name, last_name, phone, age, gender))
            mysql.connection.commit()
            new_id = cur.lastrowid
            cur.execute("SELECT * FROM customers WHERE id = %s", (new_id,))
            new_customer = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Покупця успішно додано.'
            response['customer'] = {
                'id': new_customer[0],
                'first_name': new_customer[1],
                'last_name': new_customer[2],
                'phone': new_customer[3],
                'age': new_customer[4],
                'gender': new_customer[5]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при додаванні покупця: {e}'
        return jsonify(response)

    # Редагування покупця
    @dashboard_bp.route('/customers/edit', methods=['POST'])
    @role_required(['owner', 'admin', 'operator'])
    def edit_customer():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            customer_id = int(request.form['id'])
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            phone = request.form.get('phone')
            age = int(request.form.get('age', 0))
            gender = request.form.get('gender')

            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE customers
                SET first_name = %s, last_name = %s, phone = %s, age = %s, gender = %s
                WHERE id = %s
            """, (first_name, last_name, phone, age, gender, customer_id))
            mysql.connection.commit()
            cur.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
            updated_customer = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Покупця успішно оновлено.'
            response['customer'] = {
                'id': updated_customer[0],
                'first_name': updated_customer[1],
                'last_name': updated_customer[2],
                'phone': updated_customer[3],
                'age': updated_customer[4],
                'gender': updated_customer[5]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при оновленні покупця: {e}'
        return jsonify(response)

    # Видалення покупця
    @dashboard_bp.route('/customers/delete', methods=['POST'])
    @role_required(['owner', 'admin'])
    def delete_customer():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            customer_id = int(request.form['id'])
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
            mysql.connection.commit()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Покупця успішно видалено.'
        except ValueError:
            response['message'] = 'Некоректний ID покупця.'
        except Exception as e:
            response['message'] = f'Помилка при видаленні покупця: {e}'
        return jsonify(response)

    # ======= Маршрути для Sales (Продажі) =======

    # Список продажів
    @dashboard_bp.route('/sales')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def sales():
        search_query = request.args.get('search')
        cur = mysql.connection.cursor()
        if search_query:
            cur.execute("""
                SELECT sales.id, products.name, customers.first_name, customers.last_name, employees.first_name,
                       trading_points.name, sales.sale_date, sales.quantity, sales.selling_price
                FROM sales
                LEFT JOIN products ON sales.product_id = products.id
                LEFT JOIN customers ON sales.customer_id = customers.id
                LEFT JOIN employees ON sales.employee_id = employees.id
                LEFT JOIN trading_points ON sales.trading_point_id = trading_points.id
                WHERE products.name LIKE %s OR customers.first_name LIKE %s OR customers.last_name LIKE %s
            """, ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
        else:
            cur.execute("""
                SELECT sales.id, products.name, customers.first_name, customers.last_name, employees.first_name,
                       trading_points.name, sales.sale_date, sales.quantity, sales.selling_price
                FROM sales
                LEFT JOIN products ON sales.product_id = products.id
                LEFT JOIN customers ON sales.customer_id = customers.id
                LEFT JOIN employees ON sales.employee_id = employees.id
                LEFT JOIN trading_points ON sales.trading_point_id = trading_points.id
            """)
        sales_data = cur.fetchall()

        # Отримання всіх продуктів, покупців, працівників та торгових точок для форм
        cur.execute("SELECT id, name FROM products")
        products = cur.fetchall()

        cur.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS full_name FROM customers")
        customers = cur.fetchall()

        cur.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS full_name FROM employees")
        employees = cur.fetchall()

        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()

        cur.close()
        return render_template('sales.html', sales=sales_data, products=products, customers=customers,
                               employees=employees, trading_points=trading_points)

    # Додавання продажу
    @dashboard_bp.route('/sales/add', methods=['POST'])
    @role_required(['owner', 'admin'])
    def add_sale():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            product_id = int(request.form['product_id'])
            customer_id = request.form.get('customer_id')
            employee_id = request.form.get('employee_id')
            trading_point_id = int(request.form['trading_point_id'])
            sale_date = request.form['sale_date']
            quantity = int(request.form['quantity'])
            selling_price = float(request.form['selling_price'])

            customer_id = int(customer_id) if customer_id else None
            employee_id = int(employee_id) if employee_id else None

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO sales (product_id, customer_id, employee_id, trading_point_id, sale_date, quantity, selling_price)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (product_id, customer_id, employee_id, trading_point_id, sale_date, quantity, selling_price))
            mysql.connection.commit()
            new_id = cur.lastrowid
            cur.execute("""
                SELECT sales.id, products.name, customers.first_name, customers.last_name, employees.first_name,
                       trading_points.name, sales.sale_date, sales.quantity, sales.selling_price
                FROM sales
                LEFT JOIN products ON sales.product_id = products.id
                LEFT JOIN customers ON sales.customer_id = customers.id
                LEFT JOIN employees ON sales.employee_id = employees.id
                LEFT JOIN trading_points ON sales.trading_point_id = trading_points.id
                WHERE sales.id = %s
            """, (new_id,))
            new_sale = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Продаж успішно додано.'
            response['sale'] = {
                'id': new_sale[0],
                'product_name': new_sale[1],
                'customer_first_name': new_sale[2] or '',
                'customer_last_name': new_sale[3] or '',
                'employee_first_name': new_sale[4] or '',
                'trading_point_name': new_sale[5],
                'sale_date': new_sale[6],
                'quantity': new_sale[7],
                'selling_price': new_sale[8]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при додаванні продажу: {e}'
        return jsonify(response)

    # Редагування продажу
    @dashboard_bp.route('/sales/edit', methods=['POST'])
    @role_required(['owner', 'admin', 'operator'])
    def edit_sale():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            sale_id = int(request.form['id'])
            product_id = int(request.form['product_id'])
            customer_id = request.form.get('customer_id')
            employee_id = request.form.get('employee_id')
            trading_point_id = int(request.form['trading_point_id'])
            sale_date = request.form['sale_date']
            quantity = int(request.form['quantity'])
            selling_price = float(request.form['selling_price'])

            customer_id = int(customer_id) if customer_id else None
            employee_id = int(employee_id) if employee_id else None

            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE sales
                SET product_id = %s, customer_id = %s, employee_id = %s, trading_point_id = %s,
                    sale_date = %s, quantity = %s, selling_price = %s
                WHERE id = %s
            """, (product_id, customer_id, employee_id, trading_point_id, sale_date, quantity, selling_price, sale_id))
            mysql.connection.commit()
            cur.execute("""
                SELECT sales.id, products.name, customers.first_name, customers.last_name, employees.first_name,
                       trading_points.name, sales.sale_date, sales.quantity, sales.selling_price
                FROM sales
                LEFT JOIN products ON sales.product_id = products.id
                LEFT JOIN customers ON sales.customer_id = customers.id
                LEFT JOIN employees ON sales.employee_id = employees.id
                LEFT JOIN trading_points ON sales.trading_point_id = trading_points.id
                WHERE sales.id = %s
            """, (sale_id,))
            updated_sale = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Продаж успішно оновлено.'
            response['sale'] = {
                'id': updated_sale[0],
                'product_name': updated_sale[1],
                'customer_first_name': updated_sale[2] or '',
                'customer_last_name': updated_sale[3] or '',
                'employee_first_name': updated_sale[4] or '',
                'trading_point_name': updated_sale[5],
                'sale_date': updated_sale[6],
                'quantity': updated_sale[7],
                'selling_price': updated_sale[8]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при оновленні продажу: {e}'
        return jsonify(response)

    # Видалення продажу
    @dashboard_bp.route('/sales/delete', methods=['POST'])
    @role_required(['owner', 'admin'])
    def delete_sale():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            sale_id = int(request.form['id'])
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM sales WHERE id = %s", (sale_id,))
            mysql.connection.commit()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Продаж успішно видалено.'
        except ValueError:
            response['message'] = 'Некоректний ID продажу.'
        except Exception as e:
            response['message'] = f'Помилка при видаленні продажу: {e}'
        return jsonify(response)

    # Маршрути для Orders

    @dashboard_bp.route('/orders')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def orders():
        search_query = request.args.get('search')
        cur = mysql.connection.cursor()
        if search_query:
            cur.execute("""
                SELECT orders.id, suppliers.name, trading_points.name, employees.first_name, orders.order_date, orders.status
                FROM orders
                JOIN suppliers ON orders.supplier_id = suppliers.id
                JOIN trading_points ON orders.trading_point_id = trading_points.id
                LEFT JOIN employees ON orders.manager_id = employees.id
                WHERE suppliers.name LIKE %s OR trading_points.name LIKE %s OR employees.first_name LIKE %s
            """, ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
        else:
            cur.execute("""
                SELECT orders.id, suppliers.name, trading_points.name, employees.first_name, orders.order_date, orders.status
                FROM orders
                JOIN suppliers ON orders.supplier_id = suppliers.id
                JOIN trading_points ON orders.trading_point_id = trading_points.id
                LEFT JOIN employees ON orders.manager_id = employees.id
            """)
        orders_data = cur.fetchall()

        # Отримання всіх постачальників, торгових точок та менеджерів для форм
        cur.execute("SELECT id, name FROM suppliers")
        suppliers = cur.fetchall()

        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()

        cur.execute("SELECT id, CONCAT(first_name, ' ', last_name) AS full_name FROM employees")
        employees = cur.fetchall()

        cur.close()
        return render_template('orders.html', orders=orders_data, suppliers=suppliers, trading_points=trading_points,
                               employees=employees)

    # Додавання замовлення
    @dashboard_bp.route('/orders/add', methods=['POST'])
    @role_required(['owner', 'admin'])
    def add_order():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            supplier_id = int(request.form['supplier_id'])
            trading_point_id = int(request.form['trading_point_id'])
            manager_id = request.form.get('manager_id')
            order_date = request.form['order_date']
            status = request.form['status']

            manager_id = int(manager_id) if manager_id else None

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO orders (supplier_id, trading_point_id, manager_id, order_date, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (supplier_id, trading_point_id, manager_id, order_date, status))
            mysql.connection.commit()
            new_id = cur.lastrowid
            cur.execute("""
                SELECT orders.id, suppliers.name, trading_points.name, employees.first_name, orders.order_date, orders.status
                FROM orders
                JOIN suppliers ON orders.supplier_id = suppliers.id
                JOIN trading_points ON orders.trading_point_id = trading_points.id
                LEFT JOIN employees ON orders.manager_id = employees.id
                WHERE orders.id = %s
            """, (new_id,))
            new_order = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Замовлення успішно додано.'
            response['order'] = {
                'id': new_order[0],
                'supplier_name': new_order[1],
                'trading_point_name': new_order[2],
                'manager_first_name': new_order[3] or '',
                'order_date': new_order[4],
                'status': new_order[5]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при додаванні замовлення: {e}'
        return jsonify(response)

    # Редагування замовлення
    @dashboard_bp.route('/orders/edit', methods=['POST'])
    @role_required(['owner', 'admin', 'operator'])
    def edit_order():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            order_id = int(request.form['id'])
            supplier_id = int(request.form['supplier_id'])
            trading_point_id = int(request.form['trading_point_id'])
            manager_id = request.form.get('manager_id')
            order_date = request.form['order_date']
            status = request.form['status']

            manager_id = int(manager_id) if manager_id else None

            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE orders
                SET supplier_id = %s, trading_point_id = %s, manager_id = %s, order_date = %s, status = %s
                WHERE id = %s
            """, (supplier_id, trading_point_id, manager_id, order_date, status, order_id))
            mysql.connection.commit()
            cur.execute("""
                SELECT orders.id, suppliers.name, trading_points.name, employees.first_name, orders.order_date, orders.status
                FROM orders
                JOIN suppliers ON orders.supplier_id = suppliers.id
                JOIN trading_points ON orders.trading_point_id = trading_points.id
                LEFT JOIN employees ON orders.manager_id = employees.id
                WHERE orders.id = %s
            """, (order_id,))
            updated_order = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Замовлення успішно оновлено.'
            response['order'] = {
                'id': updated_order[0],
                'supplier_name': updated_order[1],
                'trading_point_name': updated_order[2],
                'manager_first_name': updated_order[3] or '',
                'order_date': updated_order[4],
                'status': updated_order[5]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при оновленні замовлення: {e}'
        return jsonify(response)

    # Видалення замовлення
    @dashboard_bp.route('/orders/delete', methods=['POST'])
    @role_required(['owner', 'admin'])
    def delete_order():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            order_id = int(request.form['id'])
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM orders WHERE id = %s", (order_id,))
            mysql.connection.commit()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Замовлення успішно видалено.'
        except ValueError:
            response['message'] = 'Некоректний ID замовлення.'
        except Exception as e:
            response['message'] = f'Помилка при видаленні замовлення: {e}'
        return jsonify(response)

    # Маршрути для Order_Items

    @dashboard_bp.route('/order_items')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def order_items():
        search_query = request.args.get('search')
        cur = mysql.connection.cursor()
        if search_query:
            cur.execute("""
                SELECT order_items.id, orders.id, suppliers.name, trading_points.name, products.name, order_items.requested_quantity,
                       order_items.quantity, order_items.purchase_price
                FROM order_items
                JOIN orders ON order_items.order_id = orders.id
                JOIN suppliers ON orders.supplier_id = suppliers.id
                JOIN trading_points ON orders.trading_point_id = trading_points.id
                JOIN products ON order_items.product_id = products.id
                WHERE suppliers.name LIKE %s OR trading_points.name LIKE %s OR products.name LIKE %s
            """, ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
        else:
            cur.execute("""
                SELECT order_items.id, orders.id, suppliers.name, trading_points.name, products.name, order_items.requested_quantity,
                       order_items.quantity, order_items.purchase_price
                FROM order_items
                JOIN orders ON order_items.order_id = orders.id
                JOIN suppliers ON orders.supplier_id = suppliers.id
                JOIN trading_points ON orders.trading_point_id = trading_points.id
                JOIN products ON order_items.product_id = products.id
            """)
        order_items_data = cur.fetchall()

        # Отримання всіх замовлень та товарів для форм
        cur.execute("""
            SELECT orders.id, CONCAT('Замовлення ', orders.id) FROM orders
        """)
        orders = cur.fetchall()

        cur.execute("SELECT id, name FROM products")
        products = cur.fetchall()

        cur.close()
        return render_template('order_items.html', order_items=order_items_data, orders=orders, products=products)

    # Додавання товару в замовлення
    @dashboard_bp.route('/order_items/add', methods=['POST'])
    @role_required(['owner', 'admin'])
    def add_order_item():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            order_id = int(request.form['order_id'])
            product_id = int(request.form['product_id'])
            requested_quantity = int(request.form['requested_quantity'])
            quantity = int(request.form['quantity'])
            purchase_price = float(request.form['purchase_price'])

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO order_items (order_id, product_id, requested_quantity, quantity, purchase_price)
                VALUES (%s, %s, %s, %s, %s)
            """, (order_id, product_id, requested_quantity, quantity, purchase_price))
            mysql.connection.commit()
            new_id = cur.lastrowid
            cur.execute("""
                SELECT order_items.id, orders.id, suppliers.name, trading_points.name, products.name, order_items.requested_quantity,
                       order_items.quantity, order_items.purchase_price
                FROM order_items
                JOIN orders ON order_items.order_id = orders.id
                JOIN suppliers ON orders.supplier_id = suppliers.id
                JOIN trading_points ON orders.trading_point_id = trading_points.id
                JOIN products ON order_items.product_id = products.id
                WHERE order_items.id = %s
            """, (new_id,))
            new_order_item = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Товар в замовленні успішно додано.'
            response['order_item'] = {
                'id': new_order_item[0],
                'order_id': new_order_item[1],
                'supplier_name': new_order_item[2],
                'trading_point_name': new_order_item[3],
                'product_name': new_order_item[4],
                'requested_quantity': new_order_item[5],
                'quantity': new_order_item[6],
                'purchase_price': new_order_item[7]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при додаванні товару в замовлення: {e}'
        return jsonify(response)

    # Редагування товару в замовленні
    @dashboard_bp.route('/order_items/edit', methods=['POST'])
    @role_required(['owner', 'admin', 'operator'])
    def edit_order_item():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            order_item_id = int(request.form['id'])
            order_id = int(request.form['order_id'])
            product_id = int(request.form['product_id'])
            requested_quantity = int(request.form['requested_quantity'])
            quantity = int(request.form['quantity'])
            purchase_price = float(request.form['purchase_price'])

            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE order_items
                SET order_id = %s, product_id = %s, requested_quantity = %s, quantity = %s, purchase_price = %s
                WHERE id = %s
            """, (order_id, product_id, requested_quantity, quantity, purchase_price, order_item_id))
            mysql.connection.commit()
            cur.execute("""
                SELECT order_items.id, orders.id, suppliers.name, trading_points.name, products.name, order_items.requested_quantity,
                       order_items.quantity, order_items.purchase_price
                FROM order_items
                JOIN orders ON order_items.order_id = orders.id
                JOIN suppliers ON orders.supplier_id = suppliers.id
                JOIN trading_points ON orders.trading_point_id = trading_points.id
                JOIN products ON order_items.product_id = products.id
                WHERE order_items.id = %s
            """, (order_item_id,))
            updated_order_item = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Товар в замовленні успішно оновлено.'
            response['order_item'] = {
                'id': updated_order_item[0],
                'order_id': updated_order_item[1],
                'supplier_name': updated_order_item[2],
                'trading_point_name': updated_order_item[3],
                'product_name': updated_order_item[4],
                'requested_quantity': updated_order_item[5],
                'quantity': updated_order_item[6],
                'purchase_price': updated_order_item[7]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при оновленні товару в замовленні: {e}'
        return jsonify(response)

    # Видалення товару в замовленні
    @dashboard_bp.route('/order_items/delete', methods=['POST'])
    @role_required(['owner', 'admin'])
    def delete_order_item():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            order_item_id = int(request.form['id'])
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM order_items WHERE id = %s", (order_item_id,))
            mysql.connection.commit()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Товар в замовленні успішно видалено.'
        except ValueError:
            response['message'] = 'Некоректний ID товару в замовленні.'
        except Exception as e:
            response['message'] = f'Помилка при видаленні товару в замовленні: {e}'
        return jsonify(response)

    # Маршрути для Transfers

    @dashboard_bp.route('/transfers')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def transfers():
        search_query = request.args.get('search')
        cur = mysql.connection.cursor()
        if search_query:
            cur.execute("""
                SELECT transfers.id, products.name, from_tp.name, to_tp.name, transfers.quantity, transfers.transfer_date
                FROM transfers
                JOIN products ON transfers.product_id = products.id
                JOIN trading_points AS from_tp ON transfers.from_trading_point_id = from_tp.id
                JOIN trading_points AS to_tp ON transfers.to_trading_point_id = to_tp.id
                WHERE products.name LIKE %s OR from_tp.name LIKE %s OR to_tp.name LIKE %s
            """, ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
        else:
            cur.execute("""
                SELECT transfers.id, products.name, from_tp.name, to_tp.name, transfers.quantity, transfers.transfer_date
                FROM transfers
                JOIN products ON transfers.product_id = products.id
                JOIN trading_points AS from_tp ON transfers.from_trading_point_id = from_tp.id
                JOIN trading_points AS to_tp ON transfers.to_trading_point_id = to_tp.id
            """)
        transfers_data = cur.fetchall()

        # Отримання всіх товарів та торгових точок для форм
        cur.execute("SELECT id, name FROM products")
        products = cur.fetchall()

        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()

        cur.close()
        return render_template('transfers.html', transfers=transfers_data, products=products,
                               trading_points=trading_points)

    # Додавання передачі товару
    @dashboard_bp.route('/transfers/add', methods=['POST'])
    @role_required(['owner', 'admin'])
    def add_transfer():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            product_id = int(request.form['product_id'])
            from_trading_point_id = int(request.form['from_trading_point_id'])
            to_trading_point_id = int(request.form['to_trading_point_id'])
            quantity = int(request.form['quantity'])
            transfer_date = request.form['transfer_date']

            if from_trading_point_id == to_trading_point_id:
                response['message'] = 'Відправлення та отримання торгової точки не можуть бути однаковими.'
                return jsonify(response)

            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO transfers (product_id, from_trading_point_id, to_trading_point_id, quantity, transfer_date)
                VALUES (%s, %s, %s, %s, %s)
            """, (product_id, from_trading_point_id, to_trading_point_id, quantity, transfer_date))
            mysql.connection.commit()
            new_id = cur.lastrowid
            cur.execute("""
                SELECT transfers.id, products.name, from_tp.name, to_tp.name, transfers.quantity, transfers.transfer_date
                FROM transfers
                JOIN products ON transfers.product_id = products.id
                JOIN trading_points AS from_tp ON transfers.from_trading_point_id = from_tp.id
                JOIN trading_points AS to_tp ON transfers.to_trading_point_id = to_tp.id
                WHERE transfers.id = %s
            """, (new_id,))
            new_transfer = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Передачу товару успішно додано.'
            response['transfer'] = {
                'id': new_transfer[0],
                'product_name': new_transfer[1],
                'from_trading_point_name': new_transfer[2],
                'to_trading_point_name': new_transfer[3],
                'quantity': new_transfer[4],
                'transfer_date': new_transfer[5]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при додаванні передачі товару: {e}'
        return jsonify(response)

    # Редагування передачі товару
    @dashboard_bp.route('/transfers/edit', methods=['POST'])
    @role_required(['owner', 'admin', 'operator'])
    def edit_transfer():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            transfer_id = int(request.form['id'])
            product_id = int(request.form['product_id'])
            from_trading_point_id = int(request.form['from_trading_point_id'])
            to_trading_point_id = int(request.form['to_trading_point_id'])
            quantity = int(request.form['quantity'])
            transfer_date = request.form['transfer_date']

            if from_trading_point_id == to_trading_point_id:
                response['message'] = 'Відправлення та отримання торгової точки не можуть бути однаковими.'
                return jsonify(response)

            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE transfers
                SET product_id = %s, from_trading_point_id = %s, to_trading_point_id = %s, quantity = %s, transfer_date = %s
                WHERE id = %s
            """, (product_id, from_trading_point_id, to_trading_point_id, quantity, transfer_date, transfer_id))
            mysql.connection.commit()
            cur.execute("""
                SELECT transfers.id, products.name, from_tp.name, to_tp.name, transfers.quantity, transfers.transfer_date
                FROM transfers
                JOIN products ON transfers.product_id = products.id
                JOIN trading_points AS from_tp ON transfers.from_trading_point_id = from_tp.id
                JOIN trading_points AS to_tp ON transfers.to_trading_point_id = to_tp.id
                WHERE transfers.id = %s
            """, (transfer_id,))
            updated_transfer = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Передачу товару успішно оновлено.'
            response['transfer'] = {
                'id': updated_transfer[0],
                'product_name': updated_transfer[1],
                'from_trading_point_name': updated_transfer[2],
                'to_trading_point_name': updated_transfer[3],
                'quantity': updated_transfer[4],
                'transfer_date': updated_transfer[5]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при оновленні передачі товару: {e}'
        return jsonify(response)

    # Видалення передачі товару
    @dashboard_bp.route('/transfers/delete', methods=['POST'])
    @role_required(['owner', 'admin'])
    def delete_transfer():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            transfer_id = int(request.form['id'])
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM transfers WHERE id = %s", (transfer_id,))
            mysql.connection.commit()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Передачу товару успішно видалено.'
        except ValueError:
            response['message'] = 'Некоректний ID передачі товару.'
        except Exception as e:
            response['message'] = f'Помилка при видаленні передачі товару: {e}'
        return jsonify(response)

    # Маршрути для Stocks

    @dashboard_bp.route('/stocks')
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def stocks():
        search_query = request.args.get('search')
        cur = mysql.connection.cursor()
        if search_query:
            cur.execute("""
                SELECT stocks.trading_point_id, trading_points.name, stocks.product_id, products.name, stocks.quantity
                FROM stocks
                JOIN trading_points ON stocks.trading_point_id = trading_points.id
                JOIN products ON stocks.product_id = products.id
                WHERE trading_points.name LIKE %s OR products.name LIKE %s
            """, ('%' + search_query + '%', '%' + search_query + '%'))
        else:
            cur.execute("""
                SELECT stocks.trading_point_id, trading_points.name, stocks.product_id, products.name, stocks.quantity
                FROM stocks
                JOIN trading_points ON stocks.trading_point_id = trading_points.id
                JOIN products ON stocks.product_id = products.id
            """)
        stocks_data = cur.fetchall()

        # Отримання всіх торгових точок та товарів для форм
        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()

        cur.execute("SELECT id, name FROM products")
        products = cur.fetchall()

        cur.close()
        return render_template('stocks.html', stocks=stocks_data, trading_points=trading_points, products=products)

    # Додавання запасу
    @dashboard_bp.route('/stocks/add', methods=['POST'])
    @role_required(['owner', 'admin'])
    def add_stock():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            trading_point_id = int(request.form['trading_point_id'])
            product_id = int(request.form['product_id'])
            quantity = int(request.form['quantity'])

            cur = mysql.connection.cursor()
            # Перевірка, чи існує вже запис
            cur.execute("""
                SELECT quantity FROM stocks
                WHERE trading_point_id = %s AND product_id = %s
            """, (trading_point_id, product_id))
            existing = cur.fetchone()
            if existing:
                new_quantity = existing[0] + quantity
                cur.execute("""
                    UPDATE stocks
                    SET quantity = %s
                    WHERE trading_point_id = %s AND product_id = %s
                """, (new_quantity, trading_point_id, product_id))
                mysql.connection.commit()
                cur.execute("""
                    SELECT stocks.trading_point_id, trading_points.name, stocks.product_id, products.name, stocks.quantity
                    FROM stocks
                    JOIN trading_points ON stocks.trading_point_id = trading_points.id
                    JOIN products ON stocks.product_id = products.id
                    WHERE stocks.trading_point_id = %s AND stocks.product_id = %s
                """, (trading_point_id, product_id))
                updated_stock = cur.fetchone()
                response['message'] = 'Запас успішно оновлено.'
            else:
                cur.execute("""
                    INSERT INTO stocks (trading_point_id, product_id, quantity)
                    VALUES (%s, %s, %s)
                """, (trading_point_id, product_id, quantity))
                mysql.connection.commit()
                cur.execute("""
                    SELECT stocks.trading_point_id, trading_points.name, stocks.product_id, products.name, stocks.quantity
                    FROM stocks
                    JOIN trading_points ON stocks.trading_point_id = trading_points.id
                    JOIN products ON stocks.product_id = products.id
                    WHERE stocks.trading_point_id = %s AND stocks.product_id = %s
                """, (trading_point_id, product_id))
                updated_stock = cur.fetchone()
                response['message'] = 'Запас успішно додано.'
            cur.close()

            response['status'] = 'success'
            response['stock'] = {
                'trading_point_id': updated_stock[0],
                'trading_point_name': updated_stock[1],
                'product_id': updated_stock[2],
                'product_name': updated_stock[3],
                'quantity': updated_stock[4]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при додаванні запасу: {e}'
        return jsonify(response)

    # Редагування запасу
    @dashboard_bp.route('/stocks/edit', methods=['POST'])
    @role_required(['owner', 'admin', 'operator'])
    def edit_stock():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            trading_point_id = int(request.form['trading_point_id'])
            product_id = int(request.form['product_id'])
            quantity = int(request.form['quantity'])

            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE stocks
                SET quantity = %s
                WHERE trading_point_id = %s AND product_id = %s
            """, (quantity, trading_point_id, product_id))
            mysql.connection.commit()
            cur.execute("""
                SELECT stocks.trading_point_id, trading_points.name, stocks.product_id, products.name, stocks.quantity
                FROM stocks
                JOIN trading_points ON stocks.trading_point_id = trading_points.id
                JOIN products ON stocks.product_id = products.id
                WHERE stocks.trading_point_id = %s AND stocks.product_id = %s
            """, (trading_point_id, product_id))
            updated_stock = cur.fetchone()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Запас успішно оновлено.'
            response['stock'] = {
                'trading_point_id': updated_stock[0],
                'trading_point_name': updated_stock[1],
                'product_id': updated_stock[2],
                'product_name': updated_stock[3],
                'quantity': updated_stock[4]
            }
        except ValueError:
            response['message'] = 'Помилка: Введено некоректне значення. Перевірте правильність введених даних.'
        except Exception as e:
            response['message'] = f'Помилка при оновленні запасу: {e}'
        return jsonify(response)

    # Видалення запасу
    @dashboard_bp.route('/stocks/delete', methods=['POST'])
    @role_required(['owner', 'admin'])
    def delete_stock():
        response = {'status': 'error', 'message': 'Щось пішло не так.'}
        try:
            trading_point_id = int(request.form['trading_point_id'])
            product_id = int(request.form['product_id'])
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM stocks WHERE trading_point_id = %s AND product_id = %s",
                        (trading_point_id, product_id))
            mysql.connection.commit()
            cur.close()

            response['status'] = 'success'
            response['message'] = 'Запас успішно видалено.'
        except ValueError:
            response['message'] = 'Некоректний ID торгової точки або товару.'
        except Exception as e:
            response['message'] = f'Помилка при видаленні запасу: {e}'
        return jsonify(response)

    @dashboard_bp.route('/queries', methods=['GET', 'POST'])
    def queries():
        return render_template('queries.html')

    @dashboard_bp.route('/query_active_customers', methods=['GET', 'POST'])
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def query_active_customers():
        cur = mysql.connection.cursor()

        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()

        results = []
        if request.method == 'POST':

            trading_point_id = request.form.get('trading_point_id')
            point_type = request.form.get('type')


            if trading_point_id:
                cur.execute("""
                    SELECT c.id, c.first_name, c.last_name, COUNT(s.id) AS purchase_count
                    FROM customers c
                    JOIN sales s ON c.id = s.customer_id
                    WHERE s.trading_point_id = %s
                    GROUP BY c.id
                    ORDER BY purchase_count DESC
                    LIMIT 10
                """, (trading_point_id,))
            elif point_type:
                cur.execute("""
                    SELECT c.id, c.first_name, c.last_name, COUNT(s.id) AS purchase_count
                    FROM customers c
                    JOIN sales s ON c.id = s.customer_id
                    JOIN trading_points tp ON s.trading_point_id = tp.id
                    WHERE tp.type = %s
                    GROUP BY c.id
                    ORDER BY purchase_count DESC
                    LIMIT 10
                """, (point_type,))
            else:
                cur.execute("""
                    SELECT c.id, c.first_name, c.last_name, COUNT(s.id) AS purchase_count
                    FROM customers c
                    JOIN sales s ON c.id = s.customer_id
                    GROUP BY c.id
                    ORDER BY purchase_count DESC
                    LIMIT 10
                """)

            results = cur.fetchall()

        cur.close()

        return render_template(
            'query_active_customers.html',
            trading_points=trading_points,
            results=results
        )

    @dashboard_bp.route('/query_product_volume_prices', methods=['GET', 'POST'])
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def query_product_volume_prices():
        cur = mysql.connection.cursor()

        # Отримання списку товарів і торгових точок для фільтра
        cur.execute("SELECT id, name FROM products")
        products = cur.fetchall()

        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()

        results = []
        if request.method == 'POST':
            # Отримання параметрів з форми
            product_id = request.form.get('product_id')
            trading_point_id = request.form.get('trading_point_id')
            point_type = request.form.get('type')

            # Формування SQL-запиту залежно від фільтрів
            if trading_point_id:
                cur.execute("""
                    SELECT tp.name AS trading_point_name, p.name AS product_name, SUM(s.quantity) AS total_quantity, AVG(s.selling_price) AS avg_price
                    FROM sales s
                    JOIN products p ON s.product_id = p.id
                    JOIN trading_points tp ON s.trading_point_id = tp.id
                    WHERE s.product_id = %s AND s.trading_point_id = %s
                    GROUP BY tp.name, p.name
                """, (product_id, trading_point_id))
            elif point_type:
                cur.execute("""
                    SELECT tp.name AS trading_point_name, p.name AS product_name, SUM(s.quantity) AS total_quantity, AVG(s.selling_price) AS avg_price
                    FROM sales s
                    JOIN products p ON s.product_id = p.id
                    JOIN trading_points tp ON s.trading_point_id = tp.id
                    WHERE s.product_id = %s AND tp.type = %s
                    GROUP BY tp.name, p.name
                """, (product_id, point_type))
            else:
                cur.execute("""
                    SELECT tp.name AS trading_point_name, p.name AS product_name, SUM(s.quantity) AS total_quantity, AVG(s.selling_price) AS avg_price
                    FROM sales s
                    JOIN products p ON s.product_id = p.id
                    JOIN trading_points tp ON s.trading_point_id = tp.id
                    WHERE s.product_id = %s
                    GROUP BY tp.name, p.name
                """, (product_id,))

            results = cur.fetchall()

        cur.close()

        return render_template(
            'query_product_volume_prices.html',
            products=products,
            trading_points=trading_points,
            results=results
        )

    @dashboard_bp.route('/dashboard/query_supplier_deliveries', methods=['GET', 'POST'])
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def query_supplier_deliveries():
        cur = mysql.connection.cursor()

        # Отримання списку постачальників і продуктів
        cur.execute("SELECT id, name FROM suppliers")
        suppliers = cur.fetchall()

        cur.execute("SELECT id, name FROM products")
        products = cur.fetchall()

        deliveries = None
        if request.method == 'POST':
            supplier_id = request.form.get('supplier_id', type=int)
            product_id = request.form.get('product_id', type=int)
            order_number = request.form.get('order_number', type=int)
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')

            # Формування запиту
            query = """
                SELECT 
                    oi.id AS order_item_id,
                    o.id AS order_id,
                    s.name AS supplier_name,
                    p.name AS product_name,
                    oi.quantity AS delivered_quantity,
                    oi.purchase_price AS price_per_unit,
                    o.order_date AS delivery_date
                FROM order_items oi
                JOIN orders o ON oi.order_id = o.id
                JOIN suppliers s ON o.supplier_id = s.id
                JOIN products p ON oi.product_id = p.id
                WHERE 
                    (%s IS NULL OR o.supplier_id = %s)
                    AND (%s IS NULL OR oi.product_id = %s)
                    AND (%s IS NULL OR o.order_date >= %s)
                    AND (%s IS NULL OR o.order_date <= %s)
                    AND (%s IS NULL OR o.id = %s);
            """
            cur.execute(query, (
                supplier_id, supplier_id,
                product_id, product_id,
                start_date, start_date,
                end_date, end_date,
                order_number, order_number
            ))
            deliveries = cur.fetchall()

        cur.close()

        return render_template(
            'query_supplier_deliveries.html',
            suppliers=suppliers,
            products=products,
            deliveries=deliveries
        )

    @dashboard_bp.route('/dashboard/query_salaries', methods=['GET', 'POST'])
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def query_salaries():
        cur = mysql.connection.cursor()

        cur.execute("SELECT DISTINCT type FROM trading_points")
        trading_point_types = cur.fetchall()

        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()

        salaries = None
        if request.method == 'POST':
            type_ = request.form.get('type')
            trading_point_id = request.form.get('trading_point_id', type=int)

            query = """
                SELECT 
                    e.first_name,
                    e.last_name,
                    e.position,
                    e.salary,
                    tp.name AS trading_point
                FROM employees e
                JOIN trading_points tp ON e.trading_point_id = tp.id
                WHERE 
                    (%s IS NULL OR tp.type = %s)
                    AND (%s IS NULL OR tp.id = %s);
            """
            cur.execute(query, (type_, type_, trading_point_id, trading_point_id))
            salaries = cur.fetchall()

        cur.close()

        return render_template(
            'query_salaries.html',
            salaries=salaries,
            trading_point_types=trading_point_types,
            trading_points=trading_points
        )

    @dashboard_bp.route('/dashboard/query_sales_volume', methods=['GET', 'POST'])
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def query_sales_volume():
        cur = mysql.connection.cursor()

        cur.execute("SELECT id, name FROM products")
        products = cur.fetchall()

        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()

        sales = None
        if request.method == 'POST':
            product_id = request.form.get('product_id', type=int)
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            type_ = request.form.get('type')
            trading_point_id = request.form.get('trading_point_id', type=int)

            query = """
                SELECT 
                    p.name AS product_name,
                    SUM(s.quantity) AS total_quantity,
                    tp.name AS trading_point
                FROM sales s
                JOIN products p ON s.product_id = p.id
                JOIN trading_points tp ON s.trading_point_id = tp.id
                WHERE 
                    s.product_id = %s
                    AND s.sale_date BETWEEN %s AND %s
                    AND (%s IS NULL OR tp.type = %s)
                    AND (%s IS NULL OR tp.id = %s)
                GROUP BY p.name, tp.name;
            """
            cur.execute(query, (product_id, start_date, end_date, type_, type_, trading_point_id, trading_point_id))
            sales = cur.fetchall()

        cur.close()

        return render_template(
            'query_sales_volume.html',
            products=products,
            trading_points=trading_points,
            sales=sales
        )

    @dashboard_bp.route('/dashboard/query_profitability', methods=['GET', 'POST'])
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def query_profitability():
        cur = mysql.connection.cursor()

        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()

        profitability = None
        if request.method == 'POST':
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            trading_point_id = request.form.get('trading_point_id', type=int)

            query = """
                SELECT 
                    tp.name AS trading_point,
                    COALESCE(SUM(s.quantity * s.selling_price), 0) AS sales_volume,
                    (COALESCE(SUM(e.salary), 0) + COALESCE(tp.rent_fee, 0) + COALESCE(tp.utility_costs, 0)) AS overhead_costs,
                    CASE 
                        WHEN (COALESCE(SUM(e.salary), 0) + COALESCE(tp.rent_fee, 0) + COALESCE(tp.utility_costs, 0)) = 0 THEN NULL
                        ELSE COALESCE(SUM(s.quantity * s.selling_price), 0) /
                             (COALESCE(SUM(e.salary), 0) + COALESCE(tp.rent_fee, 0) + COALESCE(tp.utility_costs, 0))
                    END AS profitability_ratio
                FROM trading_points tp
                LEFT JOIN employees e ON e.trading_point_id = tp.id
                LEFT JOIN sales s ON s.trading_point_id = tp.id AND s.sale_date BETWEEN %s AND %s
                WHERE (%s IS NULL OR tp.id = %s)
                GROUP BY tp.id;
            """
            cur.execute(query, (start_date, end_date, trading_point_id, trading_point_id))
            profitability = cur.fetchall()

        cur.close()

        return render_template(
            'query_profitability.html',
            trading_points=trading_points,
            profitability=profitability
        )

    @dashboard_bp.route('/dashboard/query_turnover', methods=['GET', 'POST'])
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def query_turnover():
        cur = mysql.connection.cursor()

        cur.execute("SELECT DISTINCT type FROM trading_points")
        trading_point_types = cur.fetchall()

        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()

        turnover = None
        if request.method == 'POST':
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            group_type = request.form.get('group_type')
            trading_point_id = request.form.get('trading_point_id', type=int)

            query = """
                SELECT 
                    tp.name AS trading_point,
                    tp.type AS type,
                    COALESCE(SUM(s.quantity * s.selling_price), 0) AS turnover
                FROM trading_points tp
                LEFT JOIN sales s ON s.trading_point_id = tp.id AND s.sale_date BETWEEN %s AND %s
                WHERE (%s IS NULL OR tp.type = %s) AND (%s IS NULL OR tp.id = %s)
                GROUP BY tp.id;
            """
            cur.execute(query, (start_date, end_date, group_type, group_type, trading_point_id, trading_point_id))
            turnover = cur.fetchall()

        cur.close()

        return render_template(
            'query_turnover.html',
            trading_points=trading_points,
            trading_point_types=trading_point_types,
            turnover=turnover
        )

    @dashboard_bp.route('/dashboard/query_inventory', methods=['GET', 'POST'])
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def query_inventory():
        cur = mysql.connection.cursor()

        cur.execute("SELECT id, name FROM trading_points")
        trading_points = cur.fetchall()

        inventory = None
        if request.method == 'POST':
            trading_point_id = request.form.get('trading_point_id', type=int)

            query = """
                SELECT 
                    p.name AS product_name,
                    COALESCE(s.quantity, 0) AS quantity
                FROM products p
                LEFT JOIN stocks s ON s.product_id = p.id AND s.trading_point_id = %s
                WHERE %s IS NOT NULL;
            """
            cur.execute(query, (trading_point_id, trading_point_id))
            inventory = cur.fetchall()

        cur.close()

        return render_template(
            'query_inventory.html',
            trading_points=trading_points,
            inventory=inventory
        )

    @dashboard_bp.route('/dashboard/query_customers', methods=['GET', 'POST'])
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def query_customers():
        cur = mysql.connection.cursor()

        cur.execute("SELECT id, name FROM products")
        products = cur.fetchall()

        customers = None
        total_customers = 0
        if request.method == 'POST':
            product_id = request.form.get('product_id', type=int)
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            min_quantity = request.form.get('min_quantity', type=int)

            conditions = []
            params = []

            if product_id:
                conditions.append("s.product_id = %s")
                params.append(product_id)

            if start_date:
                conditions.append("s.sale_date >= %s")
                params.append(start_date)

            if end_date:
                conditions.append("s.sale_date <= %s")
                params.append(end_date)

            if min_quantity:
                conditions.append("s.quantity >= %s")
                params.append(min_quantity)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = f"""
                SELECT DISTINCT c.first_name, c.last_name, c.phone
                FROM sales s
                JOIN customers c ON s.customer_id = c.id
                WHERE {where_clause};
            """

            count_query = f"""
                SELECT COUNT(DISTINCT c.id)
                FROM sales s
                JOIN customers c ON s.customer_id = c.id
                WHERE {where_clause};
            """

            cur.execute(query, params)
            customers = cur.fetchall()

            cur.execute(count_query, params)
            total_customers = cur.fetchone()[0]

        cur.close()

        return render_template(
            'query_customers.html',
            products=products,
            customers=customers,
            total_customers=total_customers
        )

    @dashboard_bp.route('/dashboard/query_suppliers', methods=['GET', 'POST'])
    @role_required(['owner', 'admin', 'operator', 'guest'])
    def query_suppliers():
        cur = mysql.connection.cursor()

        cur.execute("SELECT id, name FROM products")
        products = cur.fetchall()

        suppliers = None
        total_suppliers = 0
        if request.method == 'POST':
            product_id = request.form.get('product_id', type=int)
            min_quantity = request.form.get('min_quantity', type=int)
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')

            conditions = []
            params = []

            if product_id:
                conditions.append("oi.product_id = %s")
                params.append(product_id)

            if min_quantity:
                conditions.append("oi.quantity >= %s")
                params.append(min_quantity)

            if start_date:
                conditions.append("o.order_date >= %s")
                params.append(start_date)

            if end_date:
                conditions.append("o.order_date <= %s")
                params.append(end_date)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = f"""
                SELECT DISTINCT s.name, s.contact_phone
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN suppliers s ON o.supplier_id = s.id
                WHERE {where_clause};
            """

            count_query = f"""
                SELECT COUNT(DISTINCT s.id)
                FROM orders o
                JOIN order_items oi ON o.id = oi.order_id
                JOIN suppliers s ON o.supplier_id = s.id
                WHERE {where_clause};
            """

            cur.execute(query, params)
            suppliers = cur.fetchall()

            cur.execute(count_query, params)
            total_suppliers = cur.fetchone()[0]

        cur.close()

        return render_template(
            'query_suppliers.html',
            products=products,
            suppliers=suppliers,
            total_suppliers=total_suppliers
        )

    # ======= Маршрут для адмін-панелі =======

    @dashboard_bp.route('/admin', methods=['GET', 'POST'])
    @role_required(['owner', 'admin'])
    def admin_panel():
        if request.method == 'POST':

            login = request.form['login']
            password = request.form['password']
            access_right = request.form['access_right']

            if session.get('role') == 'admin' and access_right == 'admin':
                flash('Адміністратор не може додавати інших адміністраторів.', 'error')
                return redirect(url_for('dashboard.admin_panel'))

            cur = mysql.connection.cursor()
            try:
                cur.execute("INSERT INTO `Keys` (login, password, access_right) VALUES (%s, %s, %s)",
                            (login, password, access_right))
                mysql.connection.commit()
                flash('Користувача успішно додано.', 'success')
            except Exception as e:
                flash('Помилка додавання користувача: ' + str(e), 'error')
            finally:
                cur.close()
            return redirect(url_for('dashboard.admin_panel'))
        else:

            if session.get('role') == 'owner':

                cur = mysql.connection.cursor()
                cur.execute("SELECT * FROM `Keys`")
                users = cur.fetchall()
                cur.close()
                return render_template('admin_panel.html', users=users)
            else:

                return render_template('admin_panel.html')

    # ======= Маршрути для видалення користувача =======

    @dashboard_bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
    @role_required(['owner'])
    def delete_user(user_id):
        # Запобігаємо видаленню самого себе
        if user_id == session.get('user'):
            flash('Ви не можете видалити самого себе.', 'error')
            return redirect(url_for('dashboard.admin_panel'))

        cur = mysql.connection.cursor()
        try:
            cur.execute("DELETE FROM `Keys` WHERE id = %s", (user_id,))
            mysql.connection.commit()
            flash('Користувача видалено.', 'success')
        except Exception as e:
            flash('Помилка видалення користувача: ' + str(e), 'error')
        finally:
            cur.close()
        return redirect(url_for('dashboard.admin_panel'))

    # ======= Маршрути для керування таблицями =======

    @dashboard_bp.route('/admin/delete_table', methods=['POST'])
    @role_required(['owner'])
    def delete_table():
        table_name = request.form['delete_table_name']
        if not table_name.isidentifier():
            flash('Некоректна назва таблиці.', 'error')
            return redirect(url_for('dashboard.admin_panel'))
        cur = mysql.connection.cursor()
        try:
            cur.execute(f"SHOW TABLES LIKE %s", (table_name,))
            table_exists = cur.fetchone()
            if not table_exists:
                flash(f"Таблиця {table_name} не існує.", 'error')
            else:
                cur.execute(f"DROP TABLE {table_name}")
                mysql.connection.commit()
                flash(f"Таблицю {table_name} успішно видалено.", 'success')

        except Exception as e:
            flash(f"Помилка при видаленні таблиці: {e}", 'error')
        finally:
            cur.close()

        return redirect(url_for('dashboard.admin_panel'))
