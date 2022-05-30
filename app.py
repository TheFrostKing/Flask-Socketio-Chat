from flask import Flask,render_template, redirect,url_for,session,request, json
from datetime import date, datetime, timedelta
from flask_login import REFRESH_MESSAGE,  login_user, LoginManager, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin, AdminIndexView, expose
from forms import RegisterForm, LoginForm
from flask_talisman import Talisman
from flask_socketio import SocketIO, join_room, leave_room, emit, send
from time import localtime, strftime
from datetime import datetime
# MODELS
from models import db, Events_model, User, History, Rooms

# create an instance of the flask app
app = Flask(__name__)
bcrypt = Bcrypt(app)
socketio = SocketIO(app)

ROOMS = ['lounge', 'news']
users_map = {}
private_rooms = []
users_sessions = {}
active_users = []

# ADD DISCONECTION LOGIC AND FIX DESIGN
# WORK ON CHAT UPDATE

login_manager = LoginManager()
login_manager.init_app(app)
csp = {
    'default-src': [
        '\'self\'',
        '\'unsafe-inline\'',
        'stackpath.bootstrapcdn.com',
        'https://source.unsplash.com/twukN12EN7c/1920x1080',
        'https://images.unsplash.com',
        'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js',
        "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css",
        "https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js",
        "https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css",
        "https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js",
        "https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js",
        "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css",
        "https://192.168.0.101/jquery-3.6.0.min.js",
        "https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.5.0/socket.io.js",

        
        'code.jquery.com',
        'cdn.jsdelivr.net'
    ]
}
talisman = Talisman(app, content_security_policy=csp)


# database path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'ItShouldBeAnythingButSecret' 
db.init_app(app)

login_manager.login_view = 'login'
login_manager.session_protection = "strong"
login_manager.refresh_view = 'login'
login_manager.needs_refresh_message = (u"Session timed out, please re-login")
login_manager.needs_refresh_message_category = "info"


    
@app.before_first_request
def create_table():
    db.create_all()
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5) # time for inactivity
    session.modified = True # refresh session of inactivity

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
def load_all_users():
    return User.query.all()


class AdminView(ModelView):
    def is_accessible(self):
        if current_user.is_authenticated:
            return True
    #redirects to login page if not authenticated
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))
    #hashing the password on adding
    def on_model_change(self, form, model, is_created):
        model.password = bcrypt.generate_password_hash(model.password)
       

''' ADMIN VIEW '''
from forms import MyHomeView

admin = Admin(app, index_view=MyHomeView(), template_mode='bootstrap4')
admin.add_view(AdminView(User, db.session))

def routes():
    @app.route('/register', methods = ['GET', 'POST'])
    def register():
        form = RegisterForm()

        if request.method == 'POST' and form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data) #hashing the passwd
            new_user = User(username=form.username.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit(), 200
            return redirect(url_for('login'))

        return render_template('register.html', form=form)


    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user:
                login_user(user)
                # Beggin user mapping for chat
                new_lst = []
                for room in ROOMS:
                    new_lst.append(room)
                users_map[current_user.username] = new_lst 
                users_sessions[current_user.username] = current_user.username
                return redirect(request.args.get("next") or url_for("home"))
                
        return render_template('login.html', form=form)

    @app.route('/logout', methods=['GET', 'POST'])
    @login_required
    def logout():
        if active_users != []:
            active_users.remove(current_user.username)
        logout_user()
        return redirect(url_for('login'))
        
        

    ''' FORM TO CREATE NEW DATA '''
    @app.route('/create' , methods = ['GET','POST'])
    @login_required
    def create():
        if request.method == 'GET':
            return render_template('createpage.html')
        

        if request.method == 'POST':
            level = request.form['level']
            date_time = request.form['date_time']
            datetime_object = datetime.strptime(date_time, "%Y-%m-%dT%H:%M")
            source = request.form['source']
            event_id = request.form['event_id']
            application_log = Events_model(level=level, date_time=datetime_object, source=source, event_id=event_id)
            db.session.add(application_log)
            db.session.commit()
            return redirect('/')

        return  'Failed to create'
                


    ''' SEARCH SINGLE ELEMENT'''

    @app.route('/search', methods = ['POST']) # SOLO SEARCH
    @login_required
    def RetrieveLog():
        if request.method == "POST":
            id = request.form.get('id') 
            
            application_logs = Events_model.query.filter_by(id=id)
            if application_logs:
                return render_template('index.html', application_logs=application_logs), 200

        return render_template('index.html', application_logs=[])


    @app.route('/data/<int:id>', methods = ['GET', 'POST'])
    @login_required
    def RetrieveSingleEmployee(id):
        application_log = Events_model.query.filter_by(id=id).first()
        if application_log: 
            return render_template('data.html', application_log = application_log)
        return f"ID with id ={id} Doesn't exist", 404


    ''' UPDATE EXISTING DATA'''

    @app.route('/data/<int:id>/update',methods = ['GET','POST'])
    @login_required
    def update(id):
        application_log = Events_model.query.filter_by(id=id).first()
        if request.method == 'POST':
            print(request.form)
            if application_log:
                application_log.level = request.form['level']
                date_time = request.form['date_time']              
                application_log.date_time = datetime.strptime(date_time, "%Y-%m-%dT%H:%M")
                application_log.source = request.form['source']
                application_log.event_id = request.form['event_id']

                db.session.add(application_log)
                db.session.commit()
                return redirect(f'/data/{id}')
            return f"error with id ={id} Doesn't exist", 200

        return render_template('update.html', application_log = application_log)
        

    @app.route('/data/<int:id>/delete', methods=['GET','POST'])
    @login_required   
    def delete(id):
        application_log = Events_model.query.filter_by(id=id).first()
        if request.method == 'GET':
            if application_log:
                db.session.delete(application_log)
                db.session.commit()
                return redirect('/')
            return 'Failed to delete', 401
        return redirect('/')


    @app.route('/')
    @login_required
    def home():
        page = request.args.get('page', type = int)
        application_logs = Events_model.query.paginate(page = page, per_page = 5)
        return render_template('index.html', application_logs=application_logs, name = current_user), 200
        

    @app.route('/about',methods=['GET','POST'])
    def about():
        return render_template('about.html'),200



def socketio_routes():
    
    @app.route("/chat", methods = ['GET', 'POST'])
    @login_required
    def chat():
        
        if request.method == 'GET':

            print(f'\n\n{users_map}\n\n')
            return render_template('chat.html', username = current_user.username,
            rooms = users_map[current_user.username], actives = active_users),200

        if request.method == 'POST':        
            print(f'\n\nPOST')
            print(f'\n\nPOST\n\n')
            recipient = request.form['recipient']
            
            print(f'\n\n{recipient}\n\n')
            
            print(f'\n\n{recipient}\n\n')
            check_room = f"{current_user.username}'s chat with {recipient}"
            reversed_name =  f"{recipient}'s chat with {current_user.username}"
            if recipient != '':
                if check_room not in users_map[current_user.username] and reversed_name not \
                        in users_map[current_user.username] and recipient != current_user.username:
                    
                    print(f'\n\n{users_map[current_user.username]}\n\n')
                    users = load_all_users()
                
                    for user in users:
                        if recipient == user.username:
                            # PRIVATE MESSAGING a user - it will create a room with the recipient
                            new_room  = f"{current_user.username}'s chat with {recipient}"
                            users_map[current_user.username].append(str(new_room))
                            users_map[recipient].append(str(new_room))

            
            # send(f'{current_user.username}')
            print(f'\n\n{users_map}\n\n')
            print(f'\n\n{ROOMS}\n\n')
            return render_template('chat.html', username = current_user.username, 
                                    rooms = users_map[current_user.username], actives = active_users ),200
        
    

    @socketio.on('message')
    def message(data):
        print(data['recipient'])
       
        # send(f'{current_user.username}')
        # send data to clients - broadcasts to all clients
        rooms_of_user  = [ room for room in users_map[current_user.username]]
        print(f'\n\n{rooms_of_user}\n\n')
        print(f'\n\n{data}\n\n')
        json_string =  json.dumps(rooms_of_user)
        print(f'{json_string}')

        for session in users_sessions: # receive notification
            if data['recipient'] == session:
                emit("response", {'msg' : 'Received a msg from someone', 'recipient': data['recipient'],
                 'room': data['room'], 'rooms_of_user': [f'{json_string}'] }, room = users_sessions[session])
                
        

        send({'msg': data['msg'], 'username': data['username'], 'recipient': data['recipient'],
        'time_stamp':strftime("%Y-%m-%d %H:%M:%S",localtime()), 'rooms_of_user': [f'{json_string}']}, room=data['room']) 
        now = datetime.now()
        datem = datetime.strptime(str(now.strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")  
        query = History(Name=data['username'], Message=data['msg'], Session=data['room'], Time=datem)
        db.session.add(query)
        db.session.commit()


    # @socketio.on('update_rooms')
    # def update_rooms(data):
    #     print(data['recipient'])
    #     # send(f'{current_user.username}')
    #     # send data to clients - broadcasts to all clients
    #     send({'username': data['username'], 'recipient': data['recipient']}, room=data['room'])     

    #     join_room(data['room'])
    
    
    @socketio.on('refresh')
    def refresh(data):
        print(f'\n\n REFRESH \n\n')
        print(f'\n\n REFRESH \n\n')
        print(f'\n\n REFRESH \n\n')
        print(data)
        user = current_user.username
        recipient = data['recipient']
        private_session = [user, recipient]

        check_room = f"{user}'s chat with {recipient}"
        reversed_name =  f"{recipient}'s chat with {user}"
       # Create one identical room for two users to chat privately
        exists = Rooms.query.filter_by(Rooms = check_room, Name = user).first()
        exists_reversed = Rooms.query.filter_by(Rooms = reversed_name, Name = user).first()

        if not exists and not exists_reversed and recipient != user:
            sender = Rooms(Name = user, Rooms = check_room)
            recip = Rooms(Name = recipient, Rooms = check_room)
            db.session.add(sender)
            db.session.add(recip)
            db.session.commit()
            update_rooms = Rooms.query.filter_by(Name = current_user.username).all()
            print(f'\n\n {update_rooms} \n\n')
            update_rooms = [str(room) for room in update_rooms]
            print(f'\n\n {update_rooms} after list compr\n\n')
            for user in private_session: # receive notification
                if data['recipient']:
                    emit("refresh_response", {'recipient' : data['recipient'], 
                    'rooms' : [f'{json.dumps(update_rooms)}']}, room = users_sessions[user])
        

     
                        
        
       
                

    @socketio.on('join')
    def join(data):
        session = request.sid
        name = current_user.username
        users_sessions[name] = data['room']
         
        # TO TEST FOR NAMES
        # update_rooms = Rooms.query.filter_by(Rooms = 'lounge').all()
        # print(f'\n\n{update_rooms} PRINTING BY NAMES')

        # ADD starters' rooms
        for room in ROOMS: 
            exists = Rooms.query.filter_by(Rooms = room, Name = name).first()
            if not exists:
                new_room = Rooms(Name = name, Rooms = room)
                db.session.add(new_room)
                db.session.commit()
        

        # FROM TUPLE TO LIST result = [r for r, in result]
        

        
        
        # starter_rooms = []
        # for user in users_map:
        #     if name == user :
        #         for room in users_map[user]:
        #             starter_rooms.append(room)
        # print(f'\n\n {starter_rooms} \n\n')
        # json_starter_rooms = json.dumps(starter_rooms)

        # Put starting packet of rooms available for the user
        rooms = Rooms.query.filter_by(Name = name).all()
        rooms = [str(r) for r in rooms]
        json_starter_rooms = json.dumps(rooms)
        
            
        new_user = current_user.username
        new_user_json = json.dumps(new_user)
        if new_user not in active_users and data['room'] == current_user.username:
            for user in users_sessions: # receive notification
                emit("user_list", {"user": [f'{new_user_json}']}, room = users_sessions[user])
            
        if current_user.username not in active_users:
                active_users.append(current_user.username)
    
        
        print(f'\n\n {session} \n\n')
        print(f'\n\n {users_sessions[name]} \n\n')

        current_room_name = users_sessions[current_user.username]
        print(f'\n\n {current_room_name} CURRENT ROOM NAME   \n\n')
        history_list = []
        history = History.query.filter_by(Session = current_room_name).all()
        
        
        

        join_room(data['room']) 

          #send chat history 
        for x in history: 
            history_list.append(str(x))

        print(f'\n\n {history_list} PRINTED LIST OF HISTORY')
        json_history= json.dumps(history_list)
        print(f' STIGA LI DO TUK')
        emit('history', {'chats': f'{json_history}', 'joined_user': f'{current_user.username}',
        'rooms': f'{json_starter_rooms}'},
        room = users_sessions[current_user.username])
        send({'msg': data['username'] + " has joined the " + data['room'] + " room."}, room = data['room'])
       

    @socketio.on('leave')
    def leave(data):
        leave_room(data['room'])
        send({'msg': data['username'] + " has left the " + data['room'] + " room."}, room = data['room'])
        
    
    
socketio_routes()
routes()


if __name__ == "__main__":
    
    socketio.run(app.run(ssl_context=('self_signed/cert.pem', 'self_signed/key.pem'), host ="0.0.0.0", port=443, debug = True))