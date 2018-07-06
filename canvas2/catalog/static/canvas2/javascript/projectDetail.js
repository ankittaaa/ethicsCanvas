var admins;
var adminNames = [];
var users;
var activeUsers = [];
var loggedInUser
var isAdmin;
var allCanvasses
var collabComponent;
var collabSocket;


$j(document).ready(function(data){


    $j.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });

    currentURL = window.location.pathname;
    var splitURL = currentURL.split("/");
    projectPK = splitURL[splitURL.length - 2];
    var data = {
        "operation": " "
    };

    // INITIAL AJAX REQUEST TO GET CANVAS INFORMATION AND RENDER IT TO PAGE
    performAjaxGET(currentURL, data, initSuccessCallback, initFailureCallback);
});

/*************************************************************************************************************
                                        COLLABORATOR CALLBACKS
*************************************************************************************************************/

function addUserSuccessCallback(data){
    var tempUser = (JSON.parse(data.user));
    // console.log(users);
    users.push(tempUser[0]);
    // console.log(users);
    // // console.log("pushed " + tempUser)
}

function addUserFailureCallback(data){
    // console.log(data.responseText);
}

function deleteUserSuccessCallback(data){
    var ui = JSON.parse(data.ui);
    var victimIsAdmin = JSON.parse(data.victimIsAdmin);

    if (users[ui].fields.username === loggedInUser[0].fields.username){
        alert("You've been removed from the project");
        // go back to project view after 2s 
        setInterval(
            function(){ 
                window.location.href="/catalog/project-list/"
            }, 
            100);
    }
    // console.log(users);
    users.splice(ui, 1);
    // console.log(users);

    if (victimIsAdmin === true){
        isAdmin = false;
        adminNames.splice(ui, 1);
        admins.splice(ui, 1);
        // console.log(admins);
    }
}

function deleteUserFailureCallback(data){
    // console.log(data);
}

function promoteUserSuccessCallback(data){
    var tempAdmin = JSON.parse(data.admin);
    admins.push(tempAdmin[0]);
    adminNames.push(tempAdmin[0].fields.username);

    if (loggedInUser[0].fields.username === tempAdmin[0].fields.username)
    {
        isAdmin = true;
    }
}

function promoteUserFailureCallback(data){
    // console.log(data.responseText);
}

function demoteAdminSuccessCallback(data){
    var ai = JSON.parse(data.ai);
    var victimName = adminNames[ai];
    admins.splice(ai, 1);
    adminNames.splice(ai, 1);

    if (loggedInUser[0].fields.username === victimName)
    {
        isAdmin = false;
    }
}

function demoteAdminFailureCallback(data){
    console.log(data.responseText);
}

function newActiveUserCallback(data){

    user = data.user;
    activeUsers.push(user[0].fields.username);


    collabSocket.send(JSON.stringify({
        'function': 'sendWholeList',
        'users': activeUsers,
    }));
}

function wholeListCallback(data){

    if (data.users.length <= activeUsers.length)
        return;
    else 
    {
        for (u in data.users){
            if (activeUsers.includes(data.users[u]))
                continue;
            else
                activeUsers.push(data.users[u]);
        }
    }
}

function removeActiveUserCallback(data){

    user = data.user;
    i = activeUsers.indexOf(user[0].fields.username);

    if (i > -1)
        activeUsers.splice(i, 1);
}

function populateUsersAdmins(data){
/*
    Function for updating the user/admin list for the 
    collaborator component upon modification of either list
*/
    admins = JSON.parse(data.admins);

    collabComponent.adminsList = admins;
    collabComponent.$children[0].adminsList = admins;    

    users = JSON.parse(data.users);

    collabComponent.usersList = users;
    collabComponent.$children[0].usersList = users;

    adminNames = [];

    for (a in admins)
        adminNames.push(admins[a].fields.username);

    collabComponent.adminNameList = adminNames;
    collabComponent.$children[0].adminNameList = adminNames; 

}

/*************************************************************************************************************
                                            INITIAL CALLBACK
*************************************************************************************************************/


function initSuccessCallback(data){

    admins = JSON.parse(data.admins);
    users = JSON.parse(data.users);
    loggedInUser = JSON.parse(data.loggedInUser);
    
    initCollabSocket();

    for (a in admins)
        adminNames.push(admins[a].fields.username);

    if (adminNames.indexOf(loggedInUser[0].fields.username) !== -1)
        isAdmin = true;
    else
        isAdmin = false;


    collabComponent = new Vue({
        el: '#collab-div',
        data: {
            showCollab: false,
            usersList: users,
            adminsList: admins,
            adminNameList: adminNames,
            loggedInUser: loggedInUser,
            isAdmin: isAdmin,
            active: activeUsers,
        },
    }) 
}

function initFailureCallback(data){
    console.log(data);
}

/*************************************************************************************************************
                                            COLLAB-LIST COMPONENT
*************************************************************************************************************/
 
Vue.component('collabs', {
    props: [],
    delimiters: ['<%', '%>'],
    
    template:'#collabs',

    data: function(){
        return {
            showCollab: false,
            usersList: users,
            adminsList: admins,
            adminNameList: adminNames,
            loggedInUser: loggedInUser,
            isAdmin: isAdmin,
            active: activeUsers,
        }
    },

    methods: {
        togglePublic: function(){
            // console.log("beep")
            collabSocket.send(JSON.stringify({
                'function': 'togglePublic',
                'project_pk': projectPK
            }))
        }
    },
})

/*************************************************************************************************************
                                            COLLAB-POPUP COMPONENT
*************************************************************************************************************/
 
Vue.component('collab-popup', {
    props: ['users', 'admins', 'logged-in-user', 'is-admin', 'admin-names', 'active'],
    delimiters: ['<%', '%>'],

    data: function(){
        return {
            currentUser: this.loggedInUser,
            name: '',
            a: '',
            c: '',
            activeList: this.active,
        }
    },

    computed: {
        userList: function(){
            return this.users
        },
        adminList: function(){
            return this.admins
        },
        adminNameList: function(){
            return this.adminNames
        },
        admin: function(){
            return this.isAdmin
        }
    },

    template: ` 
            <modal> 
                <div slot="header"> 
                    <h3>Collaborators</h3> 
                </div> 
                 
                <div slot="body"> 
                    <h3>Admins</h3> 
                        <ul> 
                        <li v-for="(a, ai) in adminList" style="list-style-type:none;"> 
                            <span> 
                                <% a.fields.username 
                                + ( loggedInUser[0].fields.username === a.fields.username ? " (you)" : activeList.includes(a.fields.username) ? " (active)" : "" ) %> 
                            </span> 

                            <div  

                                id="admin-buttons" 
                                v-if="loggedInUser[0].fields.username !== a.fields.username && adminNameList.includes(loggedInUser[0].fields.username)" 
                            > 
                                <button class="delete-admin" @click="deleteUser($event, a, ai)">Delete</button> 
                                <button class="demote-admin" @click="demoteAdmin($event, a, ai)">Demote</button> 
                            </div> 
                        </li> 
                    </ul> 
                     
                    <h3>Users</h3> 
                    <ul> 
                        <li v-for="(u, ui) in this.users" style="list-style-type:none;"> 
                            <span> 
                                <% u.fields.username   
                                + ( loggedInUser[0].fields.username === u.fields.username ? " (you)" : activeList.includes(u.fields.username) ? " (active)" : "" ) %> 

                            </span> 
                            <div  
                                id="user-buttons" 
                                v-if="loggedInUser[0].fields.username !== u.fields.username && adminNameList.includes(loggedInUser[0].fields.username)" 
                            > 
                                <button class="delete-user" @click="deleteUser($event, u, ui)">Delete</button> 
                                <button  
                                    v-if="adminNameList.indexOf(u.fields.username) === -1" 
                                    class="promote-user" @click="promoteUser($event, u)" 
                                >Promote</button> 
                            </div> 
                        </li> 
                    </ul> 
                    <div v-if="adminNameList.includes(loggedInUser[0].fields.username)"> 
                        <h3>Add User</h3> 
                        <input v-model="name" placeholder="Enter a username"> 
                        <button @click="addUser($event, name, this.isAdmin)">Add User</button> 
                    </div> 
                </div> 
                 
                <div slot="footer"> 
                    <button class="modal-default-button" @click="$emit( 'close' )"> 
                    Close 
                    </button> 
                </div> 
            </modal> 
        `,

    methods: {
        addUser: function(event, name, isAdmin){
            // // console.log(isAdmin);
            collabSocket.send(JSON.stringify({
                'function': 'addUser',
                'name': name
            }));
            this.name = ""
        },

        deleteUser: function(event, u, ui){
            collabSocket.send(JSON.stringify({
                'function': 'deleteUser',
                'user_pk': u.pk,
                'ui': ui
            }));
        },

        promoteUser: function(event, u){
            collabSocket.send(JSON.stringify({
                'function': 'promoteUser',
                'user_pk': u.pk,
            }));            
        },

        demoteAdmin: function(event, a, ai){
            collabSocket.send(JSON.stringify({
                'function': 'demoteUser',
                'user_pk': a.pk,
                'ai': ai
            }));
        },

    },
    watch: {

    },
    created: function(){
    }
})



Vue.component('modal', {
  template: '#modal-template'
})


function initCollabSocket(){
    collabSocket = new WebSocket(
        'ws://' + window.location.host + 
        '/ws/project/' + projectPK + '/collab/'
    );

    /***********************************
                COLLAB SOCKET
    ************************************/
    collabSocket.onmessage = function(e){
        var data = JSON.parse(e.data);
        var f = data["function"];

        switch(f) {
            case "promoteUser": {
                promoteUserSuccessCallback(data.data);
                break;
            }
            case "demoteUser": {
                demoteAdminSuccessCallback(data.data);
                break;
            }
            case "addUser": {
                addUserSuccessCallback(data.data);
                break;
            }
            case "deleteUser": {
                deleteUserSuccessCallback(data.data);
                break;
            }
            case "newActiveUser": {
                newActiveUserCallback(data.data);
                break;
            }

            case "removeActiveUser": {
                removeActiveUserCallback(data.data);
                break;
            }

            case "sendWholeList": {
                wholeListCallback(data.data);
                break;
            }
        }
    };

    collabSocket.onopen = function(e){
        collabSocket.send(JSON.stringify({
            "function": "newActiveUser",
            "user": loggedInUser,
        }));
    };

}

window.onbeforeunload = function(e){
    collabSocket.send(JSON.stringify({
            "function": "removeActiveUser",
            "user": loggedInUser,
    }));
    collabSocket.close();
};