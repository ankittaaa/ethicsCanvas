var admins;
var adminNames = [];
var users;
var activeUsers = [];
var loggedInUser
var isAdmin;
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
    users.push(tempUser);
}

function addUserFailureCallback(data){
    console.log(data);
}

function deleteUserSuccessCallback(data){
    var userListIndex = JSON.parse(data.userListIndex);
    var victimIsAdmin = JSON.parse(data.victimIsAdmin);

    if (users[userListIndex].fields.username === loggedInUser.fields.username){
        alert("You've been removed from the project");
        // go back to project view after 2s 
        setInterval(
            function(){ 
                window.location.href="/catalog/project-list/"
            }, 
            100);
    }

    users.splice(userListIndex, 1);


    if (victimIsAdmin === true){
        isAdmin = false;
        adminNames.splice(userListIndex, 1);
        admins.splice(userListIndex, 1);

    }
}

function deleteUserFailureCallback(data){
    console.log(data);
}

function promoteUserSuccessCallback(data){
    var tempAdmin = JSON.parse(data.admin);
    admins.push(tempAdmin);
    adminNames.push(tempAdmin.fields.username);

    if (loggedInUser.fields.username === tempAdmin.fields.username)
    {
        isAdmin = true;
    }
}

function promoteUserFailureCallback(data){
    console.log(data);
}

function demoteAdminSuccessCallback(data){
    var adminListIndex = JSON.parse(data.adminListIndex);
    var victimName = adminNames[adminListIndex];
    admins.splice(adminListIndex, 1);
    adminNames.splice(adminListIndex, 1);

    if (loggedInUser.fields.username === victimName)
    {
        isAdmin = false;
    }
}

function demoteAdminFailureCallback(data){
    console.log(data);
}

function newActiveUserCallback(data){

    user = data.user;
    activeUsers.push(user.fields.username);


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
    i = activeUsers.indexOf(user.fields.username);

    if (i > -1)
        activeUsers.splice(i, 1);
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

    if (adminNames.indexOf(loggedInUser.fields.username) !== -1)
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
    // console.log(data);
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
            admin: '',
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
        userIsadmin: function(){
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
                        <li v-for="(admin, adminListIndex) in adminList" style="list-style-type:none;"> 
                            <span> 
                                <% admin.fields.username 
                                + ( loggedInUser.fields.username === admin.fields.username ? " (you)" : activeList.includes(admin.fields.username) ? " (active)" : "" ) %> 
                            </span> 

                            <div  

                                id="admin-buttons" 
                                v-if="loggedInUser.fields.username !== admin.fields.username && adminNameList.includes(loggedInUser.fields.username)" 
                            > 
                                <button class="delete-admin" @click="deleteUser($event, admin, adminListIndex)">Delete</button> 
                                <button class="demote-admin" @click="demoteAdmin($event, admin, adminListIndex)">Demote</button> 
                            </div> 
                        </li> 
                    </ul> 
                     
                    <h3>Users</h3> 
                    <ul> 
                        <li v-for="(user, userListIndex) in this.users" style="list-style-type:none;"> 
                            <span> 
                                <% user.fields.username   
                                + ( loggedInUser.fields.username === user.fields.username ? " (you)" : activeList.includes(user.fields.username) ? " (active)" : "" ) %> 

                            </span> 
                            <div  
                                id="user-buttons" 
                                v-if="loggedInUser.fields.username !== user.fields.username && adminNameList.includes(loggedInUser.fields.username)" 
                            > 
                                <button class="delete-user" @click="deleteUser($event, user, userListIndex)">Delete</button> 
                                <button  
                                    v-if="adminNameList.indexOf(user.fields.username) === -1" 
                                    class="promote-user" @click="promoteUser($event, user)" 
                                >Promote</button> 
                            </div> 
                        </li> 
                    </ul> 
                    <div v-if="adminNameList.includes(loggedInUser.fields.username)"> 
                        <h3>Add User</h3> 
                        <input v-model="name" placeholder="Enter admin username"> 
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
            collabSocket.send(JSON.stringify({
                'function': 'addUser',
                'name': name
            }));
            this.name = ""
        },

        deleteUser: function(event, user, userListIndex){
            collabSocket.send(JSON.stringify({
                'function': 'deleteUser',
                'user_pk': user.pk,
                'user_list_index': userListIndex
            }));
        },

        promoteUser: function(event, user){
            collabSocket.send(JSON.stringify({
                'function': 'promoteUser',
                'user_pk': user.pk,
            }));            
        },

        demoteAdmin: function(event, admin, adminListIndex){
            collabSocket.send(JSON.stringify({
                'function': 'demoteUser',
                'user_pk': admin.pk,
                'admin_list_index': adminListIndex
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
                if (data.data.error)
                    promoteUserFailureCallback(data.data);
                else
                    promoteUserSuccessCallback(data.data);
                break;
            }
            case "demoteUser": {
                if (data.data.error)
                    demoteUserFailureCallback(data.data);
                else
                    demoteAdminSuccessCallback(data.data);
                break;
            }
            case "addUser": {
                if (data.data.error)
                    addUserFailureCallback(data.data);
                else
                    addUserSuccessCallback(data.data);
                break;
            }
            case "deleteUser": {
                if (data.data.error)
                    deleteUserFailureCallback(data.data);
                else
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