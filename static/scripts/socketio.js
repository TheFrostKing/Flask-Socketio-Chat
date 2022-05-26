document.addEventListener('DOMContentLoaded', () => {
    
    // How to connect to SocketIO
    var socket = io.connect('https://' + document.domain + ':' + location.port);
    let room = username; // figure out joining
    joinRoom(room)
    rooms = []
    var counter = 0;
    

    // //respond ot message
    // socket.on('response', function(msg) {
    //     console.log(msg.room)
    //     console.log(JSON.parse(msg.rooms_of_user))
    //     counter ++;
    //     console.log(counter)
    //     // document.querySelector('#display-message-section').append(JSON.parse(msg.rooms_of_user)); 
    //     document.getElementsByClassName("badge").textContent() = counter;
    //     // store notifications and receive them after click you have to send them back and update the database
    //         // code if clicked on specific room clear counter 
    // });
    
   

    // Render chat history
    socket.on('history', function (chats){
      
        document.querySelector('#display-rooms').innerHTML = '';
        rooms_arr = JSON.parse(chats.rooms)
        for (var i = 0; i < rooms_arr.length; i++) { 

            printRooms(rooms_arr[i])
            scrollDownChatWindow()
        }

        if (chats.joined_user === username) {
        history_arr = JSON.parse(chats.chats)
        for (var i = 0; i < history_arr.length; i++) { 
            printSysMsg(history_arr[i])
            scrollDownChatWindow()
        }
       
    }
        
    });
    
    socket.on('refresh_response', function(msg) {
        clearRooms()
        console.log('PRINTING REFRESH')
        arr = JSON.parse(msg.rooms)

        for (var i = 0; i < arr.length; i++) { 
            console.log(arr[i])
            printRooms(arr[i])
           
        }
        
    });

    socket.on('load_chats', function(msg) {
        console.log(msg.rooms)
        
    });

   

    socket.on('user_list', function(msg) {
        console.log(JSON.parse(msg.user))
        user = JSON.parse(msg.user)
        console.log(user)
        const p = document.querySelector('#display-users');
       
        if (user) {
            node = `<span id= ${user}>${user}</span>
            <span href="#" class="badge badge-success">Online</span> <br>`
            p.innerHTML += node         
            
    }

    document.querySelector("#logout-btn").onclick = () => {
        
        console.log('LOGOUT')
        socket.emit('exit', {'username':username});    
        
    }

    // socket.on('user_left', function(msg) {
    //     console.log(JSON.parse(msg.user_left))
    //     console.log('LEFT')
    //     user = JSON.parse(msg.user_left)
        
    // });
        
        // arr = JSON.parse(msg.rooms)

        //     for (var i = 0; i < arr.length; i++) { 
        //         document.querySelector('.side').append(arr[i])
        //     }
        
    });

    // Display incoming messages
    socket.on('message', data => {
        const p = document.createElement('p');
        const span_username = document.createElement('span');
        const span_timestamp = document.createElement('span');
        const rooms = document.createElement('span');
        const br = document.createElement('br');
        
        if (data.username && data.msg !==''){
            span_username.innerHTML = data.username
            span_timestamp.innerHTML = data.time_stamp;
            rooms.innerHTML = data.rooms_of_user.value;
            
            p.innerHTML = span_timestamp.outerHTML+': '+ span_username.outerHTML + ': ' + data.msg;
            document.querySelector('#display-message-section').append(p);
        
            
            // arr = JSON.parse(data.rooms_of_user)
            // for (var i = 0; i < arr.length; i++) { 
            //     document.querySelector('#display-message-section').append(arr[i])
            // }
            
        }
        else {
            
            printSysMsg(data.msg)
            
            
        }
        scrollDownChatWindow();
    
    });

  

    //Send message
    document.querySelector('#send_message').onclick = () => {
        
        socket.send({'msg':document.querySelector('#user_message').value,
                    'username':username, 'room': room, 'recipient': document.querySelector('#private_message').value});

            
        // Clear input area
        document.querySelector('#user_message').value = '';
        document.querySelector('#private_message').value = '';
    }

  
    document.querySelector('#send_private').onclick = () => {
       
        if (document.querySelector('#private_message').value !== ''){
            socket.emit('refresh', {'username': username,
             'room': room, 'recipient': document.querySelector('#private_message').value});
        }
        
       
        document.querySelector('#private_message').value = '';
    }


     // Select a room
    
    document.querySelectorAll('#display-rooms').forEach(p => {
        p.onclick = () => {
            document.querySelectorAll('.select-room').forEach(p => {
                p.onclick = () => {
                    let newRoom = p.textContent;
                    // Check if user already in the room
                    if (newRoom === room) {
                        msg = `You are already in ${room} room.`
                        printSysMsg(msg);
                    } else {
                        joinRoom(newRoom);
                        leaveRoom(room);
                        clearChat()
                        room = newRoom;
                    }
                };
            });
        };
    });
    
    
     // Scroll chat window down
    function scrollDownChatWindow() {
        const chatWindow = document.querySelector("#display-message-section");
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
    //Leave room
    function leaveRoom(room) {
        socket.emit('leave', {'username': username, 'room': room });
    }

    // Join room
    function joinRoom(room) {
        socket.emit('join', {'username': username, 'room': room });
        
        // Autofocus on text box
        
        document.querySelector('#user_message').focus()
    }

    // Print system msg
    function printSysMsg(msg) {
        const p = document.createElement('p');
        p.innerHTML = msg;
        document.querySelector('#display-message-section').append(p);
    }

    function printRooms(room) {
        const p = document.querySelector('#display-rooms');
        
        node = `<div><p id = ${room} class = 'select-room cursor-pointer'>${room}</p></div>`
        p.innerHTML += node
        

        // document.querySelector('#display-rooms').append(node);
        
    }

    function clearChat() {
        document.querySelector('#display-message-section').innerHTML = '';
    }
    function clearRooms() {
        document.querySelector('#display-rooms').innerHTML = '';
    }
   
})