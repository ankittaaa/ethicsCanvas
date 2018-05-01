var canvasPK;
// var admins;
// var users;
// var owner;
// var me;
var amAdmin = false;
var adminPKs = [];

$j(document).ready(function(data){

    $j.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });

    var url = window.location.pathname;
    performAjaxGET(url, initSuccessCallback, initFailureCallback);

});



/*************************************************************************************************************
**************************************************************************************************************
                                            EVENT HANDLERS
**************************************************************************************************************   
**************************************************************************************************************/

$j("#add-user").on("submit", function(e){
    e.preventDefault();

    var name = $j(this).find("input[value]")[0].value;
    var data = {
        'name': name
    }
    var url = window.location.pathname;

    performAjaxPOST(url, data, addUserSuccessCallback, addUserFailureCallback);
});

$j(document).on("click", ".delete-user", function(e){
    var url = "/catalog/delete_user/";
    var userPK = $j(this).parent()[0].id.split("-")[1];
    var adminListID =  "#admins #user-" + userPK;
    var userListID =  "#users #user-" + userPK;

    var data = {
        'user_pk': userPK,
        'canvas_pk': canvasPK
    };
    
    performAjaxPOST(url, data, deleteUserSuccessCallback, deleteUserFailureCallback);
    $j(adminListID).remove();
    $j(userListID).remove();
})


$j(document).on("click", ".promote-user", function(e){
    var url = "/catalog/add_admin/";
    var userPK = $j(this).parent()[0].id.split("-")[1];
    // var promoteButton =  "#users #user-" + userPK 
    var data = {
        'user_pk': userPK,
        'canvas_pk': canvasPK
    };
    
    performAjaxPOST(url, data, promoteUserSuccessCallback, promoteUserFailureCallback);
    $j(this).remove(); 
});


$j(document).on("click", ".demote-user", function(e){
    var url = "/catalog/delete_admin/";
    var userPK = $j(this).parent()[0].id.split("-")[1];
    var listID =  "#users #user-" + userPK;
    var data = {
        'user_pk': userPK,
        'canvas_pk': canvasPK
    };
    
    performAjaxPOST(url, data, demoteUserSuccessCallback, demoteUserFailureCallback);

    $j(this).parent().remove();
    $j(listID).append(
        "<button class = 'promote-user'>Promote</button>"
    );
});



$j("#back").on("click", function(e){
    e.preventDefault();

    window.location.href = "/catalog/canvas/" + canvasPK +"/";
});




/*************************************************************************************************************
**************************************************************************************************************
                                            CALLBACK FUNCTIONS
**************************************************************************************************************   
**************************************************************************************************************/

function deleteUserSuccessCallback(data){
    console.log(data);
}
function deleteUserFailureCallback(data){
    console.log(data);
}

function promoteUserSuccessCallback(data){
    var admin = JSON.parse(data.user);
    $j("#admins").append(
        "<li class = 'user' id = 'user-" + admin[0].pk + "'> \
            <p>" + admin[0].fields.username + "</p>   \
            <button class = 'delete-user'>Delete</button> \
            <button class = 'demote-user'>Demote</button> \
        </li>"
    );
    adminPKs.push(admin[0].pk);
}
function promoteUserFailureCallback(data){
    console.log(data.responseText);
}

function demoteUserSuccessCallback(data){
    // console.log(data);
}
function demoteUserFailureCallback(data){
    console.log(data.responseText);
}


function addUserSuccessCallback(data){
    var user = JSON.parse(data.user);
    $j("#users").append(
        "<li class = 'user' id = 'user-" + user[0].pk + "'> \
            <p>" + user[0].fields.username + "</p>          \
             <button class = 'delete-user'>Delete</button>  \
             <button class = 'promote-user'>Promote</button> \
        </li>"
    );
}
function addUserFailureCallback(data){
    console.log(data.responseText);
}



function initSuccessCallback(data){
/*
    This function is to pick apart the data received from the initial AJAX POST request, as there are several django models being sent back.
*/
    var users = JSON.parse(data.users);
    var admins = JSON.parse(data.admins);
    var me = JSON.parse(data.me);
    canvasPK = JSON.parse(data.canvasPK);

    for (var i = 0; i < admins.length; i++){

        if (me[0].pk == admins[i].pk){
            amAdmin = true;
            break;
        }
    }

    populateCollabList(users, admins, me);
}

function initFailureCallback(data){
    console.log(data.responseText);
}


/*************************************************************************************************************
**************************************************************************************************************
                                            MISCELLANEOUS
**************************************************************************************************************   
**************************************************************************************************************/

// function addUserAdmin(){
// }



function populateCollabList(users, admins, me){



    // admins array is not necessarily the same length as users array
    if (admins.length > 0) {
        for (var i = 0; i < admins.length; i++){
            $j("#admins").append(
                "<li class = 'user' id = 'user-" + admins[i].pk + "'> \
                    <p>" + admins[i].fields.username + (( admins[i].pk == me[0].pk ) ? " (you)" : "" ) + "</p>   \
                    <button class = 'delete-user'>Delete</button> \
                    <button class = 'demote-user'>Demote</button> \
                </li>"
            );
            adminPKs.push(admins[i].pk);
        }
    }

    if (users.length > 0) {
        var isAdmin = false;
        
        for (var i = 0; i < users.length; i++){
            if (adminPKs.includes(users[i].pk))
                isAdmin = true;
            else
                isAdmin = false;

            console.log(isAdmin);

            $j("#users").append(
                "<li class = 'user' id = 'user-" + users[i].pk + "'> \
                    <p>" + users[i].fields.username + (( users[i].pk == me[0].pk ) ? " (you)"  : "" ) + "</p>               \
                    <button class = 'delete-user'>Delete</button>  \
                    " + ((isAdmin == false) ? "<button class = 'promote-user'>Promote</button>" : "") +"\
                </li>"
            );
        }
    }
}





