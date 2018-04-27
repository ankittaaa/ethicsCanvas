var canvasPK;
// var admins;
// var users;
// var owner;
// var me;
var amAdmin = false;

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
    var splitURL = url.split("/");
    canvasPK = splitURL[splitURL.length - 2];

    data = {
        "canvas_pk": canvasPK
    };
    performAjaxPOST(url, data, initSuccessCallback, initFailureCallback);

});



/*************************************************************************************************************
**************************************************************************************************************
                                            EVENT HANDLERS
**************************************************************************************************************   
**************************************************************************************************************/








/*************************************************************************************************************
**************************************************************************************************************
                                            CALLBACK FUNCTIONS
**************************************************************************************************************   
**************************************************************************************************************/








function initSuccessCallback(data){
/*
    This function is to pick apart the data received from the initial AJAX POST request, as there are several django models being sent back.
*/
    var users = JSON.parse(data.users);
    var admins = JSON.parse(data.admins);
    var me = JSON.parse(data.me);

    // console.log(users);
    // console.log(admins);
    // console.log(me);

    for (var i = 0; i < admins.length; i++){

        if (me[0].pk == admins[i].pk){
            amAdmin = true;
            break;
        }
    }

    console.log(amAdmin);

    populateCollabList(users, admins, me);
}

function initFailureCallback(data){
    console.log(data);
}


/*************************************************************************************************************
**************************************************************************************************************
                                            MISCELLANEOUS
**************************************************************************************************************   
**************************************************************************************************************/

function addUserAdmin(){

    // "                                                               \
    // <form id = 'add-user' action="" method='post'>                  \
    //     <input value = ' placeholder = 'Enter a username'/>        \
    //     <input type = 'submit' value = 'Submit' />                  \
    // </form>"
}



function populateCollabList(users, admins, me){
    if (users.length > 0) {
        for (var i = 0; i < users.length; i++){
            $j("#users").append(
                "<li class = 'user' id = 'user-" + users[i].pk + "'> \
                    <p>" + users[i].fields.username + (( users[i].pk == me[0].pk ) ? " (you)"  : "" ) + "</p>               \
                    " + (amAdmin ? "<button class = 'delete-user>Delete</button>'" : "") + " \
                </li>"
            );
        }
    }

    // admins array is not necessarily the same length as users array
    if (admins.length > 0 && amAdmin) {
        for (var i = 0; i < admins.length; i++){
            $j("#admins").append(
                "<li class = 'user' id = 'user-" + admins[i].pk + "'> \
                    <p>" + admins[i].fields.username + (( admins[i].pk == me[0].pk ) ? " (you)" : "" ) + "</p>   \
                    <button class = 'delete-user>Delete</button>' \
                </li>"
            );
        }
    }
}





