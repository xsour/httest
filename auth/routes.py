from flask import Blueprint, render_template, request, redirect, url_for, flash, session

auth_bp = Blueprint('auth', __name__, template_folder='templates')


def create_auth_routes(app, mysql):
    @app.before_request
    def require_login():
        allowed_routes = ['auth.login', 'auth.register', 'auth.forgot_password', 'static']
        if request.endpoint not in allowed_routes and 'user' not in session:
            flash('Ви повинні увійти в систему, щоб переглянути цю сторінку.', 'error')
            return redirect(url_for('auth.login'))

    @auth_bp.route('/login', methods=['GET', 'POST'])
    def login():
        if 'user' in session:
            flash('Ви вже увійшли в систему.', 'info')
            return redirect(url_for('dashboard.dashboard'))

        if request.method == 'POST':
            user_login = request.form['login']
            password = request.form['password']

            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM `Keys` WHERE login = %s", (user_login,))
            user = cur.fetchone()
            cur.close()

            if user and user[2] == password:
                session['user'] = user[0]
                session['username'] = user[1]
                session['role'] = user[3]
                flash('Успішний вхід', 'success')
                return redirect(url_for('dashboard.dashboard'))
            else:
                flash('Невірні дані для входу', 'error')
                return redirect(url_for('auth.login'))
        return render_template('login.html')

    @auth_bp.route('/register', methods=['GET', 'POST'])
    def register():
        if 'user' in session:
            flash('Ви вже увійшли в систему.', 'info')
            return redirect(url_for('dashboard.dashboard'))

        if request.method == 'POST':
            user_login = request.form['login']
            password = request.form['password']
            confirm_password = request.form['confirm_password']

            if password != confirm_password:
                flash('Паролі не співпадають. Спробуйте ще раз.', 'error')
                return redirect(url_for('auth.register'))

            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM `Keys` WHERE login = %s", (user_login,))
            user = cur.fetchone()
            if user:
                flash('Користувач з таким логіном вже існує. Спробуйте ще раз.', 'error')
                return redirect(url_for('auth.register'))

            cur.execute("INSERT INTO `Keys` (login, password, access_right) VALUES (%s, %s, %s)",
                        (user_login, password, 'guest'))
            mysql.connection.commit()
            cur.close()

            flash('Користувача успішно зареєстровано', 'success')
            return redirect(url_for('auth.login'))

        return render_template('register.html')

    @auth_bp.route('/forgot_password', methods=['GET', 'POST'])
    def forgot_password():
        if 'user' in session:
            flash('Ви вже увійшли в систему.', 'info')
            return redirect(url_for('dashboard.dashboard'))

        if request.method == 'POST':
            user_login = request.form['login']

            cur = mysql.connection.cursor()
            cur.execute("SELECT password FROM `Keys` WHERE login = %s", (user_login,))
            user = cur.fetchone()
            cur.close()

            if user:
                flash(f'Ваш пароль: {user[0]}', 'info')
            else:
                flash('Користувача не знайдено', 'error')

            return redirect(url_for('auth.forgot_password'))

        return render_template('forgot_password.html')

    @auth_bp.route('/logout', methods=['POST', 'GET'])
    def logout():
        session.pop('user', None)
        session.pop('role', None)
        flash('Ви успішно вийшли з системи.', 'success')
        return redirect(url_for('auth.login'))


