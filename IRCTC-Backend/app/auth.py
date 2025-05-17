from flask import Blueprint, request, url_for, redirect, jsonify, current_app
from . import db
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
import logging
from flask_cors import cross_origin

auth = Blueprint('auth', __name__)


#### Refrencing current app handler to initiate logging
log = current_app

@auth.route('/signin', methods=['POST'])
def login():
    """
    Login Endpoint queries db for password, stores and starts a login session.

    :param: request form email
    :param: request from password

    :return: jsonify response success status code
    :rtype: JSON
    """

    # Get argument data from signin form.
    email = request.json['email']
    password = request.json['password']

    print(email, password)

    # Logging for attempted signin.
    log.logger.warn(f'Attempted login from {email}')

    # Check `email` and `password` are entered.
    if email != None and password != None:

        # Fetch user details using `email`.
        user = User.query.filter_by(email=email).first()
        
        print(f'USR_DATA: {user.to_dict()}')

        # Verify password.
        if not user or not check_password_hash(user.password, password):

            # Logging for failed login.
            log.logger.warn(f'Login fail from {email}')

            # Return status code and response message.
            return jsonify({'detail': 'LOGIN_BAD_CREDENTIALS'}), 403
        
        # Login successful.
        login_user(user,remember=True)

        # Logging for successful signin.
        log.logger.info(f'Successful login from {email}')

        # Return status code and response message.
        return jsonify({
            'detail': 'LOGIN_SUCCESS', 
            'role': user.role,
            'dept': user.department,
            'user_pages': user.user_pages,
            'user_actions': user.user_actions,
        }), 200
    
    else:
        # Return status code and response message.
        return jsonify({'detail':'NOT_AUTHENTICATED'}), 403

@auth.route('/user', methods=['POST']) 
def auth_user():
    """
    User details

    :return: jsonify response success status code
    :rtype: JSON
    """

    # Check if current user is authenticated.
    if not current_user.is_authenticated:

            # Return status code and response message.
            return current_app.login_manager.unauthorized()
    
    try:
        # Fetch user details using current user's `email`.
        user = User.query.filter_by(email=current_user.email).first()

        # If user is not found or invalid.
        if not user:

            # Logging for unauthorized access of user endpoint.
            log.logger.warn(f'{current_user.email} attempted user endpoint')

            # Return status code and response message.
            return jsonify({'detail':'NOT_AUTHENTICATED'}), 403
        
        # Convert to dictionary.
        user_dict = user.to_dict()

        # Remove password key-value pair from dictionary.
        del user_dict['password']

        # Logging for user endpoint access.
        log.logger.info(f'{current_user.email} accessed user endpoint successfully')

        # Return status code and response message.
        return jsonify(user_dict), 200
    
    except:
        # Return status code and response message.
        return jsonify({'detail':'SERVER_ERROR'}), 503


@auth.route('/signup', methods=['POST'])
@login_required
def signup():
    """
    Signup Endpoint requires authenticated user with admin role to signup a user stores into db

    :param: email
    :param: password
    :param: name
    :param: username
    :param: role

    :return: jsonfiy response success with status code
    :rtype: JSON

    """
    # Check if current user role is not `admin`.
    if current_user.role != 'admin':

        # Logging for unauthorized signup.
        log.logger.warn(f'{current_user.name} attempted signup endpoint')

        # Return status code and response message.
        return jsonify({'detail':'INVALID_PERMISSIONS'}), 403
    
    # Get argument data from signup form.
    email = request.json['email']
    password = request.json['password']
    name = request.json['name']
    username = request.json['username']
    role = request.json['role']
    department = request.json['department']
    departmentrole = request.json['departmentrole']
    user_pages = request.json['user_pages']
    user_actions = request.json['user_actions']

    # Fetching user by `email`.
    user = User.query.filter_by(email=email).first()

    # If user is already signed up.
    if user:

        # Logging for unauthorized signup.
        log.logger.warn(f'{current_user.name} attempted signup endpoint')

        # Return status code and response message.
        return jsonify({'detail':'SIGNUP_EMAIL_EXISTS'}), 302
    
    # Adding row for new user details.
    new_user = User(email=email, name=name,username=username, role=role, password=generate_password_hash(password, method='sha256'), department=department,department_role=departmentrole, user_pages=user_pages, user_actions=user_actions)

    # Adding `new_user` to the database.
    db.session.add(new_user)

    # Commit the changes in the database.
    db.session.commit()

    # Logging for successful signup.
    log.logger.debug(f'New user signed up {email}, {username}')

    # Return status code and response message.
    return jsonify({'detail': 'SIGNUP_SUCCESS'}), 200

@auth.route('/delete_user', methods=['GET'])
@login_required
def delete_user():
    """
    Delete user/Deletes user from DB (permission only to 'Admin').

    :param: email
    :ptype: string

    :return: jsonfiy response with with status code
    :rtype: JSON
    """
    # Check if current user role is not `admin`.
    if current_user.role != 'admin':

        # Logging for unauthorized deletion of user.
        log.logger.warn(f'{current_user.name} attempted delete endpoint')

        # Return status code and response message.
        return jsonify({'detail': 'DELETE ACTION REQUIRES ADMIN ACCESS'}), 403

    email = request.args.get('email')

    # Fetching user using `email`.
    user = User.query.filter_by(email=email).first()
    
    # If user is not valid or not found.
    if not user:

        # Logging for successful editing of user.
        log.logger.warn(f'{current_user.name} attempted delete endpoint')

        # Return status code and response message.
        return jsonify({'detail': 'USER NOT FOUND'}), 203
    
    # Prevent deletion of user with admin role.
    if user.role == 'admin':
        return jsonify({'detail': 'USER WITH ADMIN ACCESS COULD NOT BE DELETED'}), 403
    
    # Logging for successful deletion of user.
    log.logger.info(f'{user.email} deleted successfully')

    # Delete user entry from the database.
    db.session.delete(user)

    # Commit the changes in the database.
    db.session.commit()
    
    # Return status code and response message.
    return jsonify({'detail':'USER DELETED SUCCESSFULLY'}), 200


@auth.route('/edit_user', methods=['POST'])
@login_required
def edit_user():
    """
    Edits user from DB (permission only to 'Admin').

    :return: jsonfiy response with with status code
    :rtype: JSON
    """
    # Check if current user role is not `admin`.
    if current_user.role != 'admin':

        # Logging for unauthorized editing of user.
        log.logger.warn(f'{current_user.name} attempted edit endpoint')

        # Return status code and response message.
        return jsonify({'detail': 'INVALID_PERMISSIONS'}), 403
    
    # Get argument data from edit user form.
    id = request.json['id']
    # email = request.json['email']
    # password = request.json['password']
    # name = request.json['name']
    # username = request.json['username']
    # role = request.json['role']
    # department = request.json['department']
    # department_role = request.json['department_role']
    user_pages = request.json['user_pages']
    user_actions = request.json['user_actions']

    # Fetching user on basis of ID.
    user = User.query.filter_by(id=id).first()

    # If user entry is not present in database.
    if not user:

        # Logging if user is not found.
        log.logger.warn(f'{current_user.name} attempted edit endpoint')

        # Return status code and response message.
        return jsonify({'detail': 'USER_NOT_FOUND'}), 203

    # Logging for successful editing of user.
    log.logger.warn(f'Successful edit by {current_user.email}')

    # Setting new values.
    # user.email = email
    # user.password = generate_password_hash(password, method='sha256')
    # user.name = name
    # user.username = username
    # user.role = role
    # user.department = department
    # user.department_role = department_role

    user.user_pages = user_pages
    user.user_actions = user_actions

    # Commit the changes in database.
    db.session.commit()

    # Return status code and response message.
    return jsonify({'detail':'EDIT_USER_SUCCESS'}), 200


@auth.route('/signout', methods=['GET'])
@login_required
def logout():
    """
    Logout from session by removing token from both client-server side.
    :return: jsonify response with status code
    :rtype: JSON
    """
    # Logging for user signout.
    log.logger.info(f'{current_user.name} logged out')

    # Remove user from the session.
    logout_user()

    # Return status code and response message.
    return jsonify({'detail':'LOGOUT_SUCCESS'}), 201
