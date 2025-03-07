from flask import Flask
from flask_mysqldb import MySQL
from auth.routes import auth_bp, create_auth_routes
from dashboard.routes import dashboard_bp, create_dashboard_routes

app = Flask(__name__)
app.config.from_object('config.Config')

mysql = MySQL(app)

create_auth_routes(app, mysql)
create_dashboard_routes(app, mysql)

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)

if __name__ == '__main__':
    app.run(debug=True)
