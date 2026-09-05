import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'editorconnect.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    PROFILE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "profiles")
    PORTFOLIO_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, "portfolio")
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "webm"}
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB

    PROFESSIONS = [
        "Video Editor",
        "Photographer",
        "Videographer",
        "Drone Operator",
        "Graphic Designer",
        "Colorist",
        "Motion Designer",
        "Thumbnail Designer",
        "Sound Engineer",
        "Content Creator",
    ]
