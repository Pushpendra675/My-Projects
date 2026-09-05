import os
from flask import Flask
from flask_login import current_user

from config import Config
from database import db, login_manager


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(Config.PROFILE_UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.PORTFOLIO_UPLOAD_FOLDER, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    # Import models so SQLAlchemy registers them before create_all()
    import models  # noqa: F401

    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.client import client_bp
    from routes.professional import professional_bp
    from routes.messages import messages_bp
    from routes.notifications import notifications_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(professional_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_globals():
        unread_count = 0
        if current_user.is_authenticated:
            unread_count = current_user.unread_notification_count()
        return {"unread_notification_count": unread_count}

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        db.session.rollback()
        return render_template("errors/500.html"), 500

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
