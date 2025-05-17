from . import db
import datetime
from sqlalchemy import  TypeDecorator, String, DateTime, Float, JSON
from flask_login import UserMixin
class Json(TypeDecorator):

    impl = String

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        return json.loads(value)

# Define User data-model.
class User(db.Model, UserMixin):

    # Connect to `user` table.
    __tablename__ = "user"

    # ID as primary keys, required by SQLAlchemy.
    id = db.Column(db.Integer, primary_key=True) 

    # Email with unique and non-nullable constraint.
    email = db.Column(db.String(100), unique=True, nullable=False)

    # Password with non-nullable constraint.
    password = db.Column(db.String(100), nullable=False)

    # Name with nullable constraint.
    name = db.Column(db.String(100), unique=False, nullable=True )

    # Username with unique constraint.
    username = db.Column(db.String(100), unique=True)

    # Role with non-nullable constraint.
    role = db.Column(db.String(100), unique=False, nullable=False)

    # Department with nullable constraint.
    department = db.Column(String(100), unique=False, nullable=True)

    # Department role with nullable constraint.
    department_role = db.Column(String(100), unique=False, nullable=True)

    # Pages to be shown to the user with nullable constraint.
    user_pages = db.Column(JSON, unique=False, nullable=True)
    
    # Actions allowed; for users to perform VIEW, DOWNLOAD, UPLOAD, DELETE 
    user_actions = db.Column(JSON, unique=False, nullable=True)

    # Relationship with `Report` model.
    reports = db.relationship('Report', backref='user', lazy=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Define Report data-model.
class Report(db.Model, UserMixin):

    # Connect to `report` table.
    __tablename__ = "report"

    # ID as primary keys, required by SQLAlchemy.
    id = db.Column(db.Integer, primary_key=True)

    # Filename with unique and non-nullable constraint.
    filename = db.Column(db.String(100), unique=True, nullable=False)

    # Filesize with field type float.
    filesize = db.Column(db.Float)

    # Field with nullable constraint.
    field = db.Column(db.String(100), nullable=True)

    # Reference hash with unique constraint.
    ref_hash = db.Column(db.String(100), unique=True)

    # Created date with default value current date.
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # File date with default value current date.
    file_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # user_id as foreign key referencing to `user` table.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name in ['filename','filesize','ref_hash','created_date','file_date','field']}

    

